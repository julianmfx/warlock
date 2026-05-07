# Warlock — Session Resume
> *Pick up exactly where we left off.*

---

## What Warlock is

A multi-agent AI platform for Data, AI, Data Science, Data Engineering, Analytics, BI, MLOps, DevOps, and Software Development.

**Core idea:** one orchestrator receives a raw problem, decomposes it, routes to specialist agents, each agent owns one domain, a synthesizer merges all outputs into a unified answer.

**Philosophy:** one agent, one domain. Memory is the bus. Agents never talk to each other directly.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, synthesizer owns truth, cost discipline).

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules.

### `warlock/memory.py` ✓ done

The shared state bus every agent reads from and writes to.

```python
from datetime import datetime

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

### `warlock/agent.py` ✓ done — live Claude API call confirmed working

The base class every specialist agent inherits from. This session: `run(task)` went from a `NotImplementedError` stub to a real Claude API call.

```python
import anthropic

class Agent:
    def __init__(self, name, identity, memory):
        self.name = name
        self.identity = identity
        self.memory = memory
        self._client = anthropic.Anthropic()

    def run(self, task):
        problem = self.memory.read("problem_statement")

        response = self._client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=[
                {
                    "type": "text",
                    "text": self.identity,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Problem: {problem}\n\nTask: {task}",
                }
            ],
        )

        output = response.content[0].text

        agent_outputs = self.memory.read("agent_outputs") or {}
        agent_outputs[self.name] = output
        self.memory.write("agent_outputs", agent_outputs)

        return output

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
```

**Key concepts unlocked this session:**
- `_client = anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from the environment automatically
- `cache_control: ephemeral` on the system prompt — identity is large and stable, so we cache it to save tokens on repeated calls
- `agent_outputs` is a dict in memory — we read it, add our entry, write it back — so multiple agents accumulate without overwriting each other
- Model used: `claude-haiku-4-5-20251001` — cheapest available (Claude 3 Haiku is no longer on the API; only Claude 4.x models are available)

### `main.py` ✓ done — calls run(), confirmed real output

```python
from warlock.agent import Agent
from warlock.memory import Memory

m = Memory()
m.write("problem_statement", "Ingest CSV into BigQuery")

data_engineer = Agent(
    name="data_engineer",
    identity="I am a data engineer with over 30 years of experience...",
    memory=m,
)

output = data_engineer.run("Design the ingestion pipeline for this problem.")
print(output)
```

**Confirmed:** agent returned a full pipeline design with code — the core loop is live.

---

## What we are building next

### `warlock/agents/data_engineer.py` — first specialist agent

The base `Agent` already does everything. The specialist simply inherits it and sets the right name and identity. The pattern:

```python
from warlock.agent import Agent

class DataEngineerAgent(Agent):
    def __init__(self, memory):
        super().__init__(
            name="data_engineer",
            identity="I am a data engineer with over 30 years of experience. I move data, create data pipelines, build data models. I do pipelines, ingestion, transformation, schemas and data quality checks.",
            memory=memory,
        )
```

Then update `main.py` to import and instantiate `DataEngineerAgent` instead of the base `Agent` directly.

**Why this matters:** once we have a specialist class, we can register it in the orchestrator by type. The orchestrator will know: "for data pipeline tasks, route to `DataEngineerAgent`."

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py        ✓ done
├── agent.py         ✓ done — live API call
└── agents/
    └── __init__.py
constitution.md      ✓ done
CLAUDE.md            ✓ done
main.py              ✓ done — calls run(), output confirmed
pyproject.toml
list_models.py       (scratch file — can be deleted)
```

---

## Build sequence

- [x] `warlock/memory.py` — shared memory layer
- [x] `warlock/agent.py` — base Agent class with describe() and run() guardrail
- [x] `warlock/agent.py` — run(task) with live Claude API call and prompt caching
- [ ] `warlock/agents/data_engineer.py` — first specialist, inherits Agent ← **start here next session** — but first: (1) review and commit all pending changes from the previous session (`git diff`, understand each change, then `git commit`); (2) revisit `agent.py` `run()` — the live API call wasn't fully understood yet, walk through it line by line before moving on
- [ ] `warlock/orchestrator.py` — decomposes problems, routes to agents
- [ ] `warlock/synthesizer.py` — merges all agent outputs into one answer

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
