# Warlock — Build Plan
> *An oathbreaker. A multi-agent platform that resolves problems and creates new realities.*

---

## Vision

Warlock is a multi-agent AI platform operating in the Data & AI domain. It receives a raw problem, decomposes it, routes work to specialist agents, and synthesizes a unified output — a new reality better than any single model could produce alone.

---

## Architecture

Warlock uses a **triangle architecture** with three equal peers and no single point of authority.

```
        Orchestrator
           /    \
          /      \
    Supervisor — Agents
```

Any corner can reject, push back, or validate another. A decision is confirmed only when all three agree. The final output is an emergent result of consensus — no single corner owns it.

---

### Corner 1 — Orchestrator
`warlock/orchestrator.py`

Responsibilities:
- Receive the raw problem statement
- Decompose it into sub-tasks
- Decide which agents run and in what order
- Write decomposition into shared memory
- Participate in triangle consensus — can reject Supervisor validations or agent outputs

---

### Corner 2 — Supervisor
`warlock/supervisor.py`

Responsibilities:
- Validate agent outputs for quality and domain correctness
- Challenge Orchestrator decompositions that seem wrong or incomplete
- Flag low-confidence outputs back to the triangle for re-evaluation
- Participate in triangle consensus — can reject any decision from either corner

---

### Corner 3 — Specialist Agents
`warlock/agents/`

Each agent owns exactly one domain. No agent crosses into another's territory.

| Agent | Domain | Responsibilities |
|---|---|---|
| `data_engineer` | Data Engineering | Pipelines, ingestion, transformation, warehousing |
| `ml_engineer` | Machine Learning | Model design, training, evaluation, deployment |
| `analytics` | Analytics | EDA, metrics, dashboards, KPIs, recurring reports, insight generation |
| `devops_mlops` | DevOps / MLOps | Infra, CI/CD, model serving, monitoring |
| `data_scientist` | Data Science | Problem formulation, experimentation, statistical inference, causal analysis |
| `software_dev` | Software Development | APIs, services, integrations, tooling |

Note: `bi_agent` was merged into `analytics` — the BI domain (KPIs, dashboards, recurring reports) is now owned by the analytics agent, which handles both discovery and monitoring.

Agents can flag uncertainty or disagreement instead of running silently. This triggers the triangle.

---

### Shared Memory
`warlock/memory.py`

A key-value context store that all corners read from and write to. The only communication bus.

| Key | Description |
|---|---|
| `problem_statement` | The original raw input |
| `task_decomposition` | The orchestrator's breakdown of sub-tasks |
| `agent_outputs` | Results written by each specialist agent |
| `consensus` | Current agreement state across the triangle |
| `iteration` | Current loop count |
| `confidence` | Confidence score of the final output (0.0–1.0) |

---

### Triangle Activation

The triangle activates on:
- Agent uncertainty or low-confidence output
- Inter-agent conflict
- Explicit rejection by any corner

**Escape valve:** after 3 iterations without full consensus, Warlock emits the best-effort output tagged with a confidence score. It does not pretend to have reached full agreement.

---

## Build Sequence

### Phase 1 — Core (done)
- [x] Shared `Memory` layer — key-value context object agents read/write during a run
- [x] Base `Agent` class — interface every specialist agent inherits from
- [x] `run(task)` on base `Agent` — live Claude API call with prompt caching, writes to `agent_outputs`
- [x] `LLMClient` Protocol — provider-agnostic abstraction layer
- [x] `AnthropicClient` adapter — first provider implementation

### Phase 2 — First Agent + Orchestrator (done)
- [x] `data_engineer` agent — production-grade system prompt, model passed by caller
- [x] `Orchestrator` class — problem decomposition via LLM, agent registry, routing engine
- [x] Agent registration: `data_engineer` registered into the Orchestrator
- [x] End-to-end test: problem → orchestrator → `data_engineer` → memory → output

### Phase 3 — Full Agent Fleet (done)
- [x] `ml_engineer` agent — production-grade ROLE with experimentation discipline, pushback handling, ethical risk surfacing
- [x] `analytics` agent — absorbs BI domain; owns EDA, metrics, dashboards, KPIs, and recurring reports
- [x] `devops_mlops` agent — incident response, DR vs. incident distinction, SLA/SLO/SLI, error budgets, boring technology principle
- [x] `data_scientist` agent — added this session; owns problem formulation, causal inference, experimentation, statistical methodology
- [x] `software_dev` agent — interface-first philosophy, contract testing, distributed systems failure modes, DB hazards
- [x] `bi_agent` removed — domain merged into `analytics`

### Phase 4 — Triangle
- [x] `Supervisor` class — validates outputs, challenges decompositions, participates in consensus
- [ ] Triangle consensus loop — any corner can reject or push back, decision confirmed on agreement
- [ ] Escape valve — after 3 iterations emit best-effort output with confidence score
- [ ] Multi-agent run: all agents in parallel, triangle converges outputs

#### Known issues fixed

- **P0 ✓** — Capture `validate()` return value and retry agent once on rejection.
- **P1 ✓** — Guard `cache_read_tokens` with `or 0` before accumulating in both supervisor and orchestrator.
- **P2 ✓** — Orchestrator token tracking now accumulates via `current_tokens` pattern instead of overwriting.
- **P3 ✓** — `temperature=0` on supervisor calls; `LLMClient.complete()` signature updated to accept `temperature`.

#### Consensus loop design notes

- On retry, the rejection **reason** must be passed back to the agent as context — blind retries produce the same output.
- Agents asking clarifying questions is valid professional behavior — but only works when there is a user in the loop to answer them. Until Phase 5 (conversational loop), the supervisor correctly rejects this because there is no mechanism to resolve the questions. When Phase 5 ships, update supervisor acceptance criteria to allow clarifying questions.
- The trace logger (`warlock/trace_logger.py`) captures every validation event to disk — this data is the foundation for future fine-tuning of a cheaper supervisor model.

### Phase 5 — Platform
- [ ] CLI interface to submit problems to Warlock
- [ ] Conversational loop — agents can emit clarifying questions through memory, orchestrator surfaces them to the user, waits for input, re-routes with the answer
- [ ] FastAPI web UI — local interface to submit problems, see agent outputs rendered, follow the conversation
- [ ] Docker — containerized local run, no Python or uv setup required
- [ ] Logging and observability per agent
- [ ] Iterative runs (agents can loop until output is accepted)

### Phase 6 — Deployment
- [ ] EC2 deployment — production server running Warlock on demand
- [ ] NAS / local notebook deployment — always-on local server, triggered when needed
- [ ] Environment config — API keys, model selection, and memory backend configurable per deployment target

---

## Evaluation Track (parallel to Phases 4–6)

Designed in full in `.specs/eval_ml_plan.md`. Measures whether a run's *process* and *output* are correct, and evolves from a hand-tuned heuristic into a learned classifier as labeled runs accumulate.

- Per-run feature vector `x = [C, R, A, F]`: **C** coverage (routing recall), **R** routing precision, **A** supervisor acceptance rate, **F** output relevance (sentence-transformers cosine, each agent's assigned task vs. its output, averaged).
- Three honest feature axes — process-conformance (C, R), self-report (A), output-relevance (F) — plus the ground-truth label `y ∈ {excellent, acceptable, poor}`. Rule: the set must contain ≥1 output-grounded feature (F).
- Decisions **D1–D8** settled (embedding source, minimal-domain ground truth, label source, taxonomy, curated 15–30 case suite, log-every-run with `has_case` flag + null-only-C/R, gitignored dataset).

Session sequencing for both this track and the Phase 4 consensus loop lives in `.specs/next-steps.md` (measure-before-improve: build the logger, capture a baseline, then prove the consensus loop moves it).

Steps:
- [ ] **Step 1 — log every run** → `warlock/eval/{metrics,run_logger,cases}.py`, embedding-F, `eval_runs/<date>.jsonl` (gitignored).
  - [x] Curated case suite drafted **and reviewed** — `warlock/eval/cases.py`, 24 `EvalCase` entries (6 single-domain, 15 two-to-three-domain, 3 broad), each with minimal `expected_domains` and per-domain inclusion/exclusion reasoning (D6). An `EvalCase.verified: bool` flag was added; 20 of 24 cases are `verified=True` after the review pass (md-15, bd-01, bd-02, bd-03 still pending). The review (`warlock/eval/EVAL_REFERENCE.md`) found 23/24 cases sound; the one real fix (sd-02 view/semantic-layer ownership → analytics) is applied, and the suite-level lifecycle-ownership rule (`warlock/eval/suite_notes.md` §1) now backs the exclusion notes.
  - [x] Domain-boundary disputes surfaced by cases recorded in `warlock/eval/agent_contracts.md` — three entries: data_scientist ↔ ml_engineer (research vs. production cycle; handoff = a production artifact), ml_engineer ↔ devops_mlops (model vs. infra monitoring), data_engineer ↔ devops_mlops (dbt project readiness vs. workflow files; from md-15).
  - [x] Build the logger — `metrics.py` (`coverage`, `routing_precision`, `acceptance_rate`, `output_fidelity` over real memory keys; embedding-F via the `_embedding()` seam using `all-MiniLM-L6-v2`), `run_logger.py` (read-only observer; A/F always, C/R only with a case, `has_case` flag, `iteration` count, append to `eval_runs/<date>.jsonl`, `label=null`). `log_run(m)` wired into `main.py`. Deps added: `numpy`, `sentence-transformers`.
  - [x] **Capture the baseline** (Session 3) — the full 24-case suite ran through today's orchestrator; `eval_runs/2026-06-04.jsonl` holds 24 rows (one per case). Doubled as the Step-1 verify gate. **Findings:** `Coverage = 1.0` on all 24 (the orchestrator never *missed* a needed domain — zero recall variance); `Routing` spans 0.33–1.0; `acceptance_rate` and `output_fidelity` do not track scope. Full per-case + per-metric review in `warlock/eval/EVAL_REFERENCE.md` and `warlock/eval/suite_notes.md`.
  - [x] **Prompt-fix re-baseline control** (Session 3.5, step 1) — loaded a domain-ownership charter + the `agent_contracts.md` boundary rules into `Orchestrator.decompose` and set `temperature=0`; re-ran the 24-case suite (routing-only), recorded `eval_runs/2026-06-07.jsonl`. **Routing precision improved on ~15/24 cases** vs `2026-06-04`, 8 flat, **one stable regression** (md-12 — a build-a-tool case where the model invents a devops_mlops CI/CD task + a data_engineer SQL task). A precision-tightening "scope discipline" prompt line was tried and **reverted** (didn't heal md-12, broke md-15). Built **`assignment_accuracy`** (per-deliverable task→domain match) and authored **`gold_decomposition` for bd-01** (its `Assignment` rose 0.86→1.0 after the fix). **Finding:** single-sample `temperature=0` decompositions vary at the ±1-task level (md-03 flipped run-to-run), so trustworthy per-case deltas need N samples — answers `training_eval_plan.md` §5.4.

**Track reframed (this session): measure → train.** The objective shifted from *measuring* a run to *training a small LLM* — the **router (orchestrator) first**. The training-oriented plan is `warlock/eval/training_eval_plan.md`. Key consequences: a reward is optimized against, so the bar is higher than for a metric — `acceptance_rate` (inverts against scope) and `output_fidelity` (rewards parroting) are unsafe as rewards; `coverage` has zero variance so recall is untrained; `EvalCase` needs a per-example **`gold_decomposition`** target (a set cannot supervise a sequence model); and the orchestrator currently routes blind (no boundary rules, no `temperature=0` in its prompt). `eval_ml_plan.md`'s D1–D8 classifier still stands — it becomes the **reward model**, distinct from the router task-LLM. The prompt-fix re-baseline control is now **captured** (domain charter + `agent_contracts.md` boundary rules + `temperature=0` in `Orchestrator.decompose`; ~15/24 cases improved on `Routing`, recorded in `eval_runs/2026-06-07.jsonl`), **`assignment_accuracy` is built**, and **`gold_decomposition` is authored for bd-01** (`Assignment` 0.86→1.0). The next actions are extending `gold_decomposition` to the remaining discriminating cases (md-12 — the one stable regression — bd-02, bd-03, md-13) and **N-sampling the baseline** to clear the `temperature=0` single-sample noise.
- [ ] Step 2 — label runs (LLM-judge bulk + human-verified sample)
- [ ] Step 3 — train multinomial logistic regression; read `clf.coef_`
- [ ] Step 4 — honest split + confusion matrix
- [ ] Step 5 — calibrate + abstain branch
- [ ] Step 6 — retraining loop

---

## Spec Review Protocol

Every time progress is made on this project — after any phase step, agent build, or architectural decision — do the following:

1. **Review** all files in `.specs/` to check for outdated information
2. **Update** `plan.md` to reflect completed steps, revised phases, and any changed design decisions
3. **Update** `warlock_session.md` with the current state: what was just built, what's next, and any lessons learned
4. **Analyze** what the next step now requires given what was just shipped — do not design ahead, adjust only based on what was just learned

This keeps `.specs/` as the living source of truth for the project state.

---

## Principles

- **One agent, one domain.** No agent crosses boundaries.
- **Memory is the bus.** Agents collaborate through shared memory and the triangle consensus loop — never through direct calls.
- **The triangle owns truth.** Orchestrator, Supervisor, and Agents are equal peers — any corner can reject or push back. The final output is an emergent result of consensus. After 3 iterations without consensus, Warlock emits the best-effort output with a confidence score.
- **Oathbreaker mindset.** Warlock does not default to what exists. It builds what should exist.
- **Cost discipline.** Every agent call must justify its token spend. Use the cheapest model that can do the job (e.g. Haiku for routing/classification, Sonnet for reasoning, Opus only when depth demands it). Cache aggressively with prompt caching. Measure cost per run.
- **Learn by doing.** Ship the simplest working version first, then iterate. Don't design the full system before writing any code. Each phase should produce something runnable that teaches you what the next phase actually needs.

---

## Stack (proposed)

- Language: Python
- Agent framework: custom (no LangChain dependency at core)
- LLM backend: provider-agnostic via `LLMClient` Protocol — `AnthropicClient` ships first
- Memory: in-process dict → upgrade to Redis or vector store as needed
- Serving: FastAPI (Phase 5)

---

*v0.1 — oathbreaker*
