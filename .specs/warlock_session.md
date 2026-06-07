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

**Added run-provenance telemetry to the eval logger — the "store results like telemetry, not test logs" upgrade.** Motivated by Anthropic's *self-service data analytics with Claude* post (2026-06-03): every `eval_runs/*.jsonl` row now records *which version of the system produced it*, so re-baselines compare as a time series instead of unattributable one-off captures. Pure observability — no scoring change, no production-behavior change.

1. **Stamped five provenance fields onto every row** (`run_logger.py`) — `git_sha` (short HEAD, `-dirty` suffix when the tree differs from the commit), `model` (the router/orchestrator model — a row is a routing record), `temperature`, plus `token_spend` and `timing` lifted straight from memory (free reads — the orchestrator already wrote them). `model`/`temperature` come from a new `run_config` memory key.
2. **`run_config` written by the orchestrator** (`orchestrator.py`) — `decompose` writes `{model, temperature}` to memory on the line next to the actual LLM call, so the logged config can't drift from what ran. Chosen over passing params to `log_run` *because* the temperature literal lives inside `decompose`; routing it through memory ("memory is the bus") keeps the source of truth colocated with the call and leaves the `main.py` call site untouched.
3. **`_git_sha()` helper** (`run_logger.py`) — `git rev-parse --short HEAD`, then a second `git status --porcelain` for dirtiness; returns `<sha>-dirty` when non-empty, the bare sha when clean, `None` if git fails (telemetry must never break a run). Chose `--porcelain` over `git describe --dirty` deliberately: `describe --dirty` ignores *untracked* files, but `run_baseline.py`/`calibrate_assignment.py` are themselves untracked and generate eval rows — `--porcelain` catches them; `.gitignore`'d files (`__pycache__`) are excluded, so no false dirt. Verified: returns `66cec7c-dirty` on the current tree.
4. **Folded a distillation caution into `training_eval_plan.md §7`** — a blockquote recording the post's *negative* ablation (raw grep access to thousands of correct prior queries moved accuracy <1 point with the answer present ~80% of the time — *structured* per-domain docs carried the signal, not the corpus) and its failed LLM-auto-generated semantic layer (net-negative on their evals). Two constraints on the §7 SFT/generation work: (1) the SFT label is the *structured* gold (`gold_decomposition` + `agent_contracts.md`), not a raw-decomposition dump — expect raw-corpus augmentation to underperform; (2) Claude *drafts* the gold, a human *owns the definition* — exactly the D2/D6 "generate, then audit" rule.

**Key decisions:**
- **`git_sha` semantics = "the code that produced this row differs in any non-ignored way from commit X."** A `-dirty` stamp is the honest reproducibility signal — better than a clean sha that silently overstates what ran.
- **`model` is the orchestrator model only, by design** — not the agents' or supervisor's (all haiku today). A row is fundamentally a routing record, so the router model is the right single attribution; a comment in the logger flags this so it isn't read as whole-system.
- **The telemetry work is the blog's actionable takeaway, distilled.** The earlier discussion mapped the post onto Warlock and found it mostly *validates* the existing plan (prompt-as-free-baseline, structure-over-fuzzy-scoring, human-owned gold); the two things it actually *adds* are this telemetry upgrade and the §7 distillation constraint — both now landed.

Uncommitted at session close: modified `warlock/eval/run_logger.py`, `warlock/orchestrator.py`, `warlock/eval/training_eval_plan.md`. No new files; `eval_runs/` stays gitignored (D8).

The active frontier is unchanged — **eval Session 3.5 items 3–4**: make `acceptance_rate` scope-aware (Fix A) + fence `output_fidelity` out of any reward, then author under-routing / hard-negative cases so `coverage` gains variance. The standing structural fix (deliverable-level `decompose` output) and the Phase 4 consensus loop (Session 4) remain open and independent.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note reflects Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`, the curated suite in `warlock/eval/cases.py` (a `verified` flag + `gold_decomposition` for the 5 discriminating cases), the built logger (`metrics.py` — incl. embedding-based `assignment_accuracy` — `run_logger.py`), the **captured baselines** (`eval_runs/2026-06-04.jsonl` blind, `eval_runs/2026-06-07.jsonl` prompt-fix, `eval_runs/nsample/2026-06-07.jsonl` N-sample), the review docs (`EVAL_REFERENCE.md`, `suite_notes.md`), the **measure→train reframe** (`warlock/eval/training_eval_plan.md`), the **prompt-fix re-baseline control** (charter + boundary rules + `temperature=0` in `decompose`), the session sequencing in `.specs/next-steps.md`, and the boundary contracts in `warlock/eval/agent_contracts.md`.

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

### `warlock/eval/cases.py` ✓ done — curated eval suite (gold extended this session)

The human-owned ground truth the eval logger measures routing against (D2, D6). **21 of 24 cases are `verified=True`** (bd-01 flipped `True` this session; md-15, bd-02, bd-03 remain `False`, pending confirmation before they become training gold). The `gold_decomposition` field (the per-example router target the reframe requires) is now authored for the **5 discriminating cases** — bd-01, bd-02, bd-03, md-12, md-13.

```python
@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""
    verified: bool = False
    gold_decomposition: list[dict] = field(default_factory=list)   # [{deliverable, domain}]

SINGLE_DOMAIN: list[EvalCase] = [...]   # sd-01 … sd-06  (6)
MULTI_DOMAIN:  list[EvalCase] = [...]   # md-01 … md-15  (15, md-13 precedes md-15)
BROAD_DOMAIN:  list[EvalCase] = [...]   # bd-01 … bd-03  (3)
ALL_CASES = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD_DOMAIN   # 24 total
```

- **`gold_decomposition`** is `list[{deliverable, domain}]` — `deliverable` is the human-readable unit of work (and the SFT target text), `domain` is the gold assignment `assignment_accuracy` grades against. The keyword `match` field was **removed this session** when the metric went embedding-based (the deliverable text is now the locator). Empty default ⇒ the 19 non-discriminating cases are untouched and `assignment_accuracy` returns `None` for them.
- **The 5 golds** carry the boundary distinctions the big cases were built to test — e.g. **drift monitoring→ml_engineer** (bd-01/bd-02, catches the blind baseline's drift→devops misroute) and **define promotion criteria→data_scientist** (bd-03, catches the misroute to ml_engineer). Deliverable text reads like a human description, deliberately independent of the router's phrasing.
- **24 cases** spanning routing width — 6 single-domain, 15 two-to-three-domain, 3 broad (the broad cases route 4–6 domains). Each case's `notes` gives per-domain inclusion and exclusion reasoning — what makes R (over-routing) measurable.
- **Caution (`vars(cases)` collectors):** `cases` exposes both the category lists *and* `ALL_CASES`; iterate `ALL_CASES` (or dedupe by `id`) — naively scanning every module-level list double-counts each case.

### `warlock/eval/__init__.py` ✓ done

Empty package file for the eval module.

### `warlock/eval/metrics.py` ✓ done — five metric functions (`assignment_accuracy` now embedding-based)

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

def assignment_accuracy(task_decomposition, gold_decomposition, threshold=0.30) -> float | None
    # per gold deliverable: best cosine( embed(deliverable), embed(task) ) over tasks
    # IN the expected domain; hit if >= threshold. fraction of hits.
    # None when the case has no gold_decomposition.

def _cosine(a, b) -> float   # dot(a,b) / (norm(a)*norm(b))  — added this session
```

- `_embedding(text)` lazily instantiates a module-level `SentenceTransformer("all-MiniLM-L6-v2")` and encodes; `_cosine` (added this session) wraps the `numpy` `dot`/`norm` cosine.
- **`assignment_accuracy`** is the per-deliverable task→domain metric the reframe needed — it sees *within-set* misassignment that `routing_precision` (set-based) cannot. **Rewritten this session from keyword-substring to embedding similarity** (the `match` field is gone): a hit means the expected domain has a task semantically close to the deliverable, which is robust to paraphrase. `threshold=0.30` was calibrated offline against the N-sample decompositions (`calibrate_assignment.py`) — correct on bd-01/bd-02/bd-03/md-13, one residual false miss on md-12 (short "CSV export" diluted in a multi-clause task). **Known limitation:** embeddings only bridge the per-deliverable-gold vs one-paragraph-per-domain granularity mismatch; the real fix is deliverable-level orchestrator output (`training_eval_plan.md` §9).
- **Baseline review verdict (unchanged):** `coverage` and `routing_precision` trustworthy at the set level; `acceptance_rate` not a scope signal; `output_fidelity` rewards prompt-echo. Still open from the review: make `acceptance_rate` scope-aware and reframe/replace `output_fidelity` (`EVAL_REFERENCE.md` §10, `training_eval_plan.md` §6).

### `warlock/eval/run_logger.py` ✓ done — read-only per-run feature row (+ run-provenance telemetry this session)

```python
def log_run(memory, case: EvalCase | None = None, base_dir: str = "eval_runs"):
    # reads task_decomposition, agent_outputs, validation_results, problem_statement, run_config
    # has_case = case is not None;  expected_domains = case.expected_domains if has_case else None
    # row = { run_id (uuid), timestamp (utc iso),
    #         git_sha, model, temperature,            # provenance (this session)
    #         problem,
    #         Coverage, Routing, Assignment, Acceptance, Fidelity,
    #         has_case, case_id, iteration,
    #         token_spend, timing,                     # cost/latency (this session)
    #         task_decomposition, raw_outputs, validation_results, label=None }
    # appends one JSON line to eval_runs/<date>.jsonl  (dir auto-created)
    # returns row

def _git_sha() -> str | None:
    # `git rev-parse --short HEAD`, then `git status --porcelain`;
    # returns "<sha>-dirty" if the tree is dirty, "<sha>" if clean, None on failure
```

- **Run-provenance telemetry added this session** (the "store results like telemetry" upgrade): `git_sha` (with `-dirty` marker), `model` (router/orchestrator model only — a row is a routing record), `temperature`, plus `token_spend`/`timing` read straight from memory. `model`/`temperature` come from the new `run_config` key the orchestrator writes; `git_sha` from `_git_sha()` (uses `--porcelain`, so untracked eval scripts count as dirty and `.gitignore`'d files don't). Makes "did that change help?" a query over the rows and catches slow regressions across re-baselines.
- **`Assignment`** column (prior session) — `assignment_accuracy(task_decomposition, case.gold_decomposition if has_case else None)`. `None` for cases without a gold.
- Computes A/F always; C/R only when a case is given (else `None`). `has_case` flag means `None` never silently coerces to `0.0` (D7).
- `_max_iteration(validation_results)` returns `0` today (every agent runs at most once) — a forward-compat seam that will reflect real retry depth once the consensus loop lands (touch point 1).
- `label=None` — rows are unlabeled until eval Step 2. `eval_runs/` is gitignored (D8).
- **Note:** a *routing-only* re-baseline (decompose without running agents) yields rows with `Acceptance`/`Fidelity = null` and empty `raw_outputs` — that is how `eval_runs/2026-06-07.jsonl` was produced.

### `warlock/eval/run_baseline.py` ✓ done — decompose-only N-sample harness (new this session)

Samples the router without running agents — far cheaper than `orchestrator.run()` and isolates the routing target. For each case it calls `orchestrator.decompose(case.problem)` N times, writes `problem_statement` + `task_decomposition` to memory, and logs one routing-only row per sample via `log_run(case=case, base_dir="eval_runs/nsample")`. `Acceptance`/`Fidelity` are `null` by design (no agents, no embedding-model load). Malformed samples (bad JSON / missing `domain`) are skipped, not fatal. Prints a per-case `C`/`R`/`A` mean[min-max] summary.

```bash
uv run python -m warlock.eval.run_baseline --samples 5
uv run python -m warlock.eval.run_baseline --samples 8 --cases md-12,bd-02,bd-03,md-13
```

Captured `eval_runs/nsample/2026-06-07.jsonl` (24 cases × 5 = 120 rows). Confirmed `temperature=0` is non-deterministic (Routing/Assignment spread across identical samples) and surfaced new Coverage variance (md-12 = 0.50, md-03 = 0.60 — the orchestrator drops a needed domain on those).

### `warlock/eval/calibrate_assignment.py` ✓ done — offline threshold calibration (new this session)

Re-scores the captured N-sample decompositions locally (no API — all-MiniLM on CPU). For each gold deliverable it computes the best cosine to a task in the expected domain, prints the per-deliverable similarity table (sorted, so real hits/misses separate) and a per-case Assignment sweep across thresholds 0.20–0.50. This is how `threshold=0.30` was chosen: it keeps bd-01/bd-02/md-13 perfect, catches bd-03's promotion-criteria misroute (sim 0.29 < 0.30) and md-12's analytics drop, with one CSV-dilution false miss. Re-run when the gold set grows.

```bash
uv run python -m warlock.eval.calibrate_assignment
```

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
- **Blocker:** cases carry only `expected_domains` (a *set*); SFT needs a per-example **`gold_decomposition`** (`[{deliverable, domain}]`). **Now done — added to `EvalCase`, authored for the 5 discriminating cases (bd-01/02/03, md-12, md-13).** It triples as SFT target, `assignment_accuracy` source, and dense reward.
- **Metrics as rewards:** `coverage` keep-but-give-variance; `routing_precision` keep-never-alone; `acceptance_rate` fix before any reward use; `output_fidelity` do-not-reward; add `assignment_accuracy` (**built, now embedding-based**).
- **Two distinct "small models":** the `[C,R,A,F]→y` logistic-regression eval-classifier (the **reward model / quality gate**) vs. the fine-tuned router (the **task-LLM** being improved). The suite is the router's held-out test and, once trustworthy, its reward.
- **Empirical findings** (§5): Coverage = 1.0 everywhere (no recall gradient), no labels yet, the orchestrator routed blind (**now fixed**), and decomposition is non-deterministic — **§5.4 confirmed this session: even `temperature=0` decompositions vary ±1 task run-to-run, so a trustworthy baseline needs N samples.**
- **Priority order** (§10): prompt-fix re-baseline (**done**) → `gold_decomposition` + `assignment_accuracy` (**done, embedding-based**) → scope-aware `A` / fence `F` → under-routing cases → `label.py` → generation + frozen holdout. §9 now records the structural root-cause fix (deliverable-level orchestrator output).
- **§7 caution (this session):** a blockquote folds in Anthropic's negative ablation — raw access to a large correct-query corpus moved accuracy <1 point; *structured* docs carried the signal, and an LLM-auto-generated semantic layer was net-negative. Constraint on the SFT/generation plan: the label is the structured gold (`gold_decomposition` + `agent_contracts.md`), not a raw-decomposition dump, and humans own the gold definition (the existing D2/D6 "generate, then audit" rule).

### `warlock/orchestrator.py` ✓ done — decompose, route, time, supervise (prompt fixed this session)

```python
class Orchestrator:
    def __init__(self, memory, client: LLMClient, model: str, supervisor=None):
        ...

    def register(self, agent): ...
    def decompose(self, problem): ...   # writes run_config{model,temperature}; LLM (temperature=0) → JSON array [{domain, task}, ...]
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
- **Routing prompt (fixed an earlier session):** `decompose`'s `ROLE` now carries a six-domain ownership charter + the four `agent_contracts.md` boundary rules (training→data_scientist; model-vs-infra monitoring split; API-surface vs serving-layer; dbt-config vs CI/CD), and runs at **`temperature=0`**. This is the Session 3.5 control — it lifted routing precision on ~15/24 cases (`eval_runs/2026-06-07.jsonl`). A precision-tightening "scope discipline" line was tried and **reverted** (broke md-15, didn't heal md-12). Residual misroutes (md-12) are the fine-tune's job, not the prompt's.
- **Run provenance (this session):** `decompose` writes `run_config = {model, temperature}` to memory next to the LLM call, so `run_logger.log_run` can stamp each row with the exact router model + temperature that produced it — the value can't drift from what actually ran. Pure telemetry; routing behavior is unchanged.

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

### Eval Session 3.5 items 3–4 — scope-aware `A`, under-routing cases (active frontier)

Steps 1–2 are done: prompt-fix control captured, gold authored for the 5 discriminating cases, `assignment_accuracy` made embedding-based, and the baseline N-sampled (`eval_runs/nsample/2026-06-07.jsonl`). Remaining 3.5 work, all pure eval-layer (no change to production behavior):

**Item 3 — make `acceptance_rate` scope-aware + fence `output_fidelity`.** Fix A (`EVAL_REFERENCE.md` §10.1): a post-hoc override in the eval layer — a domain ∉ `expected_domains` ⇒ its acceptance counts as rejected — so `A` stops inverting against scope. And document/fence `output_fidelity` out of any reward (it rewards prompt-echo). Small edits in `metrics.py`/`run_logger.py`; the supervisor's production behavior is untouched.

**Item 4 — author under-routing / hard-negative cases.** `coverage` is still ~1.0 across the suite (the orchestrator over-routes, never under-routes), so recall has no gradient. Author cases where dropping a needed domain is the *easy* mistake (e.g. a problem that reads as pure software work but genuinely needs `data_engineer`), so `coverage` gains variance as both metric and reward.

**Standing structural fix (with the orchestrator/training rework, not now):** make `decompose` emit `{deliverable, domain}` instead of one prose task per domain. Turns `assignment_accuracy` into an exact, deterministic set comparison and makes the output shape identical to the SFT target (`training_eval_plan.md` §9). Cost: changes the production contract, invalidates the baseline, forces a re-capture.

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
├── orchestrator.py        ✓ done — decompose (charter+rules, temperature=0, run_config write), register, route, run, supervisor hook, trace logging
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
    ├── __init__.py              ✓ done
    ├── cases.py                 ✓ done — 24 EvalCase suite + verified flag (21/24) + gold_decomposition (5 cases, no match); BROAD_DOMAIN
    ├── agent_contracts.md       ✓ done — settled domain boundaries (ds ↔ mle, mle ↔ devops, de ↔ devops)
    ├── metrics.py               ✓ done — coverage, routing_precision, acceptance_rate, output_fidelity, assignment_accuracy (embedding, 0.30)
    ├── run_logger.py            ✓ done — per-run feature row + provenance (git_sha/-dirty, model, temperature, token_spend, timing) → eval_runs/<date>.jsonl
    ├── run_baseline.py          ✓ done — decompose-only N-sample harness → eval_runs/nsample/<date>.jsonl
    ├── calibrate_assignment.py  ✓ done — offline threshold sweep for assignment_accuracy
    ├── EVAL_REFERENCE.md        ✓ done — per-case + per-metric correctness review
    ├── suite_notes.md           ✓ done — how to read aggregate scores
    └── training_eval_plan.md    ✓ done — measure→train reframe (router-first)
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor + cased log_run (drives bd-03)
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml              ✓ done — + numpy, sentence-transformers
eval_runs/2026-06-04.jsonl  ✓ captured (gitignored) — 24-row blind baseline, one per case
eval_runs/2026-06-07.jsonl  ✓ captured (gitignored) — 24-row prompt-fix re-baseline (routing-only)
eval_runs/nsample/2026-06-07.jsonl ✓ captured (gitignored) — 120-row N-sample routing baseline (24×5)
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
.specs/next-steps.md        ✓ done — session sequencing (S1–S3 done, S3.5 items 1–2 done)
                            ← next: scope-aware acceptance_rate + under-routing cases; structural fix = deliverable-level decompose output
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
