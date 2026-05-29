from pathlib import Path

from tools.file_tool import build_file_tools
from tools.kb_tool import build_kb_tools
from tools.registry import ToolRegistry
from knowledge.base import KnowledgeDocumentStore
from knowledge.retriever import KeywordKnowledgeRetriever


def test_registry_executes_read_and_write_file_tools(tmp_path: Path) -> None:
    registry = ToolRegistry()
    for tool in build_file_tools():
        registry.register(tool)

    target = tmp_path / "note.txt"
    write_result = registry.execute(
        "write_file",
        {"path": str(target), "content": "hello from tool"},
    )
    read_result = registry.execute("read_file", {"path": str(target)})

    assert write_result.success is True
    assert write_result.output["success"] is True
    assert read_result.success is True
    assert read_result.output["content"] == "hello from tool"


def test_registry_handles_invalid_tool_input_without_crashing() -> None:
    registry = ToolRegistry()
    for tool in build_file_tools():
        registry.register(tool)

    result = registry.execute("read_file", {})

    assert result.success is False
    assert result.error is not None
    assert "validation" in result.error.lower()


def test_kb_tool_returns_matches() -> None:
    docs_path = Path(__file__).resolve().parents[1] / "knowledge" / "docs"
    store = KnowledgeDocumentStore(docs_path=docs_path)
    retriever = KeywordKnowledgeRetriever(store=store)
    registry = ToolRegistry()
    for tool in build_kb_tools(retriever):
        registry.register(tool)

    result = registry.execute("search_knowledge_base", {"query": "linux command execution"})

    assert result.success is True
    assert result.output["matches"]
