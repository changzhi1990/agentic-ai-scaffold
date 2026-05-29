"""Registry and execution protocol for tools."""

from __future__ import annotations

import logging

from pydantic import ValidationError

from app.models import ToolCallRecord
from tools.base import StructuredTool


LOGGER = logging.getLogger(__name__)


class ToolRegistry:
    """Stores tools and executes them with structured error capture."""

    def __init__(self) -> None:
        self._tools: dict[str, StructuredTool] = {}

    def register(self, tool: StructuredTool) -> None:
        self._tools[tool.name] = tool

    def list_tools(self) -> list[str]:
        return sorted(self._tools.keys())

    def execute(self, tool_name: str, arguments: dict) -> ToolCallRecord:
        tool = self._tools.get(tool_name)
        if tool is None:
            return ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                output={},
                error=f"Unknown tool: {tool_name}",
            )
        try:
            output = tool.execute(arguments)
            return ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                success=True,
                output=output,
                error=None,
            )
        except ValidationError as exc:
            return ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                output={},
                error=f"validation error: {exc}",
            )
        except Exception as exc:  # pragma: no cover - defensive path
            LOGGER.exception("Tool execution failed", extra={"event": "tool_failed"})
            return ToolCallRecord(
                tool_name=tool_name,
                arguments=arguments,
                success=False,
                output={},
                error=str(exc),
            )
