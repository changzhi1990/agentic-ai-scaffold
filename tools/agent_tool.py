"""Agent-to-agent tool and transport abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import httpx
from pydantic import BaseModel, Field

from tools.base import StructuredTool


class AgentCallInput(BaseModel):
    agent_name: str = Field(..., min_length=1)
    endpoint: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    context: dict[str, Any] = Field(default_factory=dict)


class AgentCallOutput(BaseModel):
    result: dict[str, Any]


class AgentClient(ABC):
    """Abstract transport for downstream agents."""

    @abstractmethod
    def invoke(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke a downstream agent and return its structured result."""


class HttpAgentClient(AgentClient):
    """HTTP transport for remote agents."""

    def invoke(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=30) as client:
            response = client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()


class MockAgentClient(AgentClient):
    """Local mock transport for tests and demos."""

    def invoke(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        agent_name = endpoint.replace("mock://", "", 1)
        return {
            "agent_name": agent_name,
            "status": "success",
            "summary": f"Mock agent `{agent_name}` handled task: {payload['task']}",
            "context": payload.get("context", {}),
        }


def build_agent_tools(remote_agents: dict[str, dict[str, Any]]) -> list[StructuredTool]:
    def handler(data: AgentCallInput) -> AgentCallOutput:
        endpoint = data.endpoint or remote_agents.get(data.agent_name, {}).get("endpoint", "")
        client: AgentClient
        if endpoint.startswith("mock://"):
            client = MockAgentClient()
        else:
            client = HttpAgentClient()
        result = client.invoke(endpoint, {"task": data.task, "context": data.context})
        return AgentCallOutput(result=result)

    return [
        StructuredTool(
            name="call_agent",
            description="Call another agent over HTTP or a local mock transport.",
            input_model=AgentCallInput,
            output_model=AgentCallOutput,
            handler=handler,
        )
    ]
