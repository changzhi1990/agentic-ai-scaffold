---
name: search_knowledge
description: Retrieve relevant knowledge before answering technical or project-specific questions.
when_to_use:
  - when the user asks factual or project-specific questions
  - when benchmark workflows, logs, or internal docs are relevant
required_tools:
  - search_knowledge_base
examples:
  - "What does the knowledge base say about Linux command execution?"
  - "Summarize benchmark automation guidance from internal docs."
---
Retrieve relevant context before answering. Prefer the knowledge base tool first, then summarize the most relevant snippets. Avoid answering from assumptions when local documents can provide better grounding.
