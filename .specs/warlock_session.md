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

### `CLAUDE.md` ✓ updated

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules.

### `warlock/memory.py` ✓ done

The shared state bus every agent reads from and writes to. Renamed from `WarlockMemory` to `Memory`.

```python
from datetime import datetime

class Memory:

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

### `warlock/agent.py` ✓ done

The base class every specialist agent inherits from. Tested and running.

```python
class Agent:

    def __init__(self, name, identity, memory):
        self.name = name
        self.identity = identity
        self.memory = memory

    def run(self, task):
        raise NotImplementedError("Each specialist agent must implement run()")

    def describe(self):
        print(f"Agent: {self.name}")
        print(f"Identity: {self.identity}")
        print(f"Memory: {self.memory.dump()}")
```

**Key concepts unlocked this session:**
- `Agent` does not import `Memory` — connection happens from the outside in `main.py` (duck typing)
- `run()` raises `NotImplementedError` — enforces the contract that every specialist must implement it
- `describe()` is a debug helper, not core logic

### `main.py` ✓ updated

Real test replacing the stub. Creates memory, writes a problem, instantiates an agent, calls describe().

```python
from warlock.memory import Memory
from warlock.agent import Agent

m = Memory()
m.write("problem_statement", "Ingest CSV into BigQuery")

data_engineer = Agent(
    name="data_engineer",
    identity="I am a data engineer with over 30 years of experience. I move data, create data pipelines, build data models. I do pipelines, ingestion, transformation, schemas and data quality checks",
    memory=m
)

data_engineer.describe()
```

**Confirmed output:**
```
Agent: data_engineer
Identity: I am a data engineer...
Memory: {'problem_statement': 'Ingest CSV into BigQuery'}
```

---

## What we are building next

### `warlock/agent.py` — add `run(task)` that calls the Claude API

This is when the agent becomes live. The method needs to:

1. Read `problem_statement` from memory
2. Build a prompt: combine identity (system prompt) + problem + task
3. Call the Claude API (`claude-sonnet-4-6`)
4. Write the response to `memory.agent_outputs[self.name]`
5. Return the response

The `run()` stub to replace:
```python
def run(self, task):
    raise NotImplementedError("Each specialist agent must implement run()")
```

Will become:
```python
def run(self, task):
    problem = self.memory.read("problem_statement")
    # build messages and call Anthropic client
    # write output to memory
    # return response
```

Install the Anthropic SDK first:
```bash
uv add anthropic
```

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py        ✓ done
├── agent.py         ✓ done — run(task) with Claude API ← next
└── agents/
    └── __init__.py
constitution.md      ✓ done
CLAUDE.md            ✓ updated
main.py              ✓ updated — test with real agent
pyproject.toml
```

---

## Build sequence

- [x] `warlock/memory.py` — shared memory layer
- [x] `warlock/agent.py` — base Agent class with describe() and run() guardrail
- [ ] `warlock/agent.py` — add `run(task)` with live Claude API call ← **start here next session**
- [ ] `warlock/agents/data_engineer.py` — first specialist, inherits Agent, overrides run()
- [ ] ReAct loop — reason → act → observe → repeat
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
