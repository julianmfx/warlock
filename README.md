# Warlock

A multi-agent AI platform built from scratch. Receives a raw problem, routes it to specialist agents via an orchestrator, and synthesizes a unified output.

No LangChain. Agents communicate through shared memory only.

## Stack

- Python 3.14, managed with `uv`
- LLM backend: provider-agnostic (`LLMClient` Protocol — `AnthropicClient` ships first)
- Memory: in-process key-value store (upgradeable to Redis/vector store)
- Serving: FastAPI (not yet started)

## Run

```bash
uv run main.py
```

## Architecture

| Layer | File | Responsibility |
|---|---|---|
| LLM contract | `warlock/llm.py` | Provider-agnostic `LLMClient` Protocol |
| Provider adapter | `warlock/providers/anthropic.py` | Anthropic SDK, prompt caching, token tracking |
| Base agent | `warlock/agent.py` | Runs a task, writes output and token spend to memory |
| Shared memory | `warlock/memory.py` | Key-value bus all agents read/write |

## Status

Phase 1 in progress. Core layer (memory, base agent, LLM abstraction) is live. Specialist agents and orchestrator are next.
