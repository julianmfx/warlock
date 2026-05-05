# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See `constitution.md` for the spirit, collaboration rules, and core principles of this project.

## Project

Warlock is a multi-agent AI platform built from scratch — no LangChain. It receives a raw problem, routes it to specialist agents via an orchestrator, and synthesizes a unified output. The architecture is intentionally layered and decoupled: agents never call each other directly; shared memory is the only communication bus.

## Stack

- Python 3.14, managed with `uv`
- LLM backend: Anthropic Claude API (use `claude-sonnet-4-6` as default model)
- Memory: in-process dict (phase 1), upgradeable to Redis/vector store later
- Serving: FastAPI (phase 5, not yet started)

## Commands

```bash
uv run main.py          # run the entrypoint
uv add <package>        # add a dependency
uv sync                 # install dependencies from lockfile
```

No test runner or linter is configured yet. When adding them, prefer `pytest` and `ruff`.

## Architecture

Four layers, built in order:

1. **Orchestrator** (`warlock/orchestrator.py`) — decomposes the problem, routes to agents, manages lifecycle
2. **Specialist Agents** (`warlock/agents/`) — one class per domain, each inherits from a base `Agent`; domains: `data_engineer`, `ml_engineer`, `analytics`, `devops_mlops`, `bi_agent`, `software_dev`
3. **Shared Memory** (`warlock/memory.py`) — a key-value store (`problem_statement`, `task_decomposition`, `agent_outputs`, `iteration`); the only way agents share state
4. **Synthesizer** (`warlock/synthesizer.py`) — collects all agent outputs, resolves conflicts, produces the final answer

## Core principles (from plan.md)

- **One agent, one domain.** No agent crosses boundaries.
- **Memory is the bus.** Agents never call each other directly.
- **The synthesizer owns truth.** It has final say on output.
- **Cost discipline.** Default to `claude-haiku-4-5` for routing/classification tasks, `claude-sonnet-4-6` for reasoning, `claude-opus-4-7` only when depth demands it. Always use prompt caching (`cache_control`) on large shared context (system prompts, memory dumps). Track token spend per agent run.
- **Learn by doing.** Ship the simplest working version at each phase before designing the next. Every phase must produce something runnable.
- Build what *should* exist, not what already does.

## Build sequence

See `plan.md` for the phased checklist. Start with Phase 1: `Orchestrator`, `Memory`, and base `Agent` class.
