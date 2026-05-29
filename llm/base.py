"""Provider abstraction for reasoning backends."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.models import KnowledgeMatch, LLMResult, PlanStep, SkillDefinition, TaskRequest, ToolCallRecord


class BaseLLMProvider(ABC):
    """Abstract interface for pluggable reasoning backends."""

    @abstractmethod
    def generate_answer(
        self,
        request: TaskRequest,
        selected_skills: list[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        plan: list[PlanStep],
        tool_calls: list[ToolCallRecord],
    ) -> LLMResult:
        """Produce a final answer from the current execution state."""
