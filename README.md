# Agentic AI Scaffold

A production-style Python starter framework for building autonomous task-oriented agents that reason with an LLM, retrieve knowledge, select reusable skills, execute tools, and optionally call other agents.

## What This Agent Is

This project is an agent runtime, not just a chatbot. It is designed for practical engineering workflows such as Linux command execution, benchmark automation, log analysis, report generation, and future multi-agent orchestration.

Core runtime layers:

- LLM reasoning layer with an OpenAI-compatible provider abstraction
- Skill loader for declarative prompt modules
- Tool registry as the only execution path
- Local knowledge base and retrieval layer
- CLI and FastAPI interfaces
- Agent-to-agent call support through a callable tool

## System Overview

Execution flow:

1. Receive and normalize a task request
2. Load skills and evaluate likely skill matches
3. Retrieve local knowledge for complex or factual requests
4. Build an ordered plan
5. Execute tools when required or explicitly requested
6. Interpret tool outputs with the LLM provider
7. Return a structured response with plan, tool calls, knowledge used, and final answer

The default runtime works offline using a deterministic fallback LLM behavior. If you provide an OpenAI-style endpoint and API key, it will call `/chat/completions` instead.

## Architecture Summary

- `app/`: orchestration, models, planner, memory, logging, config bootstrap
- `llm/`: provider abstraction and OpenAI-compatible backend
- `tools/`: structured tool definitions and registry
- `skills/`: markdown skills with YAML front matter
- `knowledge/`: local document store and retriever
- `interfaces/`: CLI and FastAPI API
- `tests/`: starter tests for runtime behavior

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Configure

1. Copy `.env.example` to `.env` if you want environment-driven overrides.
2. Review `config/settings.yaml`.
3. Optionally set:

```bash
export OPENAI_API_BASE_URL="http://localhost:8000/v1"
export OPENAI_API_KEY="your-key"
export OPENAI_MODEL="gpt-4o-mini"
export LOG_LEVEL="INFO"
```

If no API credentials are set, the scaffold uses a deterministic local fallback response generator.

## Run CLI

```bash
source .venv/bin/activate
python -m app.main run "Summarize the local knowledge about benchmark automation"
```

Pretty output:

```bash
python -m app.main run "Read /etc/hostname" --pretty
```

## Run API Server

```bash
source .venv/bin/activate
uvicorn interfaces.api:app --host 0.0.0.0 --port 8080 --reload
```

## API Usage

`POST /run`

Example:

```bash
curl -X POST http://127.0.0.1:8080/run \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Plan a benchmark automation workflow and summarize the local knowledge",
    "context": {"source": "curl-demo"}
  }'
```

## Add a Skill

1. Create a markdown file under `skills/`.
2. Add YAML front matter with:
   - `name`
   - `description`
   - `when_to_use`
   - `required_tools`
   - `examples`
3. Add the instruction body below the front matter.

Example:

```markdown
---
name: inspect_logs
description: Analyze operational logs for errors.
when_to_use:
  - when the user asks about logs, incidents, or runtime failures
required_tools:
  - read_file
  - run_shell_command
examples:
  - "Inspect the nginx error log and summarize the failures."
---
Read the target log, extract repeating failures, and summarize the probable cause.
```

## Add a Tool

1. Create or update a tool module under `tools/`.
2. Define pydantic input and output schemas.
3. Wrap the handler in a `StructuredTool`.
4. Register it in `AgentApp.from_project_root()`.

Minimal example:

```python
tool = StructuredTool(
    name="my_tool",
    description="Example tool",
    input_model=MyInput,
    output_model=MyOutput,
    handler=my_handler,
)
registry.register(tool)
```

## Add Knowledge Documents

Drop markdown, text, or `.log` files into `knowledge/docs/`. The keyword retriever loads them at runtime and returns scored snippets.

## Example Usage

Summarize knowledge:

```bash
python -m app.main run "What does the knowledge base say about Linux command execution?"
```

Force a specific tool:

```bash
python -m app.main run "Read a file" \
  --context '{"force_tool":"read_file","tool_args":{"path":"README.md"}}'
```

Delegate to another agent:

```bash
python -m app.main run "Ask the report agent to summarize benchmark results" \
  --context '{
    "force_tool": "call_agent",
    "tool_args": {
      "agent_name": "report-agent",
      "endpoint": "mock://report-agent",
      "task": "Summarize benchmark results",
      "context": {"run_id": "demo-01"}
    }
  }'
```

## Test

```bash
source .venv/bin/activate
pytest -q
```
