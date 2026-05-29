"""Keyword-based retrieval implementation."""

from __future__ import annotations

import re

from app.models import KnowledgeMatch
from knowledge.base import KnowledgeDocumentStore


class KeywordKnowledgeRetriever:
    """Search local documents using token overlap scoring."""

    def __init__(self, store: KnowledgeDocumentStore) -> None:
        self.store = store

    def search(self, query: str, limit: int = 3) -> list[KnowledgeMatch]:
        query_terms = self._tokenize(query)
        if not query_terms:
            return []

        matches: list[KnowledgeMatch] = []
        for document in self.store.load_documents():
            content_terms = self._tokenize(document.content)
            overlap = query_terms & content_terms
            if not overlap:
                continue
            score = len(overlap) / max(len(query_terms), 1)
            snippet = self._snippet_for_overlap(document.content, overlap)
            matches.append(
                KnowledgeMatch(
                    document_id=document.document_id,
                    title=document.title,
                    score=round(score, 3),
                    snippet=snippet,
                    source_path=document.source_path,
                )
            )
        matches.sort(key=lambda item: item.score, reverse=True)
        return matches[:limit]

    def _tokenize(self, text: str) -> set[str]:
        return set(re.findall(r"[a-zA-Z0-9_]+", text.lower()))

    def _snippet_for_overlap(self, content: str, overlap: set[str]) -> str:
        for line in content.splitlines():
            lowered = line.lower()
            if any(term in lowered for term in overlap):
                return line.strip()[:240]
        return content.strip().splitlines()[0][:240] if content.strip() else ""
