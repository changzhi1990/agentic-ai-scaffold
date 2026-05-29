# Agentic AI Scaffold Design

## Goal

Build a runnable Python 3.11+ starter framework for an engineering-oriented agentic AI system with a clean reasoning layer, declarative skills, auditable tool execution, lightweight knowledge retrieval, CLI/API interfaces, and agent-to-agent communication.

## Recommended Approach

Use a modular package layout with small focused files and explicit data models. The runtime flow will be:

1. Normalize the request into a `TaskRequest`
2. Retrieve local knowledge snippets when the task looks complex or factual
3. Load markdown skill definitions from disk
4. Build a lightweight plan using a planner module
5. Ask an LLM provider for a structured response, with a deterministic fallback provider when no API key is configured
6. Execute tool calls through a registry with per-tool validation and structured error capture
7. Return a structured `TaskResponse` containing plan, tool calls, knowledge used, and final answer

## Alternatives Considered

### Option 1: Fully deterministic planner-only scaffold

Pros: simplest runtime, no external dependencies for the reasoning path.
Cons: does not demonstrate the LLM/provider abstraction strongly enough.

### Option 2: Heavy graph-orchestrator scaffold

Pros: advanced orchestration and rich future expansion.
Cons: too much framework weight for a starter project and weakens readability.

### Option 3: Recommended hybrid scaffold

Use a small deterministic planner and fallback policy alongside a clean LLM provider interface. This keeps the scaffold runnable with no secrets while remaining easy to swap to OpenAI-compatible or vLLM APIs.

## Design Decisions

### Runtime

- `app/agent.py` owns the execution loop and returns a single structured response
- `app/planner.py` creates an ordered plan based on the task, chosen skills, and retrieved knowledge
- `app/memory.py` stores recent runs in memory for auditability and future extension
- `llm/base.py` defines backend contracts
- `llm/providers/openai_compatible.py` provides both live API support and a deterministic offline fallback

### Skills

- Skills are markdown files with YAML front matter plus free-form instructions
- `app/skills_loader.py` parses them into `SkillDefinition`
- Skill selection is simple, explicit, and inspectable rather than opaque magic

### Tools

- All actions go through `ToolRegistry`
- Tools use pydantic input and output models
- Failures become structured `ToolCallRecord` entries rather than uncaught exceptions
- Included tools: shell, file I/O, HTTP, KB search, and remote-agent calls

### Knowledge

- Local markdown documents under `knowledge/docs/`
- Retrieval starts with keyword scoring and snippet extraction
- `knowledge/base.py` leaves room for a future vector store without changing callers

### Interfaces

- CLI implemented with Typer
- API implemented with FastAPI
- Both reuse the same `AgentApp` bootstrap and `TaskAgent` runtime

### Failure Handling

- Centralized exceptions with structured logging
- Tool, LLM, KB, and downstream agent failures produce partial results where possible
- Response status is one of `success`, `partial_success`, or `failed`

### Testing

- Unit tests cover KB retrieval, tool execution, and end-to-end agent flow
- Smoke checks validate CLI importability and API app creation

## Output Scope

The scaffold will include README, AGENT contract doc, skills documentation, requirements, config, app modules, provider abstraction, tool registry, knowledge docs, CLI/API entrypoints, and tests.
