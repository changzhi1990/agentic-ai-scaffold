"""Application bootstrap and main task agent loop."""

from __future__ import annotations

import logging
from pathlib import Path
import os
from typing import Any

import yaml

from app.exceptions import LLMError
from app.logging_utils import configure_logging
from app.memory import RunMemory
from app.models import AppConfig, LLMResult, ResponseStatus, TaskRequest, TaskResponse, ToolCallRecord
from app.planner import SimplePlanner
from app.skills_loader import load_skills, select_skills
from knowledge.base import KnowledgeDocumentStore
from knowledge.retriever import KeywordKnowledgeRetriever
from llm.base import BaseLLMProvider
from llm.providers.openai_compatible import OpenAICompatibleProvider
from tools.agent_tool import build_agent_tools
from tools.file_tool import build_file_tools
from tools.http_tool import build_http_tools
from tools.kb_tool import build_kb_tools
from tools.registry import ToolRegistry
from tools.shell_tool import build_shell_tools


LOGGER = logging.getLogger(__name__)


class AgentApp:
    """Container for shared runtime dependencies."""

    def __init__(
        self,
        project_root: Path,
        config: AppConfig,
        llm_provider: BaseLLMProvider,
        tool_registry: ToolRegistry,
        knowledge_retriever: KeywordKnowledgeRetriever,
        skills: list,
        memory: RunMemory,
    ) -> None:
        self.project_root = project_root
        self.config = config
        self.llm_provider = llm_provider
        self.tool_registry = tool_registry
        self.knowledge_retriever = knowledge_retriever
        self.skills = skills
        self.memory = memory

    @classmethod
    def from_project_root(cls, project_root: Path) -> "AgentApp":
        """Construct the runtime from on-disk config and packaged modules."""
        config = _load_config(project_root)
        configure_logging(config.log_level)

        docs_path = project_root / config.knowledge_docs_path
        store = KnowledgeDocumentStore(docs_path=docs_path)
        retriever = KeywordKnowledgeRetriever(store=store)
        registry = ToolRegistry()
        for tool in build_file_tools():
            registry.register(tool)
        for tool in build_http_tools():
            registry.register(tool)
        for tool in build_kb_tools(retriever):
            registry.register(tool)
        for tool in build_agent_tools(config.remote_agents):
            registry.register(tool)
        for tool in build_shell_tools(
            allow_shell=config.allow_shell,
            default_timeout=config.shell_timeout_seconds,
            cwd=project_root,
        ):
            registry.register(tool)

        provider = OpenAICompatibleProvider(
            model=config.llm_model,
            api_base_url=config.llm_api_base_url,
            api_key=config.llm_api_key,
            timeout_seconds=config.llm_timeout_seconds,
        )
        skills = load_skills(project_root / "skills")
        memory = RunMemory()
        return cls(
            project_root=project_root,
            config=config,
            llm_provider=provider,
            tool_registry=registry,
            knowledge_retriever=retriever,
            skills=skills,
            memory=memory,
        )


class TaskAgent:
    """Coordinates retrieval, planning, tool execution, and answer generation."""

    def __init__(self, app: AgentApp) -> None:
        self.app = app
        self.planner = SimplePlanner()

    def run(self, request: TaskRequest) -> TaskResponse:
        """Execute the end-to-end agent flow."""
        normalized_task = request.task.strip()
        request = TaskRequest(task=normalized_task, context=request.context)
        selected_skills = select_skills(
            task=request.task,
            skills=self.app.skills,
            default_skill=self.app.config.default_skill,
        )

        knowledge_matches = []
        if self._should_retrieve_knowledge(request.task):
            try:
                knowledge_matches = self.app.knowledge_retriever.search(
                    request.task,
                    limit=self.app.config.max_knowledge_matches,
                )
            except Exception as exc:  # pragma: no cover - defensive logging path
                LOGGER.exception("Knowledge retrieval failed", extra={"event": "knowledge_failed"})
                knowledge_matches = []

        forced_tool = request.context.get("force_tool")
        plan = self.planner.build_plan(
            request=request,
            skills=selected_skills,
            knowledge_matches=knowledge_matches,
            forced_tool=forced_tool,
        )

        tool_calls: list[ToolCallRecord] = []
        if forced_tool:
            tool_args = request.context.get("tool_args", {})
            tool_calls.append(self.app.tool_registry.execute(forced_tool, tool_args))

        status = _derive_status(tool_calls)
        try:
            llm_result = self.app.llm_provider.generate_answer(
                request=request,
                selected_skills=selected_skills,
                knowledge_matches=knowledge_matches,
                plan=plan,
                tool_calls=tool_calls,
            )
        except Exception as exc:
            LOGGER.exception("LLM generation failed", extra={"event": "llm_failed"})
            llm_result = LLMResult(final_answer=f"LLM generation failed: {exc}", raw_response={})
            status = ResponseStatus.FAILED if not tool_calls else ResponseStatus.PARTIAL_SUCCESS

        if tool_calls and any(not item.success for item in tool_calls):
            status = ResponseStatus.PARTIAL_SUCCESS if llm_result.final_answer else ResponseStatus.FAILED

        if not tool_calls and not llm_result.final_answer:
            status = ResponseStatus.FAILED

        response = TaskResponse(
            task=request.task,
            selected_skills=[skill.name for skill in selected_skills],
            knowledge_used=knowledge_matches,
            plan=plan,
            tool_calls=tool_calls,
            final_answer=llm_result.final_answer,
            status=status,
        )
        self.app.memory.add(response)
        return response

    def _should_retrieve_knowledge(self, task: str) -> bool:
        lowered = task.lower()
        return any(keyword in lowered for keyword in self.app.config.auto_retrieve_keywords)


def _derive_status(tool_calls: list[ToolCallRecord]) -> ResponseStatus:
    if not tool_calls:
        return ResponseStatus.SUCCESS
    if all(call.success for call in tool_calls):
        return ResponseStatus.SUCCESS
    if any(call.success for call in tool_calls):
        return ResponseStatus.PARTIAL_SUCCESS
    return ResponseStatus.FAILED


def _load_config(project_root: Path) -> AppConfig:
    config_path = Path(os.getenv("AGENT_CONFIG_PATH", project_root / "config" / "settings.yaml"))
    if not config_path.is_absolute():
        config_path = project_root / config_path
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    app = raw.get("app", {})
    llm = raw.get("llm", {})
    agent = raw.get("agent", {})
    tools = raw.get("tools", {})
    knowledge = raw.get("knowledge", {})
    remote_agents = raw.get("remote_agents", {})

    return AppConfig(
        app_name=app.get("name", "EngineeringTaskAgent"),
        app_version=app.get("version", "0.1.0"),
        log_level=os.getenv("LOG_LEVEL", app.get("log_level", "INFO")),
        llm_provider=llm.get("provider", "openai_compatible"),
        llm_model=os.getenv("OPENAI_MODEL", llm.get("model", "gpt-4o-mini")),
        llm_api_base_url=_resolve_env(llm.get("api_base_url")),
        llm_api_key=_resolve_env(llm.get("api_key")),
        llm_timeout_seconds=int(llm.get("timeout_seconds", 30)),
        knowledge_docs_path=knowledge.get("docs_path", "knowledge/docs"),
        max_knowledge_matches=int(agent.get("max_knowledge_matches", 3)),
        auto_retrieve_keywords=list(agent.get("auto_retrieve_keywords", [])),
        default_skill=agent.get("default_skill", "plan_task"),
        shell_timeout_seconds=int(tools.get("shell_timeout_seconds", 20)),
        allow_shell=bool(tools.get("allow_shell", True)),
        remote_agents=remote_agents,
    )


def _resolve_env(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
        return os.getenv(value[2:-1], None)
    return str(value)
