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

**Built the eval logger — Session 2 of `.specs/next-steps.md` is done.** The curated suite drafted last session now has the read-only measurement code behind it. Warlock can now log a feature row for every run.

1. **Built `warlock/eval/metrics.py`** — the four metric functions (`coverage`, `routing_precision`, `acceptance_rate`, `output_fidelity`) computed over real memory keys (`task_decomposition`, `validation_results`, `agent_outputs`). F runs through a lazy `_embedding()` seam loading `sentence-transformers` `all-MiniLM-L6-v2`. `coverage`/`routing_precision` return `None` when `expected_domains` is absent.
2. **Built `warlock/eval/run_logger.py`** — `log_run(memory, case=None, base_dir="eval_runs")`, a read-only observer that computes A/F always, C/R only when a case is given, sets `has_case`, captures an `iteration` count (hardcoded `0` today via `_max_iteration`, forward-compat for the consensus loop), embeds the raw outputs, sets `label=None`, and appends one JSON line to `eval_runs/<date>.jsonl`.
3. **Wired `log_run(m)` into `main.py`** — one line after `orchestrator.run(...)`, before the log/summary prints.
4. **Added dependencies** — `numpy>=2.4.6` and `sentence-transformers>=5.5.1` in `pyproject.toml` (and `uv.lock`).
5. **Recorded a future touch point in `.specs/next-steps.md`** — the agent clarification loop: F/A must be computed on final output only, and `iteration` must reflect real clarification-round depth, once that loop lands.
6. **Reworked the case suite (23 → 24)** — rewrote `sd-05` to a pure-ops deploy case and split the old dbt-CI/CD problem into the new two-domain `md-15`, surfacing the **third boundary contract** (`data_engineer ↔ devops_mlops`) in `agent_contracts.md`.
7. **Switched `main.py` to a cased driver** — runs `sd-05` via `orchestrator.run(case.problem)` + `log_run(m, case=case)`, beginning Session 3 baseline capture / the Step-1 verify gate.

**F definition (settled):** `output_fidelity` measures each agent's **assigned task** (`task_decomposition[i].task`) vs that agent's output, averaged across agents — "did each agent answer the task it was given?" This is a sharper per-agent relevance signal than the whole-problem embedding, which would blur across agents. D1 in `eval_ml_plan.md` was updated this session to make assigned-task-vs-output the canonical definition; the shipped code already matches.

Uncommitted at session close: `main.py`, `pyproject.toml`, `uv.lock`, `.specs/next-steps.md` (modified), and the untracked `warlock/eval/metrics.py` + `warlock/eval/run_logger.py`.

The active frontier is now eval **Session 3 — capture the baseline** (which doubles as the Step-1 verify gate). The Phase 4 consensus loop remains open, sequenced as Session 4, after the baseline.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note updated to reflect Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`, the curated suite in `warlock/eval/cases.py`, the now-built logger (`metrics.py`, `run_logger.py`), the session sequencing in `.specs/next-steps.md`, and the boundary contracts in `warlock/eval/agent_contracts.md`.

### `.specs/eval_ml_plan.md` ✓ done — evaluation system design

The full step-by-step plan to evaluate Warlock runs and evolve the evaluator from heuristic to learned model. Not code yet — the agreed design Step 1 builds against.

**Feature vector** `x = [C, R, A, F] ∈ [0,1]⁴`, computed per run from memory + a per-problem eval case:
- **C — coverage (routing recall)** = `|invoked ∩ needed| / |needed|` — did we invoke the domains this problem needs? (process-conformance)
- **R — routing precision** = `|invoked ∩ needed| / |invoked|` — did we avoid invoking domains it doesn't need? Penalizes over-routing. (process-conformance)
- **A — acceptance rate** = fraction of `validation_results[*].accepted == true`. (self-report — suspect; the learned `W` audits whether it carries signal)
- **F — output relevance** = mean cosine similarity via `sentence-transformers` (`all-MiniLM-L6-v2`) between each agent's **assigned task** (`task_decomposition[i].task`) and that agent's output, averaged across agents.

**Decisions D1–D8 (all settled):**
- **D1** — F = sentence-transformers cosine; keyword recall rejected (gameable + length bias); F computed Day-1 behind a swappable embedding seam. F embeds each agent's **assigned task** vs its output (sharper per-agent signal than the whole problem).
- **D2** — `expected_domains` = minimal sufficient set per problem (may be one); human-owned ground truth with per-domain reasoning; never derived from the routing logic.
- **D3** — labels from LLM-judge (bulk) + human-verified sample; judge reads raw output only, never the metrics.
- **D4** — label vocabulary `{excellent, acceptable, poor}`.
- **D5** — three-axis taxonomy (process-conformance / self-report / output-relevance) + label `y`; the feature set must contain ≥1 output-grounded feature.
- **D6** — curated suite of 15–30 cases is the source of *complete* rows; spans routing width. **Drafted as `warlock/eval/cases.py`.**
- **D7** — log *every* run; A and F always compute; only C and R go `null` when no case; explicit `has_case: bool` flag so null never silently coerces to 0.0.
- **D8** — `eval_runs/` gitignored; commit only `cases.py`; dataset regenerable / external.

**Roadmap:** Step 1 log → Step 2 label → Step 3 train logistic regression → Step 4 split + confusion matrix → Step 5 calibrate + abstain → Step 6 retraining loop.

### `.specs/next-steps.md` ✓ done — session sequencing for both open tracks

Orders the eval pipeline and the Phase 4 consensus loop into startable-cold sessions, under the principle **measure before you improve**. A quality-improvement mechanism built without a quality measurement is unfalsifiable, so the logger is built first and the consensus loop is proven by moving a captured baseline.

**The two tracks synchronize at three touch points:**
1. **Acceptance rate `A` + iteration count** — the eval row logs the run's iteration/retry count from day one (0-or-1 today) so the *same* logger captures the richer signal once the consensus loop lands.
2. **Trace-logger completeness** — `TraceLogger` records only iteration 0 today; the consensus loop closes that gap by logging every iteration.
3. **Confidence score fusion** — once the eval *classifier* is trained (Step 3+), its `P(excellent/acceptable/poor)` replaces the hand-set `confidence: low` tag in the escape valve. This is where the two tracks merge.

**Ordered sequence:** S1 draft suite → S2 build logger → S3 capture baseline → S4 build consensus loop → S5 re-measure → S6+ label → train → calibrate → fuse. **S1 and S2 are now done; S3 is the active frontier.** This session also added an open note on the **agent clarification loop**: when it lands, F and A must be computed on the final output only (not intermediate question rounds), and `iteration` must reflect real clarification-round depth.

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
    def print_run_summary(self): ...   # per-agent cost + timing + total
```

`print_log()` detects dict-of-strings (agent outputs) and renders them as readable markdown; other values pretty-print as JSON. `print_run_summary()` reads `token_spend` and `timing` from memory and emits a one-line-per-actor table with input/output token cost (Haiku 4.5 pricing hardcoded for now) and a total cost line.

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

**Caveat:** the Anthropic SDK can return `None` (not `0`) for `cache_read_input_tokens`. Guarded with `or 0` in supervisor/orchestrator accumulators (P1 fixed).

### `warlock/agent.py` ✓ done — base Agent, token tracking live

Provider-agnostic base class. Each `run()` reads `problem_statement`, calls `client.complete()` with the agent's `ROLE` as system prompt, writes its output to `agent_outputs[self.name]` and its usage to `token_spend[self.name]` in memory.

### `warlock/agents/data_engineer.py` ✓ done — first specialist agent

Production-grade ROLE: pipelines, ingestion, transformation, schemas. Cost-aware across storage/compute/egress/dev-time/on-call/lock-in. Anti-sycophancy rule, testing as test coverage not dashboards, GitOps for pipeline code. Holds the line on enforcement when analytics owns the metric definition.

### `warlock/agents/ml_engineer.py` ✓ done — machine learning specialist

ROLE: do-we-need-ML gate, baseline-before-complexity, evaluation-before-deployment, reproducibility, fairness and disparate-impact surfacing, pushback handling, 18-month maintainability question, monitoring as a pre-deployment requirement. Splits monitoring with MLOps: model-quality thresholds here, enforcement infra there. The ownership statement reads that ml_engineer owns the *infrastructure that runs training jobs* (orchestration, compute provisioning, artifact storage), serving infrastructure, and monitoring — while problem formulation, feature-engineering strategy, and validation methodology belong upstream to data science. Consistent with the data_scientist ↔ ml_engineer contract in `warlock/eval/agent_contracts.md`.

### `warlock/agents/analytics.py` ✓ done — analytics + BI specialist

ROLE: analysis vs. confirmation, one-time vs. recurring, metric definition alignment before building, audience-tailoring, tool selection heuristic, segment-before-concluding, profile-before-you-conclude, context-beats-precision, trust-is-fragile, causality path, hand-off recognition. Owns the metric definition; hands enforcement to data engineering.

### `warlock/agents/devops_mlops.py` ✓ done — DevOps / MLOps specialist

ROLE: SLA/SLO/SLI, RPO/RTO, migration cutovers, ML-specific probes (champion-challenger, shadow mode, data pipeline failures), incident response priority order, rollout strategies, boring technology, error budgets, post-mortem anatomy, DR vs. incident distinction, alert fatigue as operational failure, deprecation discipline, security as scheduled incident.

### `warlock/agents/data_scientist.py` ✓ done — data science specialist

ROLE: predictive/causal/descriptive distinction, unit of analysis, data-generating process validation, baseline and leakage probes, experimentation discipline (pre-registration, power analysis, heterogeneity planning, researcher degrees of freedom), identification before estimation, uncertainty as the deliverable, statistical vs. business significance, fairness, motivated-analysis pushback, hands production system to ML engineer.

### `warlock/agents/software_dev.py` ✓ done — software engineering specialist

ROLE: interface-before-implementation, async/event-driven delivery guarantees (at-most-once/at-least-once/exactly-once + DLQ), boundary definition, backwards compatibility discipline, distributed-systems failure modes, contract testing at boundaries, database hazards (N+1, long transactions, pool exhaustion, migrations), implicit schema risk, named handoff partners.

### `warlock/eval/agent_contracts.md` ✓ done — settled domain-boundary decisions

The source of truth when the orchestrator or supervisor needs to reason about who owns what. Each entry is a boundary that was *explicitly decided* — not inferred from code, not assumed from domain names — and a new entry is added whenever an eval case surfaces a non-obvious or initially-wrong domain split.

First entry — **data_scientist ↔ ml_engineer** (decided in case `md-11`):
- data_scientist owns the **research cycle**: problem formulation, experiment design, feature analysis, model training, evaluation and interpretation, "this works, here's why."
- ml_engineer owns the **production cycle**: production validation, packaging and registration, deployment and serving, monitoring (drift / performance / data quality), retraining pipelines.
- **Handoff trigger:** a production artifact (batch scoring job, serving endpoint, registered model).
- Training and evaluation always belong to data_scientist regardless of how specified the approach is.

Second entry — **ml_engineer ↔ devops_mlops** (decided in `bd-01`, `bd-03`): the seam is model vs. infrastructure. ml_engineer owns *model* monitoring (drift, model performance, data quality); devops_mlops owns *infra* monitoring (latency, error rate, resource use). Handoff trigger: what the metric is *about* — the model's predictions, or the service it runs on.

Third entry — **data_engineer ↔ devops_mlops** (decided in `md-15`): the seam is workflow files vs. project config. devops_mlops owns the CI/CD workflow (GitHub Actions YAML, deployment scripts, secrets/env wiring); data_engineer owns dbt project readiness (`profiles.yml` targets, `dbt_project.yml`, state-artifact logic, schema validation). Handoff trigger: who needs domain knowledge — a devops engineer writes the Actions YAML without knowing dbt internals; a data engineer owns whether the dbt project is structured to support those workflows. Note: "no new dbt models" does **not** exclude data_engineer — project structure and CI/CD readiness are separate from model authoring.

### `warlock/eval/cases.py` ✓ done — curated eval suite

The human-owned ground truth the eval logger measures routing against (D2, D6). Pending the human's review/correction pass on the domain sets.

```python
@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""

SINGLE_DOMAIN: list[EvalCase] = [...]   # sd-01 … sd-06  (6)
MULTI_DOMAIN:  list[EvalCase] = [...]   # md-01 … md-15  (15)
BROAD:         list[EvalCase] = [...]   # bd-01 … bd-03  (3)
ALL_CASES = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD          # 24 total
```

- **24 cases** spanning routing width — 6 single-domain, 15 two-to-three-domain, 3 broad (the broad cases route 4–6 domains).
- Each case's `notes` gives per-domain **inclusion and exclusion** reasoning — what makes the R (routing-precision / over-routing) metric measurable.
- Problems use scope-narrowing language ("no downstream transformations", "no CI/CD pipeline", "model already trained and signed off") to force the minimal-domain ground truth.
- Boundary-sensitive cases (`md-09`, `md-10`, `md-11`, `md-13`, `md-15`, `bd-01`) carry inline notes on *why* a domain was included or excluded.
- This session `sd-05` was rewritten to a pure-ops case (FastAPI → Docker/ECR/ECS deploy, app code already exists → single-domain `devops_mlops`); the old dbt-CI/CD problem became the new two-domain `md-15` (`devops_mlops` + `data_engineer`), which surfaced the third boundary contract below.

### `warlock/eval/__init__.py` ✓ done

Empty package file for the eval module.

### `warlock/eval/metrics.py` ✓ done — the four metric functions (this session)

Pure functions over real memory keys, plus the embedding seam. Read-only — no writes to the bus.

```python
def coverage(task_decomposition, expected_domains) -> float | None
    # |invoked ∩ needed| / |needed|; None when no case

def routing_precision(task_decomposition, expected_domains) -> float | None
    # |invoked ∩ needed| / |invoked|; None when no case or no invoked domains

def acceptance_rate(validation_results) -> float | None
    # fraction of accepted verdicts; None when empty

def output_fidelity(task_decomposition, agent_outputs) -> float | None
    # mean cosine( embed(task_i), embed(agent_output[domain_i]) ); None when no scorable outputs
```

- `_embedding(text)` lazily instantiates a module-level `SentenceTransformer("all-MiniLM-L6-v2")` and encodes; cosine computed with `numpy` `dot` / `norm`.
- `invoked` is the set of `task["domain"]` across `task_decomposition`; `needed` is `set(expected_domains)`.
- **F (per D1):** `output_fidelity` embeds each agent's **assigned task** vs its output and averages — the canonical definition. Not the whole problem vs each output.

### `warlock/eval/run_logger.py` ✓ done — read-only per-run feature row (this session)

```python
def log_run(memory, case: EvalCase | None = None, base_dir: str = "eval_runs"):
    # reads task_decomposition, agent_outputs, validation_results, problem_statement
    # has_case = case is not None;  expected_domains = case.expected_domains if has_case else None
    # row = { run_id (uuid), timestamp (utc iso), problem,
    #         Coverage, Routing, Acceptance, Fidelity,
    #         has_case, case_id, iteration,
    #         task_decomposition, raw_outputs, validation_results, label=None }
    # appends one JSON line to eval_runs/<date>.jsonl  (dir auto-created)
    # returns row
```

- Computes A/F always; C/R only when a case is given (else `None`). `has_case` flag means `None` never silently coerces to `0.0` (D7).
- `_max_iteration(validation_results)` returns `0` today (every agent runs at most once) — a forward-compat seam that will reflect real retry depth once the consensus loop lands (touch point 1).
- `label=None` — rows are unlabeled until eval Step 2.
- `eval_runs/` is gitignored (D8).

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

### `warlock/supervisor.py` ✓ done

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

### `warlock/trace_logger.py` ✓ done — validation event recorder

`TraceLogger` appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Each record captures `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, and `iteration`. Instantiated per run in `Orchestrator.run()` with a fresh `run_id` (UUID). The raw dataset for future fine-tuning of a cheaper supervisor model. Known gap: only iteration 0 is logged today — the blind retry's output is not yet recorded (fixed once the consensus loop lands). Distinct from the eval track's *per-run feature row* (`warlock/eval/run_logger.py`) — different grain, different purpose.

### `main.py` ✓ done — wires the triangle (no consensus yet)

Registers all six agents, instantiates the Supervisor, wires it into the Orchestrator. This session the driver switched from the free-text churn problem (now commented out, with a bare `log_run(m)`) to a **cased eval run**: it picks `sd-05` from `SINGLE_DOMAIN`, runs `orchestrator.run(case.problem)`, then **`log_run(m, case=case)`** — the first cased row, and the start of Session 3 baseline capture / the Step-1 verify gate (a correctly-routed single-domain case should score `C=R=1.0`, `has_case=true`). Then prints the full memory log and the run summary.

### `.gitignore` ✓ done

Ignores all `*.txt` audit dumps, the `traces/` directory, and (D8) the `eval_runs/` dataset directory so raw agent outputs never get committed.

---

## What we are building next

### Eval Session 3 — capture the baseline (active frontier)

The logger is built and wired, F is settled (assigned-task vs output per agent — D1 and code agree), and `main.py` already runs one cased single-domain smoke test (`sd-05`). Next: run the full 24-case suite through today's orchestrator and record the baseline. This **doubles as the Step-1 verify gate** from `eval_ml_plan.md` / `next-steps.md`.

**Capture the baseline:**
- Run each `EvalCase` in `cases.py` through `orchestrator.run(case.problem)`, calling `log_run(m, case=case)` per run.
- Record baseline **means of A and F** and the **label distribution** (labels can be process-only / null at this stage — A and F are enough to start).
- These are the targets the consensus loop (Session 4) must later beat.

**Verify gate checks (from `next-steps.md` S2):**
- every row has in-range `[A, F]`;
- a **cased single-domain** problem routed correctly scores `C=R=1.0`, `has_case=true`;
- an **uncased** run gives `C=R=null`, `has_case=false`, with A/F populated and in range;
- raw outputs captured; `label=null`;
- a hand-check of one row's arithmetic matches.

### Phase 4 consensus loop (Session 4 — after baseline)

Full retry loop replacing the current one-blind-retry in `orchestrator.py`:
- Cap at 3 iterations per agent; pass the rejection **reason** back to the agent on each retry.
- Log every iteration via `TraceLogger` (currently only iteration 0 — touch point 2). Update `_max_iteration` in `run_logger.py` to reflect real retry depth (touch point 1).
- After 3 failed iterations, tag output `confidence: low`, `consensus=partial`, continue (escape valve).
- Parallel multi-agent run once the retry loop is stable.
- Clarifying questions deferred to Phase 5 (needs a user in the loop).
- **Session 5 — re-measure:** re-run the suite, compare to the Session 3 baseline. A flat-quality / 3×-token result is a valid negative result.

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
└── eval/
    ├── __init__.py        ✓ done
    ├── cases.py           ✓ done — 24 EvalCase suite (6 sd / 15 md / 3 bd)
    ├── agent_contracts.md ✓ done — settled domain boundaries (ds ↔ mle, mle ↔ devops, de ↔ devops)
    ├── metrics.py         ✓ done — coverage, routing_precision, acceptance_rate, output_fidelity
    └── run_logger.py      ✓ done — read-only per-run feature row → eval_runs/<date>.jsonl
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor + log_run(m) wired
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml              ✓ done — + numpy, sentence-transformers
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
.specs/next-steps.md        ✓ done — session sequencing for eval + consensus tracks
                            ← next: capture the baseline (Session 3)
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
