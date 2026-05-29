from pathlib import Path

from app.agent import AgentApp, TaskAgent
from app.models import TaskRequest


def test_agent_returns_structured_response_for_complex_task() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = AgentApp.from_project_root(project_root)
    agent = TaskAgent(app)

    response = agent.run(
        TaskRequest(
            task="Plan a benchmark automation workflow using the local knowledge base and summarize the result.",
            context={"source": "test"},
        )
    )

    assert response.task.startswith("Plan a benchmark automation workflow")
    assert response.status in {"success", "partial_success"}
    assert response.selected_skills
    assert response.plan
    assert isinstance(response.tool_calls, list)
    assert response.final_answer


def test_agent_marks_failed_when_tool_execution_breaks() -> None:
    project_root = Path(__file__).resolve().parents[1]
    app = AgentApp.from_project_root(project_root)
    agent = TaskAgent(app)

    response = agent.run(
        TaskRequest(
            task="Read a file that does not exist at /definitely/missing.txt",
            context={"force_tool": "read_file", "tool_args": {"path": "/definitely/missing.txt"}},
        )
    )

    assert response.status in {"partial_success", "failed"}
    assert response.tool_calls
    assert response.tool_calls[0].success is False
