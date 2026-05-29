"""Shell execution tool."""

from __future__ import annotations

import subprocess
from pathlib import Path

from pydantic import BaseModel, Field

from tools.base import StructuredTool


class ShellCommandInput(BaseModel):
    command: str = Field(..., min_length=1)
    timeout_seconds: int | None = None


class ShellCommandOutput(BaseModel):
    stdout: str
    stderr: str
    exit_code: int


def build_shell_tools(allow_shell: bool, default_timeout: int, cwd: Path) -> list[StructuredTool]:
    if not allow_shell:
        return []

    def handler(data: ShellCommandInput) -> ShellCommandOutput:
        completed = subprocess.run(
            data.command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=data.timeout_seconds or default_timeout,
            cwd=str(cwd),
            check=False,
        )
        return ShellCommandOutput(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
        )

    return [
        StructuredTool(
            name="run_shell_command",
            description="Execute a shell command with timeout and capture stdout/stderr.",
            input_model=ShellCommandInput,
            output_model=ShellCommandOutput,
            handler=handler,
        )
    ]
