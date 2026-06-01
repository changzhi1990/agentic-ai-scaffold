from __future__ import annotations

import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Callable

from app.models import CommandExecutionResult


def run_shell_command(command: str, timeout: int | None = None) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        duration = time.perf_counter() - started
        return CommandExecutionResult(
            command=command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            timed_out=False,
            duration_seconds=round(duration, 4),
        ).model_dump()
    except subprocess.TimeoutExpired as exc:
        duration = time.perf_counter() - started
        return CommandExecutionResult(
            command=command,
            stdout=exc.stdout or "",
            stderr=(exc.stderr or "") + f"\nTimed out after {timeout} seconds",
            exit_code=124,
            timed_out=True,
            duration_seconds=round(duration, 4),
        ).model_dump()


def parse_command_output(
    raw_text: str,
    parser: Callable[[str], dict[str, Any]],
    fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        return parser(raw_text)
    except Exception as exc:  # pragma: no cover - protective path
        data = dict(fallback or {})
        warnings = list(data.get("warnings", []))
        warnings.append(f"parser failed: {exc}")
        data["warnings"] = warnings
        return data


class ShellTool:
    def exists(self, command: str) -> bool:
        if "/" in command:
            return Path(command).exists()
        return shutil.which(command) is not None

    def run(self, command: str, timeout: int | None = None) -> dict[str, Any]:
        return run_shell_command(command, timeout=timeout)

    @staticmethod
    def format_command(binary_path: str, args: list[str], env: dict[str, str] | None = None) -> str:
        env_parts = []
        for key, value in sorted((env or {}).items()):
            env_parts.append(f"{key}={shlex.quote(value)}")
        parts = [*env_parts, shlex.quote(binary_path), *[shlex.quote(arg) for arg in args]]
        return " ".join(parts)
