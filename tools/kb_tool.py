"""Knowledge-base search tool."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from knowledge.retriever import KeywordKnowledgeRetriever
from tools.base import StructuredTool


class KnowledgeSearchInput(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = 3


class KnowledgeSearchOutput(BaseModel):
    matches: list[dict[str, Any]]


def build_kb_tools(retriever: KeywordKnowledgeRetriever) -> list[StructuredTool]:
    def handler(data: KnowledgeSearchInput) -> KnowledgeSearchOutput:
        matches = retriever.search(data.query, limit=data.limit)
        return KnowledgeSearchOutput(matches=[match.model_dump() for match in matches])

    return [
        StructuredTool(
            name="search_knowledge_base",
            description="Search local knowledge documents and return scored snippets.",
            input_model=KnowledgeSearchInput,
            output_model=KnowledgeSearchOutput,
            handler=handler,
        )
    ]
