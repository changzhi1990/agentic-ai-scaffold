"""Typer CLI for the agent runtime."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from app.agent import AgentApp, TaskAgent
from app.models import TaskRequest


cli_app = typer.Typer(add_completion=False, help="Engineering-oriented agentic AI scaffold CLI.")


@cli_app.command("run")
def run_task(task: str, context: str = "{}", pretty: bool = False) -> None:
    """Execute a task and print the structured response."""
    parsed_context = json.loads(context)
    project_root = Path(__file__).resolve().parents[1]
    app = AgentApp.from_project_root(project_root)
    agent = TaskAgent(app)
    response = agent.run(TaskRequest(task=task, context=parsed_context))
    payload = response.model_dump(mode="json")
    typer.echo(json.dumps(payload, indent=2 if pretty else None))


@cli_app.command("serve")
def serve(host: str = "127.0.0.1", port: int = 8080) -> None:
    """Start the FastAPI server with uvicorn."""
    import uvicorn

    uvicorn.run("interfaces.api:app", host=host, port=port, reload=False)
