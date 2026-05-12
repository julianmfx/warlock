# Warlock — Session Resume
> *Pick up exactly where we left off.*

---

## What Warlock is

A multi-agent AI platform for Data, AI, Data Science, Data Engineering, Analytics, BI, MLOps, DevOps, and Software Development.

**Core idea:** a triangle of three equal peers — Orchestrator, Supervisor, and Agents — with checks and balances between them. Any corner can reject, push back, or validate another. The final output is an emergent result of consensus, not owned by any single corner.

**Escape valve:** after 3 iterations without full consensus, Warlock emits the best-effort output tagged with a confidence score.

**Philosophy:** one agent, one domain. Memory is the bus. Agents collaborate through shared memory and the triangle consensus loop — never through direct calls. No single point of authority.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, triangle consensus owns truth, cost discipline).

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules.

### `warlock/memory.py` ✓ done

The shared state bus every agent reads from and writes to.

```python
class Memory:
    def __init__(self):
        self._store = {}
        self._log = []

    def write(self, key, value): ...
    def read(self, key): ...
    def dump(self): ...
    def log(self): ...
    def print_log(self): ...
```

### `warlock/llm.py` ✓ done — provider contract

The language Warlock uses to talk to any LLM. Three types:

```python
from dataclasses import dataclass
from typing import Any, Protocol

@dataclass
class LLMUsage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0

@dataclass
class LLMResponse:
    text: str
    usage: LLMUsage

class LLMClient(Protocol):
    def complete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> LLMResponse: ...
```

**Key concepts:**
- `LLMClient` is a `Protocol` — any class with a matching `complete()` signature satisfies it, no inheritance required
- `system` is a plain string — the adapter decides how to format it for its provider
- `model` travels through `complete()` so one client instance can serve agents using different models
- `cache_read_tokens` defaults to `0` for providers that don't report it

### `warlock/providers/__init__.py` ✓ done

Empty package file.

### `warlock/providers/anthropic.py` ✓ done — first provider adapter

All Anthropic-specific logic lives here. Nothing leaks out.

```python
from typing import Any, cast
import anthropic
from anthropic.types import MessageParam
from warlock.llm import LLMResponse, LLMUsage

class AnthropicClient:
    def __init__(self):
        self._client = anthropic.Anthropic()

    def complete(
        self,
        model: str,
        system: str,
        messages: list[dict[str, Any]],
        max_tokens: int = 1024,
    ) -> LLMResponse:
        response = self._client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=cast(list[MessageParam], messages),
        )
        text = next(block.text for block in response.content if block.type == "text")
        usage = LLMUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            cache_read_tokens=getattr(response.usage, "cache_read_input_tokens", 0),
        )
        return LLMResponse(text=text, usage=usage)
```

**Key concepts:**
- `cache_control: ephemeral` on the system prompt — Anthropic-specific, contained here
- `cast(list[MessageParam], messages)` — type-checker hint only, no runtime effect
- `getattr(..., "cache_read_input_tokens", 0)` — only present in response on a cache hit

### `warlock/agent.py` ✓ done — provider-agnostic, token tracking live

```python
from warlock.llm import LLMClient

class Agent:
    def __init__(self, name, identity, memory, client: LLMClient, model: str):
        self.name = name
        self.identity = identity
        self.memory = memory
        self._client = client
        self._model = model

    def run(self, task):
        problem = self.memory.read("problem_statement")

        response = self._client.complete(
            model=self._model,
            system=self.identity,
            messages=[{"role": "user", "content": f"Problem: {problem}\n\nTask: {task}"}],
        )

        agent_outputs = self.memory.read("agent_outputs") or {}
        agent_outputs[self.name] = response.text
        self.memory.write("agent_outputs", agent_outputs)

        token_spend = self.memory.read("token_spend") or {}
        token_spend[self.name] = {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "cache_read_tokens": response.usage.cache_read_tokens,
        }
        self.memory.write("token_spend", token_spend)

        output = response.text
        return output

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
```

**Key concepts:**
- No `import anthropic` — the agent is fully provider-agnostic
- `token_spend` is written to memory after every run — cost tracking is live
- `output = response.text` before `return` is a minor redundancy deferred by the user

### `main.py` ✓ done — wires AnthropicClient to Agent

```python
from warlock.agent import Agent
from warlock.memory import Memory
from warlock.providers.anthropic import AnthropicClient

m = Memory()
m.write("problem_statement", "Ingest CSV into BigQuery")

client = AnthropicClient()

data_engineer = Agent(
    name="data_engineer",
    identity="I am a data engineer with over 30 years of experience...",
    memory=m,
    client=client,
    model="claude-haiku-4-5-20251001",
)

output = data_engineer.run("Design the ingestion pipeline for this problem.")
print(output)
```

---

## What we are building next

### `warlock/agents/data_engineer.py` — first specialist agent

The base `Agent` already does everything. The specialist inherits it and fixes the name, identity, and model. Now it also needs to accept and forward `client`:

```python
from warlock.agent import Agent
from warlock.llm import LLMClient

class DataEngineerAgent(Agent):
    def __init__(self, memory, client: LLMClient):
        super().__init__(
            name="data_engineer",
            identity="I am a data engineer with over 30 years of experience. I move data, create data pipelines, build data models. I do pipelines, ingestion, transformation, schemas and data quality checks.",
            memory=memory,
            client=client,
            model="claude-haiku-4-5-20251001",
        )
```

Then update `main.py` to import and instantiate `DataEngineerAgent` instead of the base `Agent` directly.

**Why this matters:** once we have a specialist class, we can register it in the orchestrator by type. The orchestrator will know: "for data pipeline tasks, route to `DataEngineerAgent`."

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py           ✓ done
├── agent.py            ✓ done — provider-agnostic, token tracking live
├── llm.py              ✓ done — LLMClient Protocol, LLMResponse, LLMUsage
├── providers/
│   ├── __init__.py     ✓ done
│   └── anthropic.py    ✓ done — AnthropicClient adapter
└── agents/
    └── __init__.py
constitution.md          ✓ done
CLAUDE.md                ✓ done
main.py                  ✓ done — wires AnthropicClient to Agent
pyproject.toml
list_models.py           (scratch file — can be deleted)
warlock/agents/data_engineer.py   ← next
```

---

## Build sequence

- [x] `warlock/memory.py` — shared memory layer
- [x] `warlock/agent.py` — base Agent class with describe() and run()
- [x] `warlock/llm.py` — provider-agnostic LLMClient Protocol
- [x] `warlock/providers/anthropic.py` — AnthropicClient adapter
- [ ] `warlock/agents/data_engineer.py` — first specialist, inherits Agent ← **start here next session**
- [ ] `warlock/orchestrator.py` — decomposes problems, routes to agents, participates in consensus
- [ ] `warlock/supervisor.py` — validates outputs, challenges decompositions, participates in consensus
- [ ] Triangle consensus loop — any corner can reject or push back, escape valve after 3 iterations

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
