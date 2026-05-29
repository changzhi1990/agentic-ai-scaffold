---
name: call_tool
description: Use the tool layer as the only execution path for external actions.
when_to_use:
  - when the task requires shell execution, file I O, HTTP requests, or other actions
required_tools:
  - run_shell_command
  - read_file
  - write_file
  - call_http_api
examples:
  - "Read the benchmark report file."
  - "Call an API and summarize the result."
---
Treat tools as the only execution layer. Validate inputs, interpret outputs, and capture failures in structured form. Do not imply that a tool succeeded when it returned an error.
