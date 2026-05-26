# Warlock — Session Resume
> *Pick up exactly where we left off.*

---

## What Warlock is

A multi-agent AI platform for Data, AI, Data Science, Data Engineering, Analytics, BI, MLOps, DevOps, and Software Development.

**Core idea:** a triangle of three equal peers — Orchestrator, Supervisor, and Agents — with checks and balances between them. Any corner can reject, push back, or validate another. The final output is an emergent result of consensus, not owned by any single corner.

**Escape valve:** after 3 iterations without full consensus, Warlock emits the best-effort output tagged with a confidence score.

**Philosophy:** one agent, one domain. Memory is the bus. Agents collaborate through shared memory and the triangle consensus loop — never through direct calls. No single point of authority.

---

## This session

Spec-verification and housekeeping only — no new application code shipped. The single commit (`2b9cf6d`) broadened `.gitignore` to ignore all `*.txt` audit dumps and the `traces/` directory (previously only `output*.txt` was ignored). All four spec files were read and reconciled against the live code: `orchestrator.py`, `supervisor.py`, `memory.py`, the six agents, and `trace_logger.py` all match their documented state. The safety scan over `.specs/` and `.claude/` returned CLEAR.

The Phase 4 consensus loop remains the open frontier: `orchestrator.py` still does a single blind retry on rejection (P0 fixed, but the full reason-passing 3-iteration loop is not yet built).

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note updated to reflect Phase 4 in progress.

### `warlock/memory.py` ✓ done — shared state bus

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
    def print_log(self): ...           # pretty render of every write
    def print_run_summary(self): ...   # NEW — per-agent cost + timing + total
```

`print_log()` detects dict-of-strings (agent outputs) and renders them as readable markdown; other values pretty-print as JSON.

`print_run_summary()` reads `token_spend` and `timing` from memory and emits a one-line-per-actor table with input/output token cost (Haiku 4.5 pricing hardcoded for now) and a total cost line.

### `warlock/llm.py` ✓ done — provider contract

The language Warlock uses to talk to any LLM. Three types:

```python
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

All Anthropic-specific logic lives here. `cache_control: ephemeral` is set on the system prompt. `cache_read_input_tokens` is read off the response via `getattr(..., 0)`.

**Caveat:** the Anthropic SDK can return `None` (not `0`) for `cache_read_input_tokens`. Tracked as P1 — needs guarding in supervisor/orchestrator accumulators.

### `warlock/agent.py` ✓ done — base Agent, token tracking live

Provider-agnostic base class. Each `run()` reads `problem_statement`, calls `client.complete()` with the agent's `ROLE` as system prompt, writes its output to `agent_outputs[self.name]` and its usage to `token_spend[self.name]` in memory.

### `warlock/agents/data_engineer.py` ✓ done — first specialist agent

Production-grade ROLE: pipelines, ingestion, transformation, schemas. Cost-aware across storage/compute/egress/dev-time/on-call/lock-in. Anti-sycophancy rule, testing as test coverage not dashboards, GitOps for pipeline code. Holds the line on enforcement when analytics owns the metric definition.

### `warlock/agents/ml_engineer.py` ✓ done — machine learning specialist

ROLE: do-we-need-ML gate, baseline-before-complexity, evaluation-before-deployment, reproducibility, fairness and disparate-impact surfacing, pushback handling, 18-month maintainability question, monitoring as a pre-deployment requirement. Splits monitoring with MLOps: model-quality thresholds here, enforcement infra there.

### `warlock/agents/analytics.py` ✓ done — analytics + BI specialist

ROLE: analysis vs. confirmation, one-time vs. recurring, metric definition alignment before building, audience-tailoring, tool selection heuristic, segment-before-concluding, profile-before-you-conclude, context-beats-precision, trust-is-fragile, causality path, hand-off recognition. Owns the metric definition; hands enforcement to data engineering.

### `warlock/agents/devops_mlops.py` ✓ done — DevOps / MLOps specialist

ROLE: SLA/SLO/SLI, RPO/RTO, migration cutovers, ML-specific probes (champion-challenger, shadow mode, data pipeline failures), incident response priority order, rollout strategies, boring technology, error budgets, post-mortem anatomy, DR vs. incident distinction, alert fatigue as operational failure, deprecation discipline, security as scheduled incident.

### `warlock/agents/data_scientist.py` ✓ done — data science specialist

ROLE: predictive/causal/descriptive distinction, unit of analysis, data-generating process validation, baseline and leakage probes, experimentation discipline (pre-registration, power analysis, heterogeneity planning, researcher degrees of freedom), identification before estimation, uncertainty as the deliverable, statistical vs. business significance, fairness, motivated-analysis pushback, hands production system to ML engineer.

### `warlock/agents/software_dev.py` ✓ done — software engineering specialist

ROLE: interface-before-implementation, async/event-driven delivery guarantees (at-most-once/at-least-once/exactly-once + DLQ), boundary definition, backwards compatibility discipline, distributed-systems failure modes, contract testing at boundaries, database hazards (N+1, long transactions, pool exhaustion, migrations), implicit schema risk, named handoff partners.

### `warlock/orchestrator.py` ✓ done — decompose, route, time, supervise

```python
class Orchestrator:
    def __init__(self, memory, client: LLMClient, model: str, supervisor=None):
        ...

    def register(self, agent): ...
    def decompose(self, problem): ...   # LLM → JSON array [{domain, task}, ...]
    def run(self, problem):
        # writes problem_statement
        # decompose(); record timing["orchestrator"] + token_spend["orchestrator"]
        # for each item: route to registered agent, record timing[domain]
        # if supervisor: validate(domain, task, output), accumulate timing["supervisor"]
```

**Key concepts:**
- Supervisor is optional — Orchestrator runs without one if not passed
- `decompose()`'s defensive strip removes ```json ``` fences if the model emits them
- Empty decomposition (`[]`) is a silent no-op — Supervisor will handle in the consensus loop
- **Known issue P0:** the return value of `self._supervisor.validate()` is discarded — no retry happens yet. This is the next thing to fix.
- **Known issue P2:** `token_spend["orchestrator"] = {...}` overwrites instead of `+=`. Fine while `decompose()` runs once per `run()`, but will lose data once the retry loop calls it again.

### `warlock/supervisor.py` ✓ done — first version

```python
class Supervisor:
    def __init__(self, memory, client: LLMClient, model: str): ...

    def validate(self, agent_name: str, task: str, output: str) -> bool:
        # reads problem_statement
        # calls LLM with strict JSON-only ROLE prompt
        # writes validation_results[agent_name] = {accepted, reason}
        # accumulates token_spend["supervisor"] via +=
        # returns result["accepted"]
```

**ROLE highlights:** two-axis evaluation (ON-DOMAIN, QUALITY), JSON-only response (`{"accepted": bool, "reason": str}`), defensive code-fence strip on parse.

**Known issues:**
- **P1:** `cache_read_tokens` may be `None` from the Anthropic SDK; `+=` will TypeError. Needs a `(value or 0)` guard.
- **P3:** acceptance rate is non-deterministic across runs (saw 3/6 → 5/6 rejected with no code change). Need `temperature=0` on supervisor calls and tighter acceptance criteria.

### `main.py` ✓ done — wires the triangle (no consensus yet)

Registers all six agents, instantiates the Supervisor, wires it into the Orchestrator, runs a sample churn-prediction problem, then prints the full memory log and the run summary.

### `.gitignore` ✓ done

Ignores all `*.txt` audit dumps and the `traces/` directory so validation logs and run dumps never get committed.

### `warlock/trace_logger.py` ✓ done — validation event recorder

`TraceLogger` appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Each record captures `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, and `iteration`. Instantiated per run in `Orchestrator.run()` with a fresh `run_id` (UUID). This is the raw dataset for future fine-tuning of a cheaper supervisor model. Known gap: only iteration 0 is logged today — the blind retry's output is not yet recorded (fixed once the consensus loop lands).

---

## Recently completed (prior session)

- **P0 ✓** — `orchestrator.py` now captures `validate()` return value and retries the agent once on rejection.
- **P1 ✓** — `cache_read_tokens or 0` guard added in both `supervisor.py` and `orchestrator.py`.
- **P2 ✓** — Orchestrator token tracking now uses the `current_tokens` accumulation pattern instead of overwriting.
- **P3 ✓** — `temperature=0` threaded through `LLMClient.complete()` and `AnthropicClient.complete()`; supervisor calls with it explicitly.
- **Naming cleanup** — `token_spend` / `current_tokens` naming made consistent across both files.
- **Explicit accumulation pattern** — replaced implicit mutation-via-alias with explicit read → add → write in both orchestrator and supervisor.
- **`memory.patch()`** — new method added to `Memory` for writing nested keys without overwriting the parent dict.
- **`TraceLogger`** — new `warlock/trace_logger.py`. Appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Captures: `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, `iteration`. This is the raw dataset for future supervisor fine-tuning.
- **`CLAUDE.md`** — behavioral guidelines added (4 principles: Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution).
- **`EXAMPLES.md`** — annotated before/after examples for all four principles.

## What we are building next

### Consensus loop

Full retry loop replacing the current one-blind-retry in `orchestrator.py`:
- Cap at 3 iterations per agent
- Pass rejection reason back to agent on each retry so it can improve
- Log every iteration via `TraceLogger` (currently only iteration 0 is logged)
- After 3 failed iterations, tag output as `confidence: low` and continue

### Clarifying questions — deferred to Phase 5

Agents asking clarifying questions is valid professional behavior, but requires a user in the loop to answer them. Until Phase 5 (conversational loop), the supervisor correctly rejects this — there is no mechanism to resolve the questions. When Phase 5 ships, update supervisor ROLE acceptance criteria to explicitly allow clarifying questions.

### Escape valve

After 3 iterations without consensus, emit best-effort output tagged with a confidence score. Tag the run as `consensus=partial`.

### Parallel multi-agent run

Run independent domains concurrently once the retry loop is stable.

---

## Known edge cases (Phase 4)

- **Empty decomposition** — orchestrator returns `[]` silently when the problem doesn't match any domain. Will be handled by the consensus loop.
- **Out-of-domain problems** — no feedback to the user when nothing runs. Same fix.
- **Retry not logged** — `TraceLogger` is only called before the retry. The retried output is not recorded. Fixed in consensus loop.

---

## Project structure

```
warlock/
├── __init__.py
├── memory.py              ✓ done — shared state bus + print_log + print_run_summary
├── agent.py               ✓ done — base Agent, run(), token tracking
├── llm.py                 ✓ done — LLMClient Protocol, LLMResponse, LLMUsage
├── orchestrator.py        ✓ done — decompose, register, route, run, timing, supervisor hook, trace logging
├── supervisor.py          ✓ done — validate(), JSON-only ROLE, validation_results in memory
├── trace_logger.py        ✓ done — JSONL validation event recorder (traces/<date>/<run_id>.jsonl)
├── providers/
│   ├── __init__.py        ✓ done
│   └── anthropic.py       ✓ done — AnthropicClient, cache_control on system prompt
└── agents/
    ├── __init__.py        ✓ done
    ├── data_engineer.py   ✓ done
    ├── ml_engineer.py     ✓ done
    ├── analytics.py       ✓ done
    ├── devops_mlops.py    ✓ done
    ├── data_scientist.py  ✓ done
    └── software_dev.py    ✓ done
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor wired
.gitignore                  ✓ done — ignores *.txt and traces/
pyproject.toml
                            ← next: consensus loop — replace single blind retry with 3-iteration reason-passing loop
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
