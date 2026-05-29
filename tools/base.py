"""Base classes for structured tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel


class StructuredTool:
    """Defines a tool with input/output schemas and a runtime handler."""

    def __init__(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        output_model: type[BaseModel],
        handler: Callable[[BaseModel], BaseModel],
    ) -> None:
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model
        self.handler = handler

    def execute(self, arguments: dict[str, Any]) -> dict[str, Any]:
        parsed_input = self.input_model.model_validate(arguments)
        result = self.handler(parsed_input)
        parsed_output = self.output_model.model_validate(result)
        return parsed_output.model_dump()
