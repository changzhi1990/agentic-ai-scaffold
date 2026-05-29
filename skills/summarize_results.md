---
name: summarize_results
description: Summarize long tool outputs or documents while preserving technical meaning.
when_to_use:
  - when tool results or long documents need summarization
  - when the final answer should compress operational data clearly
required_tools:
  - read_file
  - search_knowledge_base
examples:
  - "Summarize the retrieved knowledge about logs."
  - "Condense the tool outputs into a brief report."
---
Extract key facts, keep technical meaning intact, and present the result as a concise structured summary. Call out failure conditions, missing data, and operationally relevant details.
