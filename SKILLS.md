# Skills Guide

## What Skills Are

Skills are declarative prompt modules that describe reusable reasoning behaviors. They are not executable code and do not directly perform actions. The agent uses skills to shape planning and interpretation, while tools remain the only execution layer.

## Skill Structure

Each skill is a markdown file with YAML front matter and an instruction body.

Required front matter fields:

- `name`
- `description`
- `when_to_use`
- `required_tools`
- `examples`

The rest of the markdown file contains the actual instructions used by the agent.

## How to Add or Edit Skills

1. Create or edit a file under `skills/`.
2. Keep the metadata concise and specific.
3. Write instructions that tell the reasoning layer how to approach the problem.
4. Reference tools by name in `required_tools`, but do not place executable logic in the skill.

## How the Agent Selects Skills

The scaffold uses a transparent keyword-driven matcher:

- It tokenizes the task
- It compares the task to each skill’s name, description, and `when_to_use` phrases
- It selects matching skills
- If nothing matches, it falls back to `plan_task`

This is deliberately simple so the selection behavior is easy to debug. It can later be replaced by embedding similarity or an LLM-based routing policy.

## Included Example Skills

- `search_knowledge`: retrieve context before answering technical or project-specific questions
- `summarize_results`: compress tool outputs and large documents without losing technical meaning
- `plan_task`: decompose complex tasks into ordered steps
- `delegate_to_agent`: hand work to another specialized agent and interpret the result
- `call_tool`: explain how to prepare safe tool inputs and interpret outputs
