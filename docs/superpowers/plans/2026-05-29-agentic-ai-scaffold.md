# Agentic AI Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable Python scaffold for an autonomous task-oriented agent with skills, tools, knowledge retrieval, CLI/API interfaces, and agent-to-agent calls.

**Architecture:** A small `AgentApp` bootstrap will load config, skills, knowledge, tool registry, and LLM provider. A `TaskAgent` will orchestrate retrieval, planning, optional tool execution, and final response generation using structured models. FastAPI and Typer will expose the same runtime.

**Tech Stack:** Python 3.11+, pydantic, fastapi, typer, uvicorn, httpx, PyYAML, pytest

---

### Task 1: Write the initial failing tests

**Files:**
- Create: `tests/test_kb.py`
- Create: `tests/test_tools.py`
- Create: `tests/test_agent.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_search_returns_matches():
    ...
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_kb.py tests/test_tools.py tests/test_agent.py -v`
Expected: FAIL because modules are not implemented yet

- [ ] **Step 3: Write minimal implementation**

Create the package and modules required by the tests.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_kb.py tests/test_tools.py tests/test_agent.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add agentic ai scaffold"
```

### Task 2: Implement runtime modules and docs

**Files:**
- Create: `README.md`
- Create: `AGENT.md`
- Create: `SKILLS.md`
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `config/settings.yaml`
- Create: `app/*.py`
- Create: `llm/**/*.py`
- Create: `tools/**/*.py`
- Create: `knowledge/**/*.py`
- Create: `interfaces/*.py`
- Create: `skills/*.md`

- [ ] **Step 1: Implement focused modules with explicit boundaries**

Add models, config loading, planner, memory, logging, exceptions, skill loading, provider abstraction, tool registry, knowledge retriever, and interfaces.

- [ ] **Step 2: Run tests and import smoke checks**

Run: `pytest -q`
Expected: PASS

- [ ] **Step 3: Start CLI and API smoke checks**

Run: `python -m app.main run "Summarize the sample knowledge base"`
Expected: JSON response printed

Run: `python -c "from interfaces.api import app; print(app.title)"`
Expected: `Agentic AI Scaffold API`

- [ ] **Step 4: Refactor only if all tests stay green**

Keep the implementation simple and readable.
