---
name: delegate_to_agent
description: Hand work to a specialized downstream agent when it is a better fit.
when_to_use:
  - when another specialized agent is better suited
  - when the task should be routed to reporting, diagnostics, or analysis agents
required_tools:
  - call_agent
examples:
  - "Ask the report agent to summarize benchmark results."
  - "Send this diagnostics job to the incident agent."
---
Prepare a clean payload with task and context, call the downstream agent through the `call_agent` tool, and interpret the returned result rather than echoing it blindly.
