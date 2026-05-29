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

**Design only — no application code shipped, no new commits.** We designed the evaluation system end to end and wrote it to `.specs/eval_ml_plan.md`. The work started from a question — "how do I mathematically evaluate whether a run's process and output are correct?" — and went through several sharpening passes:

1. Started from a softmax-over-quality-classes idea, then named it honestly: it's a **heuristic scoring function**, not a trained classifier, until labels exist.
2. Designed the path to **turn the heuristic into real ML** — same softmax, but learned weights `W, b` via multinomial logistic regression once labeled runs accumulate.
3. Caught and fixed the **circularity** problem: C and R only measure *process conformance* (did routing match expectation), never quality. Reframed the feature set into three honest axes and required at least one output-grounded feature.
4. Settled eight decisions **D1–D8** (see the eval plan), including the two that were blocking "log every run": what to do with uncased runs (D7 — log everything, null only C/R, add `has_case` flag) and dataset storage (D8 — gitignore `eval_runs/`).

Uncommitted at session close: new `.specs/eval_ml_plan.md`, and `.gitignore` gained `eval_runs/` (the D8 guard, added before any logger code).

The Phase 4 consensus loop remains open from prior sessions — not abandoned, just not this session's focus. The active frontier is now eval **Step 1**.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note updated to reflect Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`.

### `.specs/eval_ml_plan.md` ✓ done — evaluation system design (this session)

The full step-by-step plan to evaluate Warlock runs and evolve the evaluator from heuristic to learned model. Not code yet — the agreed design Step 1 builds against.

**Feature vector** `x = [C, R, A, F] ∈ [0,1]⁴`, computed per run from memory + a per-problem eval case:
- **C — coverage (routing recall)** = `|invoked ∩ needed| / |needed|` — did we invoke the domains this problem needs? (process-conformance)
- **R — routing precision** = `|invoked ∩ needed| / |invoked|` — did we avoid invoking domains it doesn't need? Penalizes over-routing. (process-conformance)
- **A — acceptance rate** = fraction of `validation_results[*].accepted == true`. (self-report — suspect; the learned `W` audits whether it carries signal)
- **F — output relevance** = mean cosine similarity between `embed(problem)` and `embed(each agent output)`, via `sentence-transformers` (`all-MiniLM-L6-v2`). Mean of per-output sims, NOT concatenated text (length-bias). (output-relevance — the load-bearing axis)

**Decisions D1–D8 (all settled):**
- **D1** — F = sentence-transformers cosine; keyword recall rejected (gameable + length bias); F computed Day-1 behind a swappable `embed()` seam.
- **D2** — `expected_domains` = minimal sufficient set per problem (may be one); human-owned ground truth with per-domain reasoning; never derived from the routing logic.
- **D3** — labels from LLM-judge (bulk) + human-verified sample; judge reads raw output only, never the metrics.
- **D4** — label vocabulary `{excellent, acceptable, poor}`.
- **D5** — three-axis taxonomy (process-conformance / self-report / output-relevance) + label `y`; the feature set must contain ≥1 output-grounded feature.
- **D6** — curated suite of 15–30 cases is the source of *complete* rows; spans routing width (~6 single-domain, ~12 two-to-three, ~4 broad).
- **D7** — log *every* run; A and F always compute; only C and R go `null` when no case; explicit `has_case: bool` flag so null never silently coerces to 0.0.
- **D8** — `eval_runs/` gitignored; commit only `cases.py`; dataset regenerable / external.

**Roadmap:** Step 1 log → Step 2 label → Step 3 train logistic regression → Step 4 split + confusion matrix → Step 5 calibrate + abstain → Step 6 retraining loop.

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
- A `TraceLogger` is created per run with a fresh UUID `run_id`; logs every validation event
- **Current behavior:** on rejection the agent is retried once (blind retry — P0 fixed). The full reason-passing 3-iteration loop is not yet built.

### `warlock/supervisor.py` ✓ done — first version

```python
class Supervisor:
    def __init__(self, memory, client: LLMClient, model: str): ...

    def validate(self, agent_name: str, task: str, output: str) -> bool:
        # reads problem_statement
        # calls LLM with strict JSON-only ROLE prompt, temperature=0
        # writes validation_results[agent_name] = {accepted, reason}
        # accumulates token_spend["supervisor"] via the current_tokens pattern
        # returns result["accepted"]
```

**ROLE highlights:** two-axis evaluation (ON-DOMAIN, QUALITY), JSON-only response (`{"accepted": bool, "reason": str}`), defensive code-fence strip on parse. P1 (`cache_read_tokens or 0` guard) and P3 (`temperature=0`) both fixed.

### `main.py` ✓ done — wires the triangle (no consensus yet)

Registers all six agents, instantiates the Supervisor, wires it into the Orchestrator, runs a sample churn-prediction problem, then prints the full memory log and the run summary.

### `.gitignore` ✓ done

Ignores all `*.txt` audit dumps, the `traces/` directory, and (new this session, D8) the `eval_runs/` dataset directory so raw agent outputs never get committed.

### `warlock/trace_logger.py` ✓ done — validation event recorder

`TraceLogger` appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Each record captures `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, and `iteration`. Instantiated per run in `Orchestrator.run()` with a fresh `run_id` (UUID). This is the raw dataset for future fine-tuning of a cheaper supervisor model. Known gap: only iteration 0 is logged today — the blind retry's output is not yet recorded (fixed once the consensus loop lands). Note: this is *per-task forensic trace*, distinct from the eval track's planned *per-run feature row* (`warlock/eval/run_logger.py`) — different grain, different purpose.

---

## What we are building next

### Eval Step 1 — log every run (active frontier)

We left off ready to build the evaluation logging pipeline. Two ways in; we agreed to draft the suite first so the human-owned ground truth can be corrected while the logger is built around it.

**Immediate next action — draft the curated eval suite** (D6): 15–30 `EvalCase` entries spanning routing width, each with `id`, `problem`, minimal `expected_domains`, and per-domain reasoning comments (including *why* each excluded domain is excluded). Hand to the user for review/correction — the domain sets are ground truth and must not be decreed by the routing logic.

**Then build Step 1 code:**
```
warlock/eval/
  metrics.py      # coverage, routing_precision, acceptance_rate, output_fidelity
                  #   over real memory keys: task_decomposition, validation_results, agent_outputs
                  #   output_fidelity calls embed() (sentence-transformers all-MiniLM-L6-v2)
                  #   coverage/routing_precision return None when expected_domains is absent
  run_logger.py   # after a run: compute A,F always; C,R only if a case is given; set has_case;
                  #   append one JSON line to eval_runs/<date>.jsonl; label=null
  cases.py        # the reviewed EvalCase suite (the only eval file committed to git)
```
- `uv add sentence-transformers` is the one new dependency.
- The logger is a **read-only observer** of memory — it never writes back to the bus.
- **Verify gate:** run on 2–3 problems → every row has in-range `[A,F]`; a cased single-domain problem routed correctly scores `C=R=1.0` with `has_case=true`; an uncased run gives `C=R=null, has_case=false` with A/F populated; raw outputs captured; `label=null`.

### Phase 4 consensus loop (still open, from prior sessions)

Not this session's focus but not abandoned. Full retry loop replacing the current one-blind-retry in `orchestrator.py`:
- Cap at 3 iterations per agent; pass the rejection **reason** back to the agent on each retry so it can improve.
- Log every iteration via `TraceLogger` (currently only iteration 0 is logged).
- After 3 failed iterations, tag output as `confidence: low` and continue (escape valve, `consensus=partial`).
- Parallel multi-agent run once the retry loop is stable.
- Clarifying questions deferred to Phase 5 (needs a user in the loop).

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
├── agents/
│   ├── __init__.py        ✓ done
│   ├── data_engineer.py   ✓ done
│   ├── ml_engineer.py     ✓ done
│   ├── analytics.py       ✓ done
│   ├── devops_mlops.py    ✓ done
│   ├── data_scientist.py  ✓ done
│   └── software_dev.py    ✓ done
└── eval/                  ← next: Step 1 logging (metrics.py, run_logger.py, cases.py)
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor wired
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
                            ← next: draft curated eval suite, then build warlock/eval/ Step 1
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
