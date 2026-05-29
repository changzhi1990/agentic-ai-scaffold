"""File read/write tools."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import StructuredTool


class ReadFileInput(BaseModel):
    path: str = Field(..., min_length=1)


class ReadFileOutput(BaseModel):
    content: str


class WriteFileInput(BaseModel):
    path: str = Field(..., min_length=1)
    content: str


class WriteFileOutput(BaseModel):
    success: bool


def build_file_tools() -> list[StructuredTool]:
    return [
        StructuredTool(
            name="read_file",
            description="Read a UTF-8 text file from disk.",
            input_model=ReadFileInput,
            output_model=ReadFileOutput,
            handler=_read_file,
        ),
        StructuredTool(
            name="write_file",
            description="Write UTF-8 text content to disk.",
            input_model=WriteFileInput,
            output_model=WriteFileOutput,
            handler=_write_file,
        ),
    ]


def _read_file(data: ReadFileInput) -> ReadFileOutput:
    content = Path(data.path).read_text(encoding="utf-8")
    return ReadFileOutput(content=content)


def _write_file(data: WriteFileInput) -> WriteFileOutput:
    path = Path(data.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data.content, encoding="utf-8")
    return WriteFileOutput(success=True)
