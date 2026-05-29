"""HTTP API tool implementation."""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, Field

from tools.base import StructuredTool


class HttpCallInput(BaseModel):
    method: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    headers: dict[str, str] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = 20


class HttpCallOutput(BaseModel):
    status_code: int
    response: Any


def build_http_tools() -> list[StructuredTool]:
    return [
        StructuredTool(
            name="call_http_api",
            description="Call an HTTP API using a JSON request body.",
            input_model=HttpCallInput,
            output_model=HttpCallOutput,
            handler=_call_http_api,
        )
    ]


def _call_http_api(data: HttpCallInput) -> HttpCallOutput:
    with httpx.Client(timeout=data.timeout_seconds) as client:
        response = client.request(
            method=data.method.upper(),
            url=data.url,
            headers=data.headers,
            json=data.body if data.body else None,
        )
        payload: Any
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return HttpCallOutput(status_code=response.status_code, response=payload)
