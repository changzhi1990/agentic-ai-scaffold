"""Knowledge document storage primitives."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class KnowledgeDocument:
    """Simple file-backed knowledge document."""

    document_id: str
    title: str
    content: str
    source_path: str


class KnowledgeDocumentStore:
    """Loads local knowledge files from disk."""

    def __init__(self, docs_path: Path) -> None:
        self.docs_path = docs_path

    def load_documents(self) -> list[KnowledgeDocument]:
        documents: list[KnowledgeDocument] = []
        if not self.docs_path.exists():
            return documents
        for path in sorted(self.docs_path.iterdir()):
            if not path.is_file():
                continue
            if path.suffix.lower() not in {".md", ".txt", ".log"}:
                continue
            content = path.read_text(encoding="utf-8")
            documents.append(
                KnowledgeDocument(
                    document_id=path.stem,
                    title=path.stem.replace("_", " ").title(),
                    content=content,
                    source_path=str(path),
                )
            )
        return documents
