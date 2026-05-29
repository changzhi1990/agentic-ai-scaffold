"""OpenAI-compatible provider with deterministic offline fallback."""

from __future__ import annotations

from typing import Any

import httpx

from app.exceptions import LLMError
from app.models import KnowledgeMatch, LLMResult, PlanStep, SkillDefinition, TaskRequest, ToolCallRecord
from llm.base import BaseLLMProvider


class OpenAICompatibleProvider(BaseLLMProvider):
    """Calls an OpenAI-style `/chat/completions` API when configured, otherwise falls back locally."""

    def __init__(
        self,
        model: str,
        api_base_url: str | None,
        api_key: str | None,
        timeout_seconds: int = 30,
    ) -> None:
        self.model = model
        self.api_base_url = api_base_url.rstrip("/") if api_base_url else None
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    def generate_answer(
        self,
        request: TaskRequest,
        selected_skills: list[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        plan: list[PlanStep],
        tool_calls: list[ToolCallRecord],
    ) -> LLMResult:
        if self.api_base_url and self.api_key:
            return self._call_remote_api(request, selected_skills, knowledge_matches, plan, tool_calls)
        return self._fallback_answer(request, selected_skills, knowledge_matches, plan, tool_calls)

    def _call_remote_api(
        self,
        request: TaskRequest,
        selected_skills: list[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        plan: list[PlanStep],
        tool_calls: list[ToolCallRecord],
    ) -> LLMResult:
        prompt = self._build_prompt(request, selected_skills, knowledge_matches, plan, tool_calls)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an engineering task agent."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.api_base_url}/chat/completions"
        try:
            with httpx.Client(timeout=self.timeout_seconds) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise LLMError(f"OpenAI-compatible request failed: {exc}") from exc

        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return LLMResult(final_answer=content, raw_response=data)

    def _fallback_answer(
        self,
        request: TaskRequest,
        selected_skills: list[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        plan: list[PlanStep],
        tool_calls: list[ToolCallRecord],
    ) -> LLMResult:
        answer_lines = [
            f"Task: {request.task}",
            f"Selected skills: {', '.join(skill.name for skill in selected_skills) or 'none'}",
        ]
        if knowledge_matches:
            answer_lines.append("Knowledge highlights:")
            for match in knowledge_matches:
                answer_lines.append(f"- {match.title}: {match.snippet}")
        if tool_calls:
            answer_lines.append("Tool results:")
            for call in tool_calls:
                if call.success:
                    answer_lines.append(f"- {call.tool_name} succeeded with output keys: {', '.join(call.output.keys())}")
                else:
                    answer_lines.append(f"- {call.tool_name} failed: {call.error}")
        answer_lines.append("Plan summary:")
        for step in plan:
            answer_lines.append(f"- {step.step_id}: {step.description}")
        answer_lines.append("Final assessment: The scaffold processed the request and returned structured output.")
        return LLMResult(
            final_answer="\n".join(answer_lines),
            raw_response={"mode": "fallback"},
        )

    def _build_prompt(
        self,
        request: TaskRequest,
        selected_skills: list[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        plan: list[PlanStep],
        tool_calls: list[ToolCallRecord],
    ) -> str:
        payload: dict[str, Any] = {
            "task": request.model_dump(),
            "selected_skills": [skill.model_dump() for skill in selected_skills],
            "knowledge_used": [match.model_dump() for match in knowledge_matches],
            "plan": [step.model_dump() for step in plan],
            "tool_calls": [call.model_dump() for call in tool_calls],
        }
        return (
            "Create a concise but technical final answer for the agent runtime using this state:\n"
            f"{payload}"
        )
