"""FastAPI interface for the agent runtime."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.agent import AgentApp, TaskAgent
from app.models import TaskRequest, TaskResponse


project_root = Path(__file__).resolve().parents[1]
runtime = AgentApp.from_project_root(project_root)
agent = TaskAgent(runtime)

app = FastAPI(title="Agentic AI Scaffold API", version=runtime.config.app_version)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/run", response_model=TaskResponse)
def run_task(request: TaskRequest) -> TaskResponse:
    return agent.run(request)
