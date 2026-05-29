"""Simple planning utilities."""

from __future__ import annotations

from typing import Iterable

from app.models import KnowledgeMatch, PlanStep, SkillDefinition, TaskRequest


class SimplePlanner:
    """Builds an explicit, inspectable plan for task execution."""

    def build_plan(
        self,
        request: TaskRequest,
        skills: Iterable[SkillDefinition],
        knowledge_matches: list[KnowledgeMatch],
        forced_tool: str | None = None,
    ) -> list[PlanStep]:
        plan: list[PlanStep] = [
            PlanStep(
                step_id="analyze",
                description="Analyze the task and normalize intent.",
                reason="Every request starts with intent analysis.",
            )
        ]

        if knowledge_matches:
            plan.append(
                PlanStep(
                    step_id="retrieve_knowledge",
                    description="Review retrieved knowledge snippets before answering.",
                    reason="The task appears factual, project-specific, or context dependent.",
                    tool_name="search_knowledge_base",
                )
            )

        if forced_tool:
            plan.append(
                PlanStep(
                    step_id="execute_tool",
                    description=f"Execute the requested tool `{forced_tool}`.",
                    reason="The caller explicitly requested a tool invocation.",
                    tool_name=forced_tool,
                )
            )

        if any(skill.name == "delegate_to_agent" for skill in skills):
            plan.append(
                PlanStep(
                    step_id="consider_delegation",
                    description="Prepare a delegation payload if a specialized agent is better suited.",
                    reason="A delegation-oriented skill matched the request.",
                    tool_name="call_agent",
                )
            )

        plan.append(
            PlanStep(
                step_id="compose_answer",
                description="Interpret tool outputs and produce the final structured answer.",
                reason="The runtime must return a summary with status and evidence.",
            )
        )
        return plan
