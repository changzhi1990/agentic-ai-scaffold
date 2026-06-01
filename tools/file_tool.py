from __future__ import annotations

from pathlib import Path


def read_file(path: str) -> dict[str, str]:
    file_path = Path(path)
    return {"content": file_path.read_text(encoding="utf-8")}


def file_exists(path: str) -> dict[str, bool]:
    return {"exists": Path(path).exists()}


class FileTool:
    def read(self, path: str) -> dict[str, str]:
        return read_file(path)

    def exists(self, path: str) -> dict[str, bool]:
        return file_exists(path)
