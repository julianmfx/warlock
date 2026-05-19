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

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules.

### `warlock/memory.py` ✓ done

The shared state bus every corner of the triangle reads from and writes to.

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

`print_log()` was improved this session: detects dict-of-strings (agent outputs) and renders them as readable markdown instead of escaped JSON. Other values (dicts, lists) are pretty-printed as JSON with separators.

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

### `warlock/agents/data_engineer.py` ✓ done — first specialist agent

```python
from warlock.agent import Agent
from warlock.llm import LLMClient

ROLE = """..."""  # production-grade system prompt (see file for full text)

class DataEngineerAgent(Agent):
    def __init__(self, memory, client: LLMClient, model: str):
        super().__init__(
            name="data_engineer",
            identity=ROLE,
            memory=memory,
            client=client,
            model=model,
        )
```

**Key concepts:**
- Model is passed by the caller — the specialist does not hardcode it
- `ROLE` is a module-level constant — identity text separate from class logic
- System prompt covers: reasoning approach, proposal format, technical grounding (BigQuery, Snowflake, Databricks, dbt, Kafka, Airflow, OpenTelemetry + more), cost awareness across all dimensions (storage, compute, egress, dev time, on-call, lock-in), anti-sycophancy rule, testing as test coverage not dashboards, GitOps for pipeline code

### `warlock/agents/ml_engineer.py` ✓ done — machine learning specialist

Same pattern as `data_engineer`. ROLE covers: do-we-need-ML gate, gather-before-proposing (data, latency, eval criteria, stack, deployment, time horizon), baseline-before-complexity, evaluation-before-deployment, reproducibility, fairness and disparate impact surfacing, pushback handling (update on evidence not pressure), 18-month maintainability question, monitoring as a pre-deployment requirement.

### `warlock/agents/analytics.py` ✓ done — analytics + BI specialist

Absorbs the BI domain. ROLE covers: analysis vs. confirmation distinction, one-time analysis vs. recurring artifact, metric definition alignment before building, audience-tailoring (executive/operational/technical), tool selection heuristic (SQL → BI tool → Python → dbt), segment-before-concluding, profile-before-you-conclude, context-beats-precision, trust-is-fragile, causality path (name the identification strategy), hand-off recognition.

### `warlock/agents/devops_mlops.py` ✓ done — DevOps / MLOps specialist

ROLE covers: SLA/SLO/SLI distinction, RPO/RTO, migration cutover strategies, ML-specific probes (champion-challenger, shadow mode, data pipeline failures), incident response priority order (stabilize → diagnose → optimize), rollout strategies (shadow/canary/blue-green/A/B/progressive), boring technology principle, error budgets, post-mortem anatomy (multiple contributing factors, named owners), DR vs. incident response distinction, alert fatigue as operational failure, deprecation discipline, security as "scheduled incident."

### `warlock/agents/data_scientist.py` ✓ done — data science specialist (new this session)

Added in Phase 3 after recognizing the gap between analytics (monitors known things) and ML engineering (builds production systems). The data scientist owns the space between them: problem formulation, experimentation, and statistical methodology.

ROLE covers: predictive/causal/descriptive distinction as the most consequential framing choice, unit of analysis, data-generating process validation, baseline and leakage probes, EXPERIMENTATION DISCIPLINE section (pre-registration, power analysis before not after, heterogeneity planning, researcher degrees of freedom), identification before estimation, uncertainty as the deliverable not the disclaimer, statistical vs. business significance, fairness and disparate impact, motivated analysis pushback, model monitoring as a pre-deployment requirement, feature engineering and validation strategy ownership (hands production system to ML engineer).

### `warlock/agents/software_dev.py` ✓ done — software engineering specialist

ROLE covers: interface-before-implementation as the organizing philosophy, async/event-driven delivery guarantee probes (at-most-once/at-least-once/exactly-once, dead letter strategy), boundary definition (network/trust/persistence), backwards compatibility discipline (additive safe, removal breaking, semantic change breaking, deprecation lifecycle), distributed systems failure modes (timeouts, retries, circuit breakers as defaults), contract testing as most valuable at boundaries, database hazards (N+1, long transactions, connection pool exhaustion, migrations), implicit schema risk from uncontrolled upstream sources, specific handoff partners named (data engineering, data science, ML engineering, MLOps, security).

### `warlock/orchestrator.py` ✓ done — problem decomposition and routing

```python
import json
from warlock.llm import LLMClient

ROLE = """..."""  # instructs LLM to return JSON array of {domain, task} objects

class Orchestrator:
    def __init__(self, memory, client: LLMClient, model: str):
        self._memory = memory
        self._client = client
        self._model = model
        self._agents = {}

    def register(self, agent): ...     # adds agent to registry by agent.name
    def decompose(self, problem): ...  # LLM call → list of {"domain": ..., "task": ...}
    def run(self, problem): ...        # writes problem_statement, decomposes, routes, executes
```

**Key concepts:**
- `decompose()` calls the LLM and parses a JSON array — structured output, not free-form
- Defensive strip removes markdown code fences if the model wraps output in ` ```json ``` `
- Routes by domain key — only runs agents that are registered
- Empty decomposition (`[]`) is a silent no-op — known edge case, Supervisor will handle in Phase 4

### `main.py` ✓ done — wires everything together

Currently only registers `data_engineer`. Needs to be updated to register all six agents.

---

## What we are building next

### Step 1 — Register all six agents in `main.py`

Update `main.py` to import and register all agents:

```python
from warlock.agents.data_engineer import DataEngineerAgent
from warlock.agents.ml_engineer import MLEngineerAgent
from warlock.agents.analytics import AnalyticsAgent
from warlock.agents.devops_mlops import DevOpsMLOpsAgent
from warlock.agents.data_scientist import DataScientistAgent
from warlock.agents.software_dev import SoftwareDevAgent
from warlock.memory import Memory
from warlock.orchestrator import Orchestrator
from warlock.providers.anthropic import AnthropicClient

m = Memory()
client = AnthropicClient()

orchestrator = Orchestrator(memory=m, client=client, model="claude-haiku-4-5-20251001")

orchestrator.register(DataEngineerAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))
orchestrator.register(MLEngineerAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))
orchestrator.register(AnalyticsAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))
orchestrator.register(DevOpsMLOpsAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))
orchestrator.register(DataScientistAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))
orchestrator.register(SoftwareDevAgent(memory=m, client=client, model="claude-haiku-4-5-20251001"))

orchestrator.run("Build a churn prediction system for a SaaS product")
m.print_log()
```

Run it to confirm all six agents route and respond correctly end-to-end.

### Step 2 — Phase 4: Supervisor

After the multi-agent run is confirmed, begin `warlock/supervisor.py`:

```python
class Supervisor:
    def __init__(self, memory, client: LLMClient, model: str):
        ...

    def validate(self, agent_name: str, output: str) -> bool:
        # reviews agent output for quality and domain correctness
        # returns True (accept) or False (reject, trigger triangle)
        ...
```

---

## Known edge cases (Phase 4)

- **Empty decomposition** — orchestrator returns `[]` silently when problem doesn't match any domain. Supervisor will handle this.
- **Out-of-domain problems** — no feedback to the user when nothing runs. Same fix.

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py              ✓ done — shared state bus, pretty print_log
├── agent.py               ✓ done — base Agent, run(), token tracking
├── llm.py                 ✓ done — LLMClient Protocol, LLMResponse, LLMUsage
├── orchestrator.py        ✓ done — decompose, register, route, run
├── providers/
│   ├── __init__.py        ✓ done
│   └── anthropic.py       ✓ done — AnthropicClient, cache_control on system prompt
└── agents/
    ├── __init__.py        ✓ done
    ├── data_engineer.py   ✓ done — DataEngineerAgent, production-grade ROLE
    ├── ml_engineer.py     ✓ done — MLEngineerAgent, production-grade ROLE
    ├── analytics.py       ✓ done — AnalyticsAgent, absorbs BI domain
    ├── devops_mlops.py    ✓ done — DevOpsMLOpsAgent, production-grade ROLE
    ├── data_scientist.py  ✓ done — DataScientistAgent, production-grade ROLE
    └── software_dev.py    ✓ done — SoftwareDevAgent, production-grade ROLE
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done (needs agent registrations updated) ← next
supervisor.py               ← Phase 4
pyproject.toml
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
