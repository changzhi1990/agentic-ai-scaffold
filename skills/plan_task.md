---
name: plan_task
description: Break a task into ordered steps and identify likely tools.
when_to_use:
  - when the request is multi-step or complex
  - when the user asks to plan, automate, orchestrate, or diagnose
required_tools:
  - search_knowledge_base
  - run_shell_command
  - call_agent
examples:
  - "Plan a benchmark automation workflow."
  - "Figure out how to diagnose this Linux service failure."
---
Break the task into ordered steps. Identify dependencies, required tools, and opportunities for retrieval before execution. Keep plans explicit and auditable.
