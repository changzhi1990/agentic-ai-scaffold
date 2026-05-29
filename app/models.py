"""Shared pydantic models for runtime state and API contracts."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ResponseStatus(str, Enum):
    """Possible response states for the agent runtime."""

    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class TaskRequest(BaseModel):
    """Normalized incoming request."""

    task: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class KnowledgeMatch(BaseModel):
    """Single retrieved knowledge snippet."""

    document_id: str
    title: str
    score: float
    snippet: str
    source_path: str


class SkillDefinition(BaseModel):
    """Declarative skill metadata loaded from markdown."""

    name: str
    description: str
    when_to_use: list[str] = Field(default_factory=list)
    instructions: str
    required_tools: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    source_path: str


class PlanStep(BaseModel):
    """Single execution-plan step."""

    step_id: str
    description: str
    reason: str
    tool_name: str | None = None


class ToolCallRecord(BaseModel):
    """Auditable record of one tool execution."""

    tool_name: str
    arguments: dict[str, Any]
    success: bool
    output: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class LLMResult(BaseModel):
    """Output returned by the reasoning backend."""

    final_answer: str
    raw_response: dict[str, Any] = Field(default_factory=dict)


class TaskResponse(BaseModel):
    """Structured result returned by the agent."""

    task: str
    selected_skills: list[str] = Field(default_factory=list)
    knowledge_used: list[KnowledgeMatch] = Field(default_factory=list)
    plan: list[PlanStep] = Field(default_factory=list)
    tool_calls: list[ToolCallRecord] = Field(default_factory=list)
    final_answer: str
    status: ResponseStatus


class AppConfig(BaseModel):
    """Normalized application configuration."""

    app_name: str = "EngineeringTaskAgent"
    app_version: str = "0.1.0"
    log_level: str = "INFO"
    llm_provider: str = "openai_compatible"
    llm_model: str = "gpt-4o-mini"
    llm_api_base_url: str | None = None
    llm_api_key: str | None = None
    llm_timeout_seconds: int = 30
    knowledge_docs_path: str = "knowledge/docs"
    max_knowledge_matches: int = 3
    auto_retrieve_keywords: list[str] = Field(default_factory=list)
    default_skill: str = "plan_task"
    shell_timeout_seconds: int = 20
    allow_shell: bool = True
    remote_agents: dict[str, dict[str, Any]] = Field(default_factory=dict)
