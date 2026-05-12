# Warlock

A multi-agent AI platform built from scratch. Receives a raw problem, routes it to specialist agents, and produces a unified output through triangle consensus.

No LangChain. Agents collaborate through shared memory and the triangle consensus loop — never through direct calls.

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

Warlock uses a triangle architecture with three equal peers and no single point of authority.

```
        Orchestrator
           /    \
          /      \
    Supervisor — Agents
```

Any corner can reject, push back, or validate another. A decision is confirmed only when all three agree. The final output is an emergent result of consensus — no single corner owns it.

If consensus is not reached after 3 iterations, Warlock emits the best-effort output tagged with a confidence score.

### Layers

| Component | File | Responsibility |
|---|---|---|
| Orchestrator | `warlock/orchestrator.py` | Decomposes problem, routes to agents, participates in consensus |
| Supervisor | `warlock/supervisor.py` | Validates outputs, challenges decompositions, participates in consensus |
| Agents | `warlock/agents/` | Execute domain work, flag uncertainty to trigger the triangle |
| Shared memory | `warlock/memory.py` | Key-value bus all corners read/write |
| LLM contract | `warlock/llm.py` | Provider-agnostic `LLMClient` Protocol |
| Provider adapter | `warlock/providers/anthropic.py` | Anthropic SDK, prompt caching, token tracking |

## Status

Phase 1 in progress. Core layer (memory, base agent, LLM abstraction) is live. Specialist agents, Orchestrator, and Supervisor are next.
