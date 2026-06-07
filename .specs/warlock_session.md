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

**Captured the prompt-fix re-baseline control (Session 3.5, step 1 — done) and built the first per-deliverable routing metric + gold target.** The eval reframe (measure → train the router) said the cheapest, highest-leverage move is to stop the orchestrator routing *blind*. This session did that and measured it honestly.

1. **Built `assignment_accuracy`** (`metrics.py`) — a per-deliverable task→domain match: for each gold deliverable, find the router task that mentions it (by a chosen `match` keyword) and check it landed in the gold domain. This is the metric `routing_precision` could not be — it sees *which* deliverable went to *which* domain, not just the invoked set.
2. **Added `gold_decomposition` to `EvalCase`** (`cases.py`) and authored it for **bd-01** — 7 deliverables as `{deliverable, domain, match}`. On the original blind baseline bd-01 scored `Assignment = 0.857` (drift monitoring misrouted to devops_mlops) while `Coverage = Routing = 1.0` — the exact blindness the reframe predicted. Wired `assignment_accuracy` into `run_logger.py` as the `Assignment` column.
3. **Fixed the orchestrator prompt** (`orchestrator.py`) — loaded a six-domain ownership charter + the four `agent_contracts.md` boundary rules into `decompose`'s system prompt, and set `temperature=0`. After the fix bd-01's `Assignment` rose **0.857 → 1.0** (drift now → ml_engineer).
4. **Swept all 24 cases (routing-only) and recorded the re-baseline** → `eval_runs/2026-06-07.jsonl` (via `log_run`; `Acceptance`/`Fidelity` are `null` because no agents ran). **Delta vs `2026-06-04`: ~15 cases improved on `Routing`, 8 flat, 1 stable regression (md-12).**
5. **Tried and reverted a precision-tightening prompt line.** A "scope discipline" line (don't route activities mentioned only as background) did **not** heal the targets (md-03/md-12 unchanged) and **broke md-15** (a `verified` case) by dropping its dbt work. Reverted to the rules-only prompt — the cleaner control.

**Key findings:**
- **The prompt fix is a large, real win** — loading the boundary rules lifted routing precision on ~15/24 cases (sd-02 0.33→1.0, md-01/md-14 0.5→1.0, md-08 0.6→1.0 are well outside the noise floor).
- **md-12 is the one stable regression** — "build an internal tool, no CI/CD asked" still makes the model invent a devops_mlops CI/CD task + a data_engineer SQL task. Prompting could not fix it (case-specific rules would be teaching-to-the-test). It is now the prime `gold_decomposition` target and the empirical case for the fine-tune.
- **`temperature=0` decompositions are not reproducible at the ±1-task level.** md-03 flipped between `R=0.5` (regressed) and `R=0.67` (flat) across identical runs. So single-sample per-case deltas of ~±0.17 are inside the noise floor; trustworthy deltas (especially as a training reward) need **N samples per case**. This answers `training_eval_plan.md` §5.4 empirically.

Uncommitted at session close: modified `warlock/eval/cases.py`, `warlock/eval/metrics.py`, `warlock/eval/run_logger.py`, `warlock/orchestrator.py`. (`eval_runs/2026-06-07.jsonl` is gitignored — D8.)

The active frontier is now **eval Session 3.5 item 2** — extend `gold_decomposition` to the remaining discriminating cases (md-12, bd-02, bd-03, md-13) so `assignment_accuracy` covers them — plus the methodological task of **N-sampling the baseline** to clear the `temperature=0` noise. The Phase 4 consensus loop (Session 4) remains open and independent.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note reflects Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`, the curated suite in `warlock/eval/cases.py` (now with a `verified` flag and bd-01 `gold_decomposition`), the built logger (`metrics.py` — now incl. `assignment_accuracy` — `run_logger.py`), the **captured baselines** (`eval_runs/2026-06-04.jsonl` blind, `eval_runs/2026-06-07.jsonl` prompt-fix), the review docs (`EVAL_REFERENCE.md`, `suite_notes.md`), the **measure→train reframe** (`warlock/eval/training_eval_plan.md`), the **prompt-fix re-baseline control** (charter + boundary rules + `temperature=0` in `decompose`), the session sequencing in `.specs/next-steps.md`, and the boundary contracts in `warlock/eval/agent_contracts.md`.

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

**Roadmap:** Step 1 log → Step 2 label → Step 3 train logistic regression → Step 4 split + confusion matrix → Step 5 calibrate + abstain → Step 6 retraining loop. *(Reframe note: this classifier is now recast as the **reward model**, distinct from the router task-LLM — see `training_eval_plan.md` §8.)*

### `.specs/next-steps.md` ✓ done — session sequencing for both open tracks

Orders the eval pipeline and the Phase 4 consensus loop into startable-cold sessions, under the principle **measure before you improve**. Sessions 1–3 are done (suite drafted + reviewed, logger built, baseline captured). **Session 3.5 (the measure→train reframe) item 1 is now done** — the prompt-fix re-baseline control (boundary rules + `temperature=0` in `decompose`) is captured in `eval_runs/2026-06-07.jsonl`. Remaining 3.5 items: extend `gold_decomposition`, scope-aware `acceptance_rate`, under-routing cases. The three eval↔consensus touch points (A + iteration count, trace-logger completeness, confidence-score fusion) and the open note on the agent clarification loop (F/A computed on final output only; `iteration` reflects real clarification-round depth) are retained.

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
        temperature: float = 1.0,
    ) -> LLMResponse: ...
```

**Key concepts:**
- `LLMClient` is a `Protocol` — any class with a matching `complete()` signature satisfies it, no inheritance required
- `system` is a plain string — the adapter decides how to format it for its provider
- `model` travels through `complete()` so one client instance can serve agents using different models
- `temperature` defaults to `1.0`; `Supervisor.validate` and (this session) `Orchestrator.decompose` pass `temperature=0`
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

Third entry — **data_engineer ↔ devops_mlops** (decided in `md-15`): the seam is workflow files vs. project config. devops_mlops owns the CI/CD workflow (GitHub Actions YAML, deployment scripts, secrets/env wiring); data_engineer owns dbt project readiness (`profiles.yml` targets, `dbt_project.yml`, state-artifact logic, schema validation). Handoff trigger: who needs domain knowledge — a devops engineer writes the Actions YAML without knowing dbt internals; a data engineer owns whether the dbt project is structured to support those workflows.

> **Baseline observation:** on the original *blind-prompt* baseline the orchestrator *failed* the ml_engineer ↔ devops_mlops boundary in all three broad cases (drift monitoring → devops_mlops) and the data_scientist ↔ ml_engineer boundary in bd-02/bd-03 (training → ml_engineer). `routing_precision` saw neither (the misrouted domain is still inside the expected set); the `assignment_accuracy` metric (now built) does. **After loading these boundary rules into `Orchestrator.decompose` (+ `temperature=0`), bd-01 routes drift → ml_engineer correctly (`Assignment` 0.86→1.0)** — see `eval_runs/2026-06-07.jsonl`. The bd-02/bd-03 training boundary is not yet confirmed fixed (no gold authored there yet).

### `warlock/eval/cases.py` ✓ done — curated eval suite (+ gold_decomposition this session)

The human-owned ground truth the eval logger measures routing against (D2, D6). 20 of 24 cases are `verified=True` (md-15, bd-01, bd-02, bd-03 remain `False`, pending confirmation before they become training gold). **This session** added the `gold_decomposition` field (the per-example router target the reframe requires) and authored it for **bd-01**.

```python
@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""
    verified: bool = False
    gold_decomposition: list[dict] = field(default_factory=list)   # added this session

SINGLE_DOMAIN: list[EvalCase] = [...]   # sd-01 … sd-06  (6)
MULTI_DOMAIN:  list[EvalCase] = [...]   # md-01 … md-15  (15, md-13 precedes md-15)
BROAD_DOMAIN:  list[EvalCase] = [...]   # bd-01 … bd-03  (3)
ALL_CASES = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD_DOMAIN   # 24 total
```

- **`gold_decomposition`** is `list[{deliverable, domain, match}]` — `deliverable` is the human-readable unit of work (and the eventual SFT target text), `domain` is the gold assignment `assignment_accuracy` grades against, and `match` is a deliberately-chosen, robust substring the router's task should contain (the honest v0 anchor; to be replaced by embedding similarity later — `training_eval_plan.md` §6). Empty default ⇒ the other 23 cases are untouched and `assignment_accuracy` returns `None` for them.
- **bd-01's gold** = 7 deliverables: clickstream→data_engineer, collaborative-filtering training→data_scientist, package+serving→ml_engineer, **drift monitoring→ml_engineer** (the boundary that catches the blind baseline's misroute), `/recommendations` API→software_dev, A/B traffic split→devops_mlops, CTR/conversion dashboard→analytics.
- **24 cases** spanning routing width — 6 single-domain, 15 two-to-three-domain, 3 broad (the broad cases route 4–6 domains). Each case's `notes` gives per-domain inclusion and exclusion reasoning — what makes R (over-routing) measurable.
- **Caution (`vars(cases)` collectors):** `cases` exposes both the category lists *and* `ALL_CASES`; iterate `ALL_CASES` (or dedupe by `id`) — naively scanning every module-level list double-counts each case.

### `warlock/eval/__init__.py` ✓ done

Empty package file for the eval module.

### `warlock/eval/metrics.py` ✓ done — five metric functions (+ assignment_accuracy this session)

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

def assignment_accuracy(task_decomposition, gold_decomposition) -> float | None   # added this session
    # for each gold deliverable: is there a router task containing its `match`
    # keyword that is routed to the gold `domain`? fraction of hits.
    # None when the case has no gold_decomposition.
```

- `_embedding(text)` lazily instantiates a module-level `SentenceTransformer("all-MiniLM-L6-v2")` and encodes; cosine computed with `numpy` `dot` / `norm`.
- **`assignment_accuracy`** is the per-deliverable task→domain metric the reframe needed — it sees *within-set* misassignment that `routing_precision` (set-based) cannot. On the blind baseline bd-01 scored `0.857` (drift→devops_mlops) against `Routing=1.0`; after the prompt fix it is `1.0`. v0 limitation: the `match` substring can false-negative if the router phrases the task without the keyword — tighten to embeddings before it feeds a training loop.
- **Baseline review verdict (unchanged):** `coverage` and `routing_precision` trustworthy at the set level; `acceptance_rate` not a scope signal; `output_fidelity` rewards prompt-echo. Still open from the review: make `acceptance_rate` scope-aware and reframe/replace `output_fidelity` (`EVAL_REFERENCE.md` §10, `training_eval_plan.md` §6).

### `warlock/eval/run_logger.py` ✓ done — read-only per-run feature row (+ Assignment this session)

```python
def log_run(memory, case: EvalCase | None = None, base_dir: str = "eval_runs"):
    # reads task_decomposition, agent_outputs, validation_results, problem_statement
    # has_case = case is not None;  expected_domains = case.expected_domains if has_case else None
    # row = { run_id (uuid), timestamp (utc iso), problem,
    #         Coverage, Routing, Assignment, Acceptance, Fidelity,
    #         has_case, case_id, iteration,
    #         task_decomposition, raw_outputs, validation_results, label=None }
    # appends one JSON line to eval_runs/<date>.jsonl  (dir auto-created)
    # returns row
```

- **`Assignment`** column added this session — `assignment_accuracy(task_decomposition, case.gold_decomposition if has_case else None)`. `None` for cases without a gold.
- Computes A/F always; C/R only when a case is given (else `None`). `has_case` flag means `None` never silently coerces to `0.0` (D7).
- `_max_iteration(validation_results)` returns `0` today (every agent runs at most once) — a forward-compat seam that will reflect real retry depth once the consensus loop lands (touch point 1).
- `label=None` — rows are unlabeled until eval Step 2. `eval_runs/` is gitignored (D8).
- **Note:** a *routing-only* re-baseline (decompose without running agents) yields rows with `Acceptance`/`Fidelity = null` and empty `raw_outputs` — that is how `eval_runs/2026-06-07.jsonl` was produced.

### `warlock/eval/EVAL_REFERENCE.md` ✓ done — consolidated metric + case review

The single reference for "do the cases and metrics measure routing quality?" Reviews all 24 cases and all four (now five) metrics against the captured baseline.
- **Cases:** 23/24 correctly specified as written; only `sd-02` needed a real fix (applied), `md-04` an optional hardening.
- **Metrics:** `coverage` trustworthy; `routing_precision` trustworthy **at the set level only** — blind to which deliverable went to which domain within the expected set (proven by bd-01/bd-02/bd-03, where drift→devops_mlops misassignment was invisible); `acceptance_rate` does not track scope (grades agents against the orchestrator's task partition, rewards out-of-scope work, penalizes scope-aware refusal, even manufactures out-of-taxonomy reasons); `output_fidelity` measures prompt-echo, uncorrelated with quality (the only perfect run scored lowest).
- **Fixes proposed:** the suite-level ownership rule as a header; scope-aware `acceptance_rate` (Fix A: post-hoc override; Fix B: split into `in_scope`/`executed`/`stayed_in_lane`); a per-deliverable `assignment_accuracy` with a `gold_assignments` field (**now built as `assignment_accuracy` over `gold_decomposition`**); reframe/replace `output_fidelity`.

### `warlock/eval/suite_notes.md` ✓ done — how to read aggregate scores

Companion reference for interpreting per-case and aggregate results. Contains the **suite-level ownership rule** with concrete per-case applications, per-metric interpretation notes, the full fidelity range table, and the routing×acceptance interaction taxonomy worked through every case (spurious alignment, genuine conflict, full inversion, anti-correlation-by-construction). Documents recurring orchestrator failure modes (keyword-triggered decomposition; the ml_engineer-vs-devops_mlops and data_scientist-vs-ml_engineer confusions; chain-shifting) and validator failure modes (scope-aware-penalty, non-determinism, out-of-taxonomy reasons, factual contradiction).

### `warlock/eval/training_eval_plan.md` ✓ done — the measure→train reframe

The plan that recasts the eval from a *measurement* instrument into a *training signal* for a small LLM. Core thesis: **the bar for a reward is higher than for a metric** — a reward is optimized against, so every confound a metric is allowed to have becomes a degenerate path. Contents:
- **Train the router first** (orchestrator: `problem → [{domain, task}]`) — gold is authorable, the suite already half-measures it, highest leverage. Defer the domain agents (gold outputs expensive) and the supervisor (circular to train a judge on outputs it grades).
- **Blocker:** cases carry only `expected_domains` (a *set*); SFT needs a per-example **`gold_decomposition`** (`[{deliverable, domain}]`). **Now started — added to `EvalCase`, authored for bd-01.** Author it for the rest of the discriminating cases; it triples as SFT target, `assignment_accuracy` source, and dense reward.
- **Metrics as rewards:** `coverage` keep-but-give-variance; `routing_precision` keep-never-alone; `acceptance_rate` fix before any reward use; `output_fidelity` do-not-reward; add `assignment_accuracy` (**built**).
- **Two distinct "small models":** the `[C,R,A,F]→y` logistic-regression eval-classifier (the **reward model / quality gate**) vs. the fine-tuned router (the **task-LLM** being improved). The suite is the router's held-out test and, once trustworthy, its reward.
- **Empirical findings** (§5): Coverage = 1.0 everywhere (no recall gradient), no labels yet, the orchestrator routed blind (**now fixed**), and decomposition is non-deterministic — **§5.4 confirmed this session: even `temperature=0` decompositions vary ±1 task run-to-run, so a trustworthy baseline needs N samples.**
- **Priority order** (§10): prompt-fix re-baseline (**done**) → `gold_decomposition` + `assignment_accuracy` (**started**) → scope-aware `A` / fence `F` → under-routing cases → `label.py` → generation + frozen holdout.

### `warlock/orchestrator.py` ✓ done — decompose, route, time, supervise (prompt fixed this session)

```python
class Orchestrator:
    def __init__(self, memory, client: LLMClient, model: str, supervisor=None):
        ...

    def register(self, agent): ...
    def decompose(self, problem): ...   # LLM (temperature=0) → JSON array [{domain, task}, ...]
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
- **Routing prompt (fixed this session):** `decompose`'s `ROLE` now carries a six-domain ownership charter + the four `agent_contracts.md` boundary rules (training→data_scientist; model-vs-infra monitoring split; API-surface vs serving-layer; dbt-config vs CI/CD), and runs at **`temperature=0`**. This is the Session 3.5 control — it lifted routing precision on ~15/24 cases (`eval_runs/2026-06-07.jsonl`). A precision-tightening "scope discipline" line was tried and **reverted** (broke md-15, didn't heal md-12). Residual misroutes (md-12) are the fine-tune's job, not the prompt's.

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

**ROLE highlights:** two-axis evaluation (ON-DOMAIN, QUALITY), JSON-only response (`{"accepted": bool, "reason": str}`), defensive code-fence strip on parse. P1 (`cache_read_tokens or 0` guard) and P3 (`temperature=0`) both fixed. **Baseline caveat:** the validator grades each agent against the orchestrator's assigned task, never against `expected_domains` — the root cause of `acceptance_rate` not tracking scope (`EVAL_REFERENCE.md` §3, fixable in the eval layer without touching production behavior).

### `warlock/trace_logger.py` ✓ done — validation event recorder

`TraceLogger` appends one JSONL record per validation event to `traces/<date>/<run_id>.jsonl`. Each record captures `run_id`, `timestamp`, `problem`, `agent`, `task`, `output`, `accepted`, `reason`, and `iteration`. Instantiated per run in `Orchestrator.run()` with a fresh `run_id` (UUID). The raw dataset for future fine-tuning of a cheaper supervisor model. Known gap: only iteration 0 is logged today — the blind retry's output is not yet recorded (fixed once the consensus loop lands). Distinct from the eval track's *per-run feature row* (`warlock/eval/run_logger.py`) — different grain, different purpose.

### `main.py` ✓ done — wires the triangle (no consensus yet)

Registers all six agents, instantiates the Supervisor, wires it into the Orchestrator. The driver runs one **cased eval run** per invocation: it points at the broadest case — `from warlock.eval.cases import BROAD_DOMAIN`, `case = next(c for c in BROAD_DOMAIN if c.id == "bd-03")`, then `orchestrator.run(case.problem)` followed by **`log_run(m, case=case)`** (appends one row to `eval_runs/<date>.jsonl`). Then prints the full memory log and the run summary. The free-text churn problem remains commented out above, with a bare `log_run(m)` example. Swapping the `case = next(...)` line across `SINGLE_DOMAIN` / `MULTI_DOMAIN` / `BROAD_DOMAIN` is how the full suite is run to (re)capture a baseline. *(The routing-only re-baseline sweep — decompose without running agents — was done by an ad-hoc script, not `main.py`.)*

### `.gitignore` ✓ done

Ignores all `*.txt` audit dumps, the `traces/` directory, and (D8) the `eval_runs/` dataset directory so raw agent outputs never get committed.

---

## What we are building next

### Eval Session 3.5 item 2 — extend gold + N-sample the baseline (active frontier)

Step 1 (the prompt-fix control) is done and recorded. Two threads now:

**A. Extend `gold_decomposition` to the remaining discriminating cases.** bd-01 has its gold; author it for **md-12** (the one stable regression — highest value), then **bd-02, bd-03, md-13** and the boundary `md-*`. Each is `[{deliverable, domain, match}]`, hand-authored from the case notes + `agent_contracts.md`, **human-reviewed before it becomes training gold** (D2/D6). This extends `assignment_accuracy` coverage from 1 case to the full discriminating set and fixes the SFT target shape.

**B. N-sample the routing baseline.** The `temperature=0` noise finding means one draw per case is not trustworthy for per-case deltas. Re-run each case **N times** (3–5) and record per-case mean ± spread of `Coverage`/`Routing`/`Assignment`. This is the precondition for using the suite as a *training reward* (a noisy reward teaches noise). The §5.4 greedy-vs-N-sample question is now answered by evidence: N-sample.

Then items 3–4 of Session 3.5: make `acceptance_rate` scope-aware (Fix A) and fence `output_fidelity` out of any reward (both post-hoc eval-layer overrides, no change to production behavior); author under-routing / hard-negative cases so `coverage` gains variance (today it is 1.0 on every case).

### Phase 4 consensus loop (Session 4 — runs independently of the eval-training work)

Full retry loop replacing the current one-blind-retry in `orchestrator.py`:
- Cap at 3 iterations per agent; pass the rejection **reason** back to the agent on each retry.
- Log every iteration via `TraceLogger` (currently only iteration 0 — touch point 2). Update `_max_iteration` in `run_logger.py` to reflect real retry depth (touch point 1).
- After 3 failed iterations, tag output `confidence: low`, `consensus=partial`, continue (escape valve).
- Parallel multi-agent run once the retry loop is stable.
- Clarifying questions deferred to Phase 5 (needs a user in the loop).
- **Session 5 — re-measure:** re-run the suite, compare to the baseline. A flat-quality / 3×-token result is a valid negative result.

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
├── llm.py                 ✓ done — LLMClient Protocol (incl. temperature), LLMResponse, LLMUsage
├── orchestrator.py        ✓ done — decompose (charter+rules, temperature=0), register, route, run, supervisor hook, trace logging
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
    ├── __init__.py            ✓ done
    ├── cases.py               ✓ done — 24 EvalCase suite + verified flag (20/24) + gold_decomposition (bd-01); BROAD_DOMAIN
    ├── agent_contracts.md     ✓ done — settled domain boundaries (ds ↔ mle, mle ↔ devops, de ↔ devops)
    ├── metrics.py             ✓ done — coverage, routing_precision, acceptance_rate, output_fidelity, assignment_accuracy
    ├── run_logger.py          ✓ done — read-only per-run feature row (+ Assignment) → eval_runs/<date>.jsonl
    ├── EVAL_REFERENCE.md      ✓ done — per-case + per-metric correctness review
    ├── suite_notes.md         ✓ done — how to read aggregate scores
    └── training_eval_plan.md  ✓ done — measure→train reframe (router-first)
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor + cased log_run (drives bd-03)
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml              ✓ done — + numpy, sentence-transformers
eval_runs/2026-06-04.jsonl  ✓ captured (gitignored) — 24-row blind baseline, one per case
eval_runs/2026-06-07.jsonl  ✓ captured (gitignored) — 24-row prompt-fix re-baseline (routing-only)
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
.specs/next-steps.md        ✓ done — session sequencing (S1–S3 done, S3.5 item 1 done)
                            ← next: extend gold_decomposition (md-12, bd-02/03, md-13) + N-sample baseline
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
