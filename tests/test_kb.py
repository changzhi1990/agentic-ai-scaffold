from pathlib import Path

from knowledge.base import KnowledgeDocumentStore
from knowledge.retriever import KeywordKnowledgeRetriever


def test_search_returns_ranked_matches() -> None:
    docs_path = Path(__file__).resolve().parents[1] / "knowledge" / "docs"
    store = KnowledgeDocumentStore(docs_path=docs_path)
    retriever = KeywordKnowledgeRetriever(store=store)

    matches = retriever.search("benchmark automation logs", limit=2)

    assert matches
    assert matches[0].document_id
    assert "benchmark" in matches[0].snippet.lower()


def test_search_returns_empty_list_for_unknown_query() -> None:
    docs_path = Path(__file__).resolve().parents[1] / "knowledge" / "docs"
    store = KnowledgeDocumentStore(docs_path=docs_path)
    retriever = KeywordKnowledgeRetriever(store=store)

    matches = retriever.search("totally unrelated quantum bananas", limit=3)

    assert matches == []
