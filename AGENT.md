# Agent Contract: EngineeringTaskAgent

## Purpose

Reusable engineering-oriented task agent for Linux environments. It accepts a task, optionally retrieves local knowledge, selects skills, creates a plan, executes tools, and returns a structured result.

## Capabilities

- Task analysis and lightweight planning
- Local knowledge retrieval from markdown/text/log files
- Declarative skill loading from markdown
- Structured tool execution
- Shell command execution with timeout
- File read/write operations
- HTTP API calls
- Remote agent invocation through HTTP or local mock transport
- CLI and FastAPI interfaces

## Limitations

- Default knowledge retrieval is keyword-based, not embedding-based
- The offline fallback LLM is deterministic and heuristic
- The shell tool is powerful and should be restricted before production deployment
- Memory is in-process only

## Input Schema

```json
{
  "task": "string",
  "context": {
    "optional": "object with extra execution hints"
  }
}
```

## Output Schema

```json
{
  "task": "string",
  "selected_skills": ["string"],
  "knowledge_used": [
    {
      "document_id": "string",
      "title": "string",
      "score": 0.0,
      "snippet": "string",
      "source_path": "string"
    }
  ],
  "plan": [
    {
      "step_id": "string",
      "description": "string",
      "reason": "string",
      "tool_name": "string|null"
    }
  ],
  "tool_calls": [
    {
      "tool_name": "string",
      "arguments": {},
      "success": true,
      "output": {},
      "error": "string|null"
    }
  ],
  "final_answer": "string",
  "status": "success|partial_success|failed"
}
```

## Available Tools

- `run_shell_command`
- `read_file`
- `write_file`
- `search_knowledge_base`
- `call_http_api`
- `call_agent`

## Expected Execution Flow

1. Normalize input into a task request
2. Load matching skills from disk
3. Retrieve local knowledge when the task is factual, project-specific, or explicitly asks for context
4. Build a stepwise plan
5. Execute forced or necessary tool calls
6. Interpret tool results and produce a structured response
7. Persist the run in memory

## How Another Agent Can Call It

### HTTP

Send `POST /run` with the input schema shown above.

### As a Tool

Use the `call_agent` tool:

```json
{
  "agent_name": "engineering-task-agent",
  "endpoint": "http://host:8080/run",
  "task": "Summarize benchmark logs",
  "context": {
    "run_id": "abc-123"
  }
}
```

### Mock Transport

For local testing:

```json
{
  "agent_name": "report-agent",
  "endpoint": "mock://report-agent",
  "task": "Summarize the attached results",
  "context": {
    "source": "local-test"
  }
}
```
