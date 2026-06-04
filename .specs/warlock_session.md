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

**Captured the eval baseline (Session 3 done) and reframed the eval track from *measuring* a run to *training a small LLM*.** The logger built last session ran over the full suite; the captured rows were then reviewed metric-by-metric and case-by-case, and that review changed the track's goal.

1. **Captured the baseline** — ran all 24 cases through today's orchestrator (single blind retry), producing `eval_runs/2026-06-04.jsonl` (24 rows, one per case). The Step-1 verify gate passed (broad cases `R < 1`, single-domain `C=R=1.0`, A/F in range, raw outputs captured, `label=null`).
2. **Reviewed the metrics and cases against the captured rows** → two new analysis docs:
   - `warlock/eval/EVAL_REFERENCE.md` — consolidated per-case + per-metric correctness review. 23/24 cases sound (only `sd-02` needed a real fix, since applied; `md-04` an optional hardening). `coverage` + `routing_precision` trustworthy at the **set level**; `acceptance_rate` is **not** a scope signal; `output_fidelity` is the weakest (rewards prompt-echo — the only perfect run, bd-01, scored *lowest*).
   - `warlock/eval/suite_notes.md` — how to read aggregate scores; the routing×acceptance interaction taxonomy (spurious alignment / genuine conflict / full inversion / anti-correlation) worked through all 24 cases.
3. **Reframed the track to training (router-first)** → `warlock/eval/training_eval_plan.md`. A training signal is *optimized against*, so the bar rises above a measurement metric: two of four metrics are unsafe as rewards, `coverage` has zero variance, and the cases carry no per-example target.
4. **Edited `cases.py`** — added an `EvalCase.verified: bool` flag (20 of 24 → `True`; md-15, bd-01, bd-02, bd-03 still pending); applied the `sd-02` view/semantic-layer ownership fix; strengthened many exclusion notes with the suite-level lifecycle-ownership rule; moved `md-13` up into `MULTI_DOMAIN` (before `md-15`); renamed `BROAD` → `BROAD_DOMAIN`.
5. **Switched the `main.py` driver to `bd-03`** (the broadest case) — `from warlock.eval.cases import BROAD_DOMAIN`, `case = next(c for c in BROAD_DOMAIN if c.id == "bd-03")`.

**Key empirical findings (read off the 24 rows):**
- **`Coverage = 1.0` on every case** — the orchestrator never *missed* a needed domain; its only failure mode is over-routing. Recall is therefore untrained and untested (no case makes dropping a domain tempting).
- **`Routing` spans 0.33–1.0**, doing the real discrimination.
- **`routing_precision` is set-based and blind to task→domain assignment** — in all three broad cases the orchestrator pushed **drift monitoring to devops_mlops** when the spec assigns it to **ml_engineer**, and (bd-02/bd-03) **training to ml_engineer** when it belongs to **data_scientist** — none visible to the metric because the domains are still in the expected set.
- **`acceptance_rate` / `output_fidelity` do not track scope** and are dangerous as rewards.

Uncommitted at session close: modified `main.py`, `warlock/eval/cases.py`; untracked `warlock/eval/EVAL_REFERENCE.md`, `warlock/eval/suite_notes.md`, `warlock/eval/training_eval_plan.md`. (`eval_runs/` and its baseline file are gitignored — D8.)

The active frontier is now the **prompt-fix re-baseline control** (Session 3.5): load the boundary rules into `Orchestrator.decompose`'s prompt and set `temperature=0`, re-run the suite, and report the delta against the 2026-06-04 baseline. The Phase 4 consensus loop remains open (Session 4), running independently of the eval-training work.

---

## What we have built so far

### `constitution.md` ✓ done

The soul of the project. Three sections: the spirit of Warlock (oathbreaker energy), how we build (teach before writing, learn at the same pace), and the laws (one agent one domain, memory is the bus, **triangle owns truth**, cost discipline, ship before you design).

### `README.md` ✓ done

Public-facing entry point. Project overview, stack, run command, triangle architecture diagram, layer table, and current status. Mirrors the canonical architecture in `constitution.md` and `.specs/plan.md`.

### `CLAUDE.md` ✓ done

Stripped to technical-only content. Points to `constitution.md` for all principles and collaboration rules. Build-sequence note reflects Phase 4 in progress, plus a pointer to the evaluation track in `.specs/eval_ml_plan.md`, the curated suite in `warlock/eval/cases.py` (now with a `verified` flag), the built logger (`metrics.py`, `run_logger.py`), the **captured baseline** (`eval_runs/2026-06-04.jsonl`), the review docs (`EVAL_REFERENCE.md`, `suite_notes.md`), the **measure→train reframe** (`warlock/eval/training_eval_plan.md`), the session sequencing in `.specs/next-steps.md`, and the boundary contracts in `warlock/eval/agent_contracts.md`.

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

Orders the eval pipeline and the Phase 4 consensus loop into startable-cold sessions, under the principle **measure before you improve**. Sessions 1–3 are done (suite drafted + reviewed, logger built, baseline captured). This session inserted **Session 3.5 — the measure→train reframe**: the prompt-fix re-baseline control (boundary rules + `temperature=0` in `decompose`), then `gold_decomposition` + `assignment_accuracy`, scope-aware `acceptance_rate`, and under-routing cases — taken ahead of the consensus loop. The three eval↔consensus touch points (A + iteration count, trace-logger completeness, confidence-score fusion) and the open note on the agent clarification loop (F/A computed on final output only; `iteration` reflects real clarification-round depth) are retained.

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

Third entry — **data_engineer ↔ devops_mlops** (decided in `md-15`): the seam is workflow files vs. project config. devops_mlops owns the CI/CD workflow (GitHub Actions YAML, deployment scripts, secrets/env wiring); data_engineer owns dbt project readiness (`profiles.yml` targets, `dbt_project.yml`, state-artifact logic, schema validation). Handoff trigger: who needs domain knowledge — a devops engineer writes the Actions YAML without knowing dbt internals; a data engineer owns whether the dbt project is structured to support those workflows.

> **Baseline observation (this session):** the live orchestrator *fails* the ml_engineer ↔ devops_mlops boundary in all three broad cases — drift monitoring routed to devops_mlops when the contract assigns it to ml_engineer — and the data_scientist ↔ ml_engineer boundary in bd-02/bd-03 (training routed to ml_engineer). `routing_precision` cannot see either because the misrouted domain is still inside the expected set; only the proposed `assignment_accuracy` metric would.

### `warlock/eval/cases.py` ✓ done — curated eval suite (reviewed this session)

The human-owned ground truth the eval logger measures routing against (D2, D6). The review/correction pass is done: an `EvalCase.verified: bool` field was added and 20 of 24 cases are now `verified=True` (md-15, bd-01, bd-02, bd-03 remain `False`, pending confirmation before they become training gold).

```python
@dataclass
class EvalCase:
    id: str
    problem: str
    expected_domains: list[str]
    notes: str = ""
    verified: bool = False        # added this session

SINGLE_DOMAIN: list[EvalCase] = [...]   # sd-01 … sd-06  (6)
MULTI_DOMAIN:  list[EvalCase] = [...]   # md-01 … md-15  (15, md-13 now precedes md-15)
BROAD_DOMAIN:  list[EvalCase] = [...]   # bd-01 … bd-03  (3)   (renamed from BROAD)
ALL_CASES = SINGLE_DOMAIN + MULTI_DOMAIN + BROAD_DOMAIN   # 24 total
```

- **24 cases** spanning routing width — 6 single-domain, 15 two-to-three-domain, 3 broad (the broad cases route 4–6 domains).
- This session's edits: (1) added the `verified` flag; (2) applied the **`sd-02` fix** — the view/semantic SQL layer behind a dashboard is now explicitly assigned to **analytics** (writing aggregation SQL for one's own dashboard is analytics, not data engineering); (3) strengthened many exclusion notes to cite the **suite-level lifecycle-ownership rule** (operational hooks live inside the domain that owns the artifact they sit in, unless they have independent lifecycle); (4) moved **`md-13`** (fine-tune BERT + nightly batch scoring) up into `MULTI_DOMAIN` before `md-15`; (5) renamed the broad list `BROAD` → `BROAD_DOMAIN` (the import in `main.py` follows).
- Each case's `notes` gives per-domain **inclusion and exclusion** reasoning — what makes R (routing-precision / over-routing) measurable.

### `warlock/eval/__init__.py` ✓ done

Empty package file for the eval module.

### `warlock/eval/metrics.py` ✓ done — the four metric functions

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
- **Baseline review verdict:** `coverage` and `routing_precision` are trustworthy at the set level; `acceptance_rate` is not a scope signal; `output_fidelity` rewards prompt-echo. The review (`EVAL_REFERENCE.md` §10, `training_eval_plan.md` §6) proposes adding `assignment_accuracy`, making `acceptance_rate` scope-aware, and reframing/replacing `output_fidelity` — none built yet.

### `warlock/eval/run_logger.py` ✓ done — read-only per-run feature row

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

### `warlock/eval/EVAL_REFERENCE.md` ✓ done — consolidated metric + case review (this session)

The single reference for "do the cases and metrics measure routing quality?" Reviews all 24 cases and all four metrics against the captured baseline.
- **Cases:** 23/24 correctly specified as written; only `sd-02` needed a real fix (applied), `md-04` an optional hardening.
- **Metrics:** `coverage` trustworthy; `routing_precision` trustworthy **at the set level only** — blind to which deliverable went to which domain within the expected set (proven by bd-01/bd-02/bd-03, where drift→devops_mlops misassignment was invisible); `acceptance_rate` does not track scope (grades agents against the orchestrator's task partition, rewards out-of-scope work, penalizes scope-aware refusal, even manufactures out-of-taxonomy reasons); `output_fidelity` measures prompt-echo, uncorrelated with quality (the only perfect run scored lowest).
- **Fixes proposed:** the suite-level ownership rule as a header; scope-aware `acceptance_rate` (Fix A: post-hoc override; Fix B: split into `in_scope`/`executed`/`stayed_in_lane`); a per-deliverable `assignment_accuracy` with a `gold_assignments` field; reframe/replace `output_fidelity`.

### `warlock/eval/suite_notes.md` ✓ done — how to read aggregate scores (this session)

Companion reference for interpreting per-case and aggregate results. Contains the **suite-level ownership rule** with concrete per-case applications, per-metric interpretation notes, the full fidelity range table, and the routing×acceptance interaction taxonomy worked through every case (spurious alignment, genuine conflict, full inversion, anti-correlation-by-construction). Documents recurring orchestrator failure modes (keyword-triggered decomposition; the ml_engineer-vs-devops_mlops and data_scientist-vs-ml_engineer confusions; chain-shifting) and validator failure modes (scope-aware-penalty, non-determinism, out-of-taxonomy reasons, factual contradiction).

### `warlock/eval/training_eval_plan.md` ✓ done — the measure→train reframe (this session)

The plan that recasts the eval from a *measurement* instrument into a *training signal* for a small LLM. Core thesis: **the bar for a reward is higher than for a metric** — a reward is optimized against, so every confound a metric is allowed to have becomes a degenerate path. Contents:
- **Train the router first** (orchestrator: `problem → [{domain, task}]`) — gold is authorable, the suite already half-measures it, highest leverage. Defer the domain agents (gold outputs expensive) and the supervisor (circular to train a judge on outputs it grades).
- **Blocker:** cases carry only `expected_domains` (a *set*); SFT needs a per-example **`gold_decomposition`** (`[{deliverable, domain}]`). Author it for the discriminating cases first; it triples as SFT target, `assignment_accuracy` source, and dense reward.
- **Metrics as rewards:** `coverage` keep-but-give-variance; `routing_precision` keep-never-alone; `acceptance_rate` fix before any reward use; `output_fidelity` do-not-reward; add `assignment_accuracy`.
- **Two distinct "small models":** the `[C,R,A,F]→y` logistic-regression eval-classifier (the **reward model / quality gate**) vs. the fine-tuned router (the **task-LLM** being improved). The suite is the router's held-out test and, once trustworthy, its reward.
- **Empirical findings** (§5): Coverage = 1.0 everywhere (no recall gradient), no labels yet, the orchestrator routes blind (no boundary rules in its prompt), and decomposition is non-deterministic (`temperature` unset in `decompose`).
- **Priority order** (§10): prompt-fix re-baseline (free control) → `gold_decomposition` + `assignment_accuracy` → scope-aware `A` / fence `F` → under-routing cases → `label.py` → generation + frozen holdout.

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
- **Known gap (from this session's baseline):** `decompose()`'s system prompt lists only the six domain names + output format — no boundary rules, no `temperature=0`. Fixing this is the Session 3.5 control (the cheapest routing-quality win and the baseline any fine-tune must beat).

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

Registers all six agents, instantiates the Supervisor, wires it into the Orchestrator. The driver runs one **cased eval run** per invocation: this session it points at the broadest case — `from warlock.eval.cases import BROAD_DOMAIN`, `case = next(c for c in BROAD_DOMAIN if c.id == "bd-03")`, then `orchestrator.run(case.problem)` followed by **`log_run(m, case=case)`** (appends one row to `eval_runs/<date>.jsonl`). Then prints the full memory log and the run summary. The free-text churn problem remains commented out above, with a bare `log_run(m)` example. Swapping the `case = next(...)` line across `SINGLE_DOMAIN` / `MULTI_DOMAIN` / `BROAD_DOMAIN` is how the full suite is run to (re)capture a baseline.

### `.gitignore` ✓ done

Ignores all `*.txt` audit dumps, the `traces/` directory, and (D8) the `eval_runs/` dataset directory so raw agent outputs never get committed.

---

## What we are building next

### Eval Session 3.5 — prompt-fix re-baseline (active frontier)

The baseline is captured and reviewed; the review shows the orchestrator **routes blind** (its `decompose` prompt has no boundary rules and no `temperature=0`). Before training anything, capture the honest control: the cheapest possible improvement, and the number any later fine-tune must beat.

**Do (priority order from `training_eval_plan.md` §10):**
1. **Load boundary rules + `temperature=0` into `Orchestrator.decompose`.** Put the suite-level ownership rule and the `agent_contracts.md` boundaries (and a few gold decompositions as few-shot) into the system prompt; set `temperature=0` for reproducibility. Re-run all 24 cases; record the new rows alongside `eval_runs/2026-06-04.jsonl` and report the `Routing` delta.
2. **Add `gold_decomposition` + `assignment_accuracy`.** Add `gold_decomposition: list[{deliverable, domain}]` to the discriminating cases (bd-01/02/03, md-13, boundary md-\*) and a per-deliverable `assignment_accuracy` metric in `metrics.py` — the only metric that catches drift→devops_mlops and training→ml_engineer, and the SFT target.
3. **Make `acceptance_rate` scope-aware (Fix A) and fence `output_fidelity`** out of any reward — both as a post-hoc eval-layer override; do not touch the supervisor's production behavior.
4. **Author under-routing / hard-negative cases** so `coverage` gains variance (today it is 1.0 on every case).

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
    ├── __init__.py            ✓ done
    ├── cases.py               ✓ done — 24 EvalCase suite + verified flag (20/24 True); BROAD_DOMAIN
    ├── agent_contracts.md     ✓ done — settled domain boundaries (ds ↔ mle, mle ↔ devops, de ↔ devops)
    ├── metrics.py             ✓ done — coverage, routing_precision, acceptance_rate, output_fidelity
    ├── run_logger.py          ✓ done — read-only per-run feature row → eval_runs/<date>.jsonl
    ├── EVAL_REFERENCE.md      ✓ done — per-case + per-metric correctness review
    ├── suite_notes.md         ✓ done — how to read aggregate scores
    └── training_eval_plan.md  ✓ done — measure→train reframe (router-first)
constitution.md             ✓ done
README.md                   ✓ done
CLAUDE.md                   ✓ done
main.py                     ✓ done — six agents + supervisor + cased log_run (drives bd-03)
.gitignore                  ✓ done — ignores *.txt, traces/, eval_runs/
pyproject.toml              ✓ done — + numpy, sentence-transformers
eval_runs/2026-06-04.jsonl  ✓ captured (gitignored) — 24-row baseline, one per case
.specs/eval_ml_plan.md      ✓ done — evaluation system design, D1–D8 settled
.specs/next-steps.md        ✓ done — session sequencing (S1–S3 done, S3.5 reframe inserted)
                            ← next: prompt-fix re-baseline control (Session 3.5)
```

---

## Principles

- We go slow. One concept at a time.
- We teach before we write.
- We test every step before moving on.
- We understand before we proceed.

---

*Warlock v0.1 — oathbreaker*
