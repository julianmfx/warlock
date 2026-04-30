# Warlock — Session Resume
> *Pick up exactly where we left off.*

---

## What Warlock is

A multi-agent AI platform for Data, AI, Data Science, Data Engineering, Analytics, BI, MLOps, DevOps, and Software Development.

**Core idea:** one orchestrator receives a raw problem, decomposes it, routes to specialist agents, each agent owns one domain, a synthesizer merges all outputs into a unified answer.

**Philosophy:** one agent, one domain. Memory is the bus. Agents never talk to each other directly.

---

## What we have built so far

### `warlock/memory.py` ✓ done

The shared state bus every agent will read from and write to. Backed by a dict (current state) and a list (append-only audit log).

```python
from datetime import datetime

class WarlockMemory:

    def __init__(self):
        self._store = {}
        self._log = []

    def write(self, key, value):
        self._store[key] = value
        self._log.append({
            "ts": datetime.utcnow().isoformat(),
            "key": key,
            "value": value,
        })

    def read(self, key):
        return self._store.get(key, None)

    def dump(self):
        return self._store

    def log(self):
        return self._log

    def print_log(self):
        for entry in self._log:
            print(f"[{entry['ts']}] {entry['key']} = {entry['value']}")
```

**5 methods:**
- `write(key, value)` — stores a value + records it in the log
- `read(key)` — retrieves one value safely, returns None if missing
- `dump()` — shows full current state (what IS right now)
- `log()` — returns raw log history (what HAPPENED)
- `print_log()` — prints log in human-readable form

**Key concepts locked in:**
- `{}` is a dict — fast lookup by key, represents current state only
- `[]` is a list — ordered, append-only, nothing lost, audit trail
- `.get(key, None)` is safer than `[key]` — never crashes on a missing key

---

## What we are building next

### `warlock/agent.py` ← next file

Create this file and type this exact code:

```python
class Agent:

    def __init__(self, name, identity, memory):
        self.name = name
        self.identity = identity
        self.memory = memory

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
```

Then test it immediately in `main.py`:

```python
from warlock.memory import WarlockMemory
from warlock.agent import Agent

m = WarlockMemory()
m.write("problem_statement", "Ingest CSV into BigQuery")

data_engineer = Agent(
    name="data_engineer",
    identity="I move and shape data. Nothing else.",
    memory=m
)

data_engineer.describe()
```

**Expected output:**
```
Agent: data_engineer
Identity: I move and shape data. Nothing else.
Memory: {'problem_statement': 'Ingest CSV into BigQuery'}
```

Once that runs cleanly, the next step is adding a `run(task)` method to `Agent` that calls the Claude API — this is when the agent becomes live.

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py        ✓ done
├── agent.py         ← next
└── agents/
    └── __init__.py
main.py              (stub — update to test agent.py)
pyproject.toml
```

---

## What an Agent needs (derived from design)

```
1. A task        →  what they are supposed to do
2. A problem     →  the context they walk into (read from memory)
3. Tools         →  the functions they can call to act
4. Memory        →  where they read context and write results
```

---

## The 6 specialist agents planned

| Agent | Domain |
|---|---|
| `data_engineer` | Pipelines, ingestion, transformation, schemas |
| `ml_engineer` | Model design, training, evaluation, deployment |
| `analytics` | EDA, metrics, dashboards, insight generation |
| `devops_mlops` | Infra, CI/CD, model serving, monitoring |
| `bi_agent` | SQL, reports, KPIs, data storytelling |
| `software_dev` | APIs, services, integrations, tooling |

---

## Build sequence

- [x] `warlock/memory.py` — shared memory layer
- [ ] `warlock/agent.py` — base agent class ← **start here next session**
- [ ] `warlock/agent.py` — add `run(task)` with Claude API call
- [ ] `warlock/agents/data_engineer.py` — first specialist, tools: read_source, design_schema, generate_pipeline, validate_pipeline
- [ ] ReAct loop — reason → act → observe → repeat
- [ ] `warlock/orchestrator.py` — decomposes problems, routes to agents
- [ ] `warlock/synthesizer.py` — merges all agent outputs into one answer

---

## Principles

- We go slow. One concept at a time.
- We type, we don't copy.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
