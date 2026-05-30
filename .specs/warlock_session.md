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

**Drafted the curated eval suite and formalized the first domain-boundary contract.** This is Session 1 of the sequence laid out in `.specs/next-steps.md` (D6 of the eval plan).

1. **Sequenced the work.** Committed `.specs/next-steps.md`, which orders the two open tracks — the eval pipeline and the Phase 4 consensus loop — under a single guiding principle: **measure before you improve.** Build the eval logger first, capture a baseline of today's behavior, then prove the consensus loop by moving that baseline. The two tracks are coupled by measurement at three touch points (acceptance rate + iteration count, trace-logger completeness, and the eventual confidence-score fusion).
2. **Drafted `warlock/eval/cases.py`** — 23 `EvalCase` entries spanning routing width: 6 single-domain (`sd-*`), 14 two-to-three-domain (`md-*`), 3 broad (`bd-*`). Each has a minimal `expected_domains` set and a `notes` field giving per-domain inclusion *and* exclusion reasoning. The exclusion reasoning is deliberate — it makes the over-routing cases (which exercise the R / routing-precision metric) explicit. Ground truth is human-owned; pending the human's review/correction pass.
3. **Created `warlock/eval/agent_contracts.md`** — the settled-boundary source of truth. First entry resolves **data_scientist ↔ ml_engineer**: data_scientist owns the research cycle, ml_engineer owns the production cycle, and the handoff trigger is a production artifact. Training and evaluation always belong to data_scientist regardless of how specified the approach is.
4. **Refined `warlock/agents/ml_engineer.py`** — one ROLE edit clarifying that ml_engineer owns the *infrastructure that runs training jobs* (orchestration, compute provisioning, artifact storage), not the modeling research, keeping the agent prompt consistent with the new contract.

Uncommitted at session close: `warlock/agents/ml_engineer.py` (ROLE refinement) and the untracked `warlock/eval/` directory (`__init__.py`, `cases.py`, `agent_contracts.md`). `.specs/next-steps.md` was committed (`1916d00`).

The Phase 4 consensus loop remains open from prior sessions — sequenced as Session 4 in `next-steps.md`, after the logger and baseline. The active frontier is now eval **Session 2 — build the logger**.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note updated to reflect Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`, the curated suite in `warlock/eval/cases.py`, the session sequencing in `.specs/next-steps.md`, and the boundary contracts in `warlock/eval/agent_contracts.md`.

### `.specs/eval_ml_plan.md` ✓ done — evaluation system design

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
- **D6** — curated suite of 15–30 cases is the source of *complete* rows; spans routing width (~6 single-domain, ~12 two-to-three, ~4 broad). **Drafted this session as `warlock/eval/cases.py`.**
- **D7** — log *every* run; A and F always compute; only C and R go `null` when no case; explicit `has_case: bool` flag so null never silently coerces to 0.0.
- **D8** — `eval_runs/` gitignored; commit only `cases.py`; dataset regenerable / external.

**Roadmap:** Step 1 log → Step 2 label → Step 3 train logistic regression → Step 4 split + confusion matrix → Step 5 calibrate + abstain → Step 6 retraining loop.

### `.specs/next-steps.md` ✓ done — session sequencing for both open tracks (this session)

Orders the eval pipeline and the Phase 4 consensus loop into startable-cold sessions, under the principle **measure before you improve**. A quality-improvement mechanism built without a quality measurement is unfalsifiable, so the logger is built first and the consensus loop is proven by moving a captured baseline.

**The two tracks synchronize at three touch points:**
1. **Acceptance rate `A` + iteration count** — the eval row logs the run's iteration/retry count from day one (0-or-1 today) so the *same* logger captures the richer signal once the consensus loop lands, keeping baseline-vs-after apples-to-apples.
2. **Trace-logger completeness** — `TraceLogger` records only iteration 0 today; the consensus loop closes that gap by logging every iteration.
3. **Confidence score fusion** — once the eval *classifier* is trained (Step 3+), its `P(excellent/acceptable/poor)` replaces the hand-set `confidence: low` tag in the escape valve. This is where the two tracks merge.

**Ordered sequence:** S1 draft suite → S2 build logger → S3 capture baseline → S4 build consensus loop → S5 re-measure (prove the loop earned its token cost; a flat-quality / 3×-token result is a valid negative result) → S6+ label → train → calibrate → fuse.

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

### `warlock/agents/ml_engineer.py` ✓ done — machine learning specialist (refined this session)

ROLE: do-we-need-ML gate, baseline-before-complexity, evaluation-before-deployment, reproducibility, fairness and disparate-impact surfacing, pushback handling, 18-month maintainability question, monitoring as a pre-deployment requirement. Splits monitoring with MLOps: model-quality thresholds here, enforcement infra there. **Refined this session:** the ownership statement now reads that ml_engineer owns the *infrastructure that runs training jobs* (orchestration, compute provisioning, artifact storage), serving infrastructure, and monitoring — while problem formulation, feature-engineering strategy, and validation methodology belong upstream to data science. This keeps the prompt consistent with the data_scientist ↔ ml_engineer contract in `warlock/eval/agent_contracts.md`.

### `warlock/agents/analytics.py` ✓ done — analytics + BI specialist

ROLE: analysis vs. confirmation, one-time vs. recurring, metric definition alignment before building, audience-tailoring, tool selection heuristic, segment-before-concluding, profile-before-you-conclude, context-beats-precision, trust-is-fragile, causality path, hand-off recognition. Owns the metric definition; hands enforcement to data engineering.

### `warlock/agents/devops_mlops.py` ✓ done — DevOps / MLOps specialist

ROLE: SLA/SLO/SLI, RPO/RTO, migration cutovers, ML-specific probes (champion-challenger, shadow mode, data pipeline failures), incident response priority order, rollout strategies, boring technology, error budgets, post-mortem anatomy, DR vs. incident distinction, alert fatigue as operational failure, deprecation discipline, security as scheduled incident.

### `warlock/agents/data_scientist.py` ✓ done — data science specialist

ROLE: predictive/causal/descriptive distinction, unit of analysis, data-generating process validation, baseline and leakage probes, experimentation discipline (pre-registration, power analysis, heterogeneity planning, researcher degrees of freedom), identification before estimation, uncertainty as the deliverable, statistical vs. business significance, fairness, motivated-analysis pushback, hands production system to ML engineer.

### `warlock/agents/software_dev.py` ✓ done — software engineering specialist

ROLE: interface-before-implementation, async/event-driven delivery guarantees (at-most-once/at-least-once/exactly-once + DLQ), boundary definition, backwards compatibility discipline, distributed-systems failure modes, contract testing at boundaries, database hazards (N+1, long transactions, pool exhaustion, migrations), implicit schema risk, named handoff partners.

### `warlock/eval/agent_contracts.md` ✓ done — settled domain-boundary decisions (this session)

The source of truth when the orchestrator or supervisor needs to reason about who owns what. Each entry is a boundary that was *explicitly decided* — not inferred from code, not assumed from domain names — and a new entry is added whenever an eval case surfaces a non-obvious or initially-wrong domain split.

First entry — **data_scientist ↔ ml_engineer** (decided in case `md-11`):
- data_scientist owns the **research cycle**: problem formulation, experiment design, feature analysis, model training, evaluation and interpretation, "this works, here's why."
- ml_engineer owns the **production cycle**: production validation, packaging and registration, deployment and serving, monitoring (drift / performance / data quality), retraining pipelines.
- **Handoff trigger:** a production artifact (batch scoring job, serving endpoint, registered model). The moment the output is destined for production, ml_engineer takes over.
- **Key exclusions:** training a model is not ml_engineer unless the approach is fully specified and the research question is closed; feature-importance analysis is interpretation (data_scientist); operational retraining on a fixed schedule is production maintenance (ml_engineer + devops_mlops).
- **Edge cases:** "train and deploy" → split it on whether a research question is still open; experiment-tracking *tooling* is ml_engineer while the *experiments* are data_scientist.

### `warlock/eval/cases.py` ✓ done — curated eval suite (this session)

The human-owned ground truth the eval logger will measure routing against (D2, D6). Pending the human's review/correction pass on the domain sets.

```python
@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""

SINGLE_DOMAIN: list[EvalCase] = [...]   # sd-01 … sd-06  (6)
MULTI_DOMAIN:  list[EvalCase] = [...]   # md-01 … md-14  (14)
BROAD:         list[EvalCase] = [...]   # bd-01 … bd-03  (3)
ALL_CASES = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD          # 23 total
```

- **23 cases** spanning routing width — 6 single-domain, 14 two-to-three-domain, 3 broad (the broad cases route 4–6 domains).
- Each case's `notes` gives per-domain **inclusion and exclusion** reasoning. The exclusion reasoning is what makes the R (routing-precision / over-routing) metric measurable — every domain appears as *needed* in some cases and *explicitly not-needed* in others.
- Problems are written with the scope-narrowing language ("no downstream transformations", "no CI/CD pipeline", "model already trained and signed off") that forces the minimal-domain ground truth.
- Boundary-sensitive cases (`md-09`, `md-10`, `md-11`, `md-13`, `bd-01`) carry inline notes on *why* a domain was included or excluded, several of them exercising the data_scientist ↔ ml_engineer contract.

### `warlock/eval/__init__.py` ✓ done

Empty package file for the eval module.

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

Ignores all `*.txt` audit dumps, the `traces/` directory, and (D8) the `eval_runs/` dataset directory so raw agent outputs never get committed.

### `warlock/trace_logger.py` ✓ done — validation event recorder

`TraceLogger` appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Each record captures `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, and `iteration`. Instantiated per run in `Orchestrator.run()` with a fresh `run_id` (UUID). This is the raw dataset for future fine-tuning of a cheaper supervisor model. Known gap: only iteration 0 is logged today — the blind retry's output is not yet recorded (fixed once the consensus loop lands). Note: this is *per-task forensic trace*, distinct from the eval track's planned *per-run feature row* (`warlock/eval/run_logger.py`) — different grain, different purpose.

---

## What we are building next

### Eval Session 2 — build the logger (active frontier)

The curated suite (`cases.py`) is drafted; next is the logging code from `eval_ml_plan.md` Step 1, sequenced as Session 2 in `next-steps.md`. The logger is a **read-only observer** of memory — it never writes back to the bus.

**First — `uv add sentence-transformers`** (the one new dependency).

**Then build:**
```
warlock/eval/
  metrics.py      # coverage, routing_precision, acceptance_rate, output_fidelity
                  #   over real memory keys: task_decomposition, validation_results, agent_outputs
                  #   output_fidelity calls embed() (sentence-transformers all-MiniLM-L6-v2),
                  #     mean of per-output cosine sims vs. embed(problem) — NOT concatenated text
                  #   coverage/routing_precision return None when expected_domains is absent
  run_logger.py   # after a run: compute A,F always; C,R only if a case is given; set has_case;
                  #   capture the run's iteration/retry count (forward-compat, touch point 1);
                  #   append one JSON line to eval_runs/<date>.jsonl; label=null
```

- `metrics.py` reads the real memory keys. `coverage = |invoked ∩ needed| / |needed|`, `routing_precision = |invoked ∩ needed| / |invoked|` (both `None` when no case), `acceptance_rate` over `validation_results`, `output_fidelity` via the swappable `embed()` seam.
- `run_logger.py` is forward-compatible: it logs the iteration/retry count from day one (0-or-1 today) so the same logger captures the richer signal once the consensus loop lands.

**Verify gate (from `eval_ml_plan.md` / `next-steps.md` S2):** run on 2–3 problems →
- every row has in-range `[A, F]`;
- a **cased single-domain** problem routed correctly scores `C=R=1.0`, `has_case=true`;
- an **uncased** run gives `C=R=null`, `has_case=false`, with A/F populated and in range;
- raw outputs captured; `label=null`;
- a hand-check of one row's arithmetic matches.

After the logger: **Session 3 — capture the baseline** (run the full suite through today's orchestrator, record baseline means of A, F, and label distribution — the targets the consensus loop must later beat).

### Phase 4 consensus loop (Session 4 in next-steps.md — after baseline)

Not the immediate frontier, but next after the baseline. Full retry loop replacing the current one-blind-retry in `orchestrator.py`:
- Cap at 3 iterations per agent; pass the rejection **reason** back to the agent on each retry so it can improve.
- Log every iteration via `TraceLogger` (currently only iteration 0 is logged — touch point 2).
- After 3 failed iterations, tag output as `confidence: low`, `consensus=partial`, and continue (escape valve).
- Parallel multi-agent run once the retry loop is stable.
- Clarifying questions deferred to Phase 5 (needs a user in the loop).
- **Session 5 — re-measure:** re-run the suite, compare to the Session 3 baseline. Expect `A` to rise, `F`/labels to hold or improve, and token cost recorded alongside — a flat-quality / 3×-token result is a valid negative result, not a failure.

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
│   ├── ml_engineer.py     ✓ done — ROLE refined this session (training-infra ownership)
│   ├── analytics.py       ✓ done
│   ├── devops_mlops.py    ✓ done
│   ├── data_scientist.py  ✓ done
│   └── software_dev.py    ✓ done
└── eval/
    ├── __init__.py        ✓ done
    ├── cases.py           ✓ done — 23 EvalCase suite (6 sd / 14 md / 3 bd)
    ├── agent_contracts.md ✓ done — settled domain boundaries (ds ↔ mle)
    ├── metrics.py         ← next: coverage, routing_precision, acceptance_rate, output_fidelity
    └── run_logger.py      ← next: read-only per-run feature row → eval_runs/<date>.jsonl
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor wired
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
.specs/next-steps.md        ✓ done — session sequencing for eval + consensus tracks
                            ← next: uv add sentence-transformers, then build metrics.py + run_logger.py
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
