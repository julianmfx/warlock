# Warlock — Next Steps
> *The order of work across the coming sessions, and how each step is proven.*

This document sequences the two open tracks — the **eval pipeline** (`eval_ml_plan.md`, D1–D8) and the **Phase 4 consensus loop** (`plan.md`) — and defines the test that closes each step. It is the session-planning source of truth: each session below is sized to be startable cold and finishable in one sitting.

---

## The guiding principle

**Measure before you improve.** The consensus loop exists to produce *better* outputs. A quality-improvement mechanism built without a quality measurement is unfalsifiable — you cannot tell if it helped, regressed, or just burned 3× the tokens for the same answer. So the eval logger is built *first*, used to capture a **baseline** of today's behavior, and the consensus loop is then proven by moving that baseline.

This is the Goal-Driven principle from `CLAUDE.md` applied at the project scale: *define the success metric, then make the number go up.*

---

## How the two tracks synchronize

Neither track blocks the other's *construction* — both read only what already lives in memory. They are coupled by **measurement**, at three touch points:

1. **Acceptance rate `A` + iteration count (now).** Today `validation_results` holds one verdict per agent. The consensus loop turns `A` into "accepted after up to 3 iterations" and adds a meaningful retry count. → The eval row is built **forward-compatible**: it logs the run's iteration/retry count from day one (0-or-1 today), so the *same* logger captures the richer signal once the loop lands, and baseline-vs-after stays apples-to-apples.
2. **Trace-logger completeness (loop side).** `TraceLogger` records only iteration 0 today. The consensus loop closes that gap by logging every iteration. Per-task forensic trace and per-run eval feature row get richer together.
3. **Confidence score (the long-term fusion).** The escape valve will first emit a hand-set `confidence: low` tag. Once the eval *classifier* is trained (eval Step 3+), its `P(excellent/acceptable/poor)` becomes a better confidence signal and can **replace** the hand-set tag. At that point eval stops being a measuring tape and becomes part of the consensus mechanism itself. This is the endpoint where the two tracks merge.

---

## The ordered sequence

### Session 1 — Draft the curated eval suite
**Goal:** produce the human-owned ground truth the eval logger measures against (D2, D6).
**Do:** draft 15–30 `EvalCase` entries spanning routing width (~6 single-domain, ~12 two-to-three-domain, ~4 broad). Each carries `id`, `problem`, minimal `expected_domains`, and **per-domain reasoning comments** — including *why* each excluded domain is excluded (so the over-routing cases that exercise R are explicit). Each domain appears as *needed* in several cases and *not-needed* in others.
**Division of labor:** Claude drafts with reasoning; the human reviews and corrects the domain sets. Ground truth must not be decreed by the routing logic.
**Verify / done when:** the human has reviewed and corrected every case; the set is saved as `warlock/eval/cases.py`; it is the only eval file committed to git (D8).

### Session 2 — Build eval Step 1 (the logger)
**Goal:** every run appends one feature+label-ready row. Read-only observer; never writes back to the bus.
**Do:**
- `uv add sentence-transformers`.
- `warlock/eval/metrics.py` — `coverage`, `routing_precision`, `acceptance_rate`, `output_fidelity` over the real memory keys (`task_decomposition`, `validation_results`, `agent_outputs`). `output_fidelity` calls an `embed()` seam (`all-MiniLM-L6-v2`); `coverage`/`routing_precision` return `None` when `expected_domains` is absent.
- `warlock/eval/run_logger.py` — after a run: compute A and F always; C and R only if a case is supplied; set `has_case`; **capture iteration/retry count (forward-compat, touch point 1)**; append one JSON line to `eval_runs/<date>.jsonl`; `label=null`.
**Verify / done when (the gate from `eval_ml_plan.md`):**
- every row has in-range `[A, F]`;
- a **cased single-domain** problem routed correctly scores `C=R=1.0`, `has_case=true`;
- an **uncased** run gives `C=R=null`, `has_case=false`, with A/F populated and in range;
- raw outputs captured; `label=null`;
- a hand-check of one row's arithmetic matches.

### Session 3 — Capture the baseline ✅ done
**Goal:** a measured snapshot of **today's** orchestrator (single blind retry) before the consensus loop changes anything.
**Done:** the full 24-case suite ran through the current `main.py`/orchestrator; `eval_runs/2026-06-04.jsonl` holds 24 rows (one per case). The verify gate passed (broad cases `R < 1`, single-domain `C=R=1.0`, A/F in range, raw outputs captured, `label=null`). **Findings:** `Coverage = 1.0` on all 24 (no recall variance), `Routing` spans 0.33–1.0, and `acceptance_rate`/`output_fidelity` were shown not to track scope (full review: `warlock/eval/EVAL_REFERENCE.md`, `warlock/eval/suite_notes.md`).

### Session 3.5 — Track reframed: measure → train (the new control)
**What changed:** the eval's purpose shifted from *measuring* a run to *training a small LLM* — the **router (orchestrator) first** (`warlock/eval/training_eval_plan.md`). A training signal is optimized against, so the bar rises: `acceptance_rate` and `output_fidelity` are unsafe as rewards, `coverage` has zero variance (recall untrained), and the suite has no per-example target.
**Goal:** the honest control any fine-tune must beat, captured *before* any model is trained — the "measure before you improve" principle applied to training.
**Do (priority order from `training_eval_plan.md` §10, ahead of the consensus loop):**
1. Load the boundary rules (`agent_contracts.md`, the suite-level ownership rule) into `Orchestrator.decompose`'s prompt and set `temperature=0`; re-run the suite and re-baseline. Cheapest possible win; the control any later fine-tune is measured against.
2. Add `gold_decomposition` (`[{deliverable, domain}]`) to the discriminating cases (bd-01/02/03, md-13, boundary md-\*) and an `assignment_accuracy` metric — catches the drift→devops misassignment that set-based `routing_precision` misses, and is the SFT target.
3. Make `acceptance_rate` scope-aware (Fix A: domain ∉ `expected_domains` ⇒ rejected, a post-hoc eval-layer override); fence `output_fidelity` out of any reward.
4. Author under-routing / hard-negative cases so `coverage` gains variance.
**Verify / done when:** the prompt-fix suite re-run is recorded next to the 2026-06-04 baseline, with the delta on `Routing` (and `assignment_accuracy`, once it exists) reported. The consensus loop (Session 4) and the eval-classifier roadmap continue independently; the classifier becomes the **reward model**, distinct from the router task-LLM.

### Session 4 — Build the consensus loop (Phase 4)
**Goal:** replace the single blind retry with a real reason-passing loop + escape valve.
**Do (per `plan.md` Phase 4):**
- Cap at 3 iterations per agent; pass the rejection **reason** back to the agent each retry (blind retries reproduce the same output).
- Log **every** iteration via `TraceLogger` (closes touch point 2).
- After 3 failed iterations, tag the output `confidence: low`, `consensus=partial`, and continue (escape valve).
**Verify / done when (functional tests):**
- a deliberately-rejected output triggers a retry **with the reason present** in the agent's next context;
- the iteration cap is enforced (never a 4th attempt);
- the escape valve fires on persistent rejection and tags `confidence: low` / `consensus=partial`;
- `TraceLogger` now shows iterations 1 and 2, not just 0.

### Session 5 — Re-measure: prove the loop earned its cost
**Goal:** the falsifiable test of whether the consensus loop helped.
**Do:** re-run the same suite through the new orchestrator; compare the new `eval_runs/` rows to the Session 3 baseline.
**Verify / done when (regression test against baseline):**
- **`A` rises** (fewer final rejections after reason-passing retries) — the primary expected effect;
- **`F` and labels hold or improve** — converged outputs are at least as relevant/good;
- **token cost is recorded** alongside the quality delta. If quality is flat while tokens ~3×, the loop is **not** earning its cost — and the eval makes that visible instead of hidden. That is a valid, valuable negative result, not a failure of the process.

### Beyond — eval Steps 2–6 and the fusion
Once the baseline/loop comparison is in hand, continue the eval roadmap from `eval_ml_plan.md`:
- **Step 2** — finish labeling to ~150–300 rows.
- **Step 3** — train multinomial logistic regression; read `clf.coef_` (learn whether C, R, A actually predict quality; A's coefficient audits the self-grading suspicion).
- **Step 4** — honest split + confusion matrix.
- **Step 5** — calibrate + abstain branch.
- **Step 6** — retraining loop.
- **Fusion (touch point 3):** wire the trained classifier's probability into the escape valve as the confidence score, replacing the hand-set `low` tag. The two tracks merge here.

---

## At-a-glance order and tests

| # | Session | Track | Done when |
|---|---|---|---|
| 1 | Draft eval suite | eval | ✅ Human-reviewed `cases.py` (`verified` flag) |
| 2 | Build logger | eval | ✅ Verify gate passed; rows correct & forward-compat |
| 3 | Capture baseline | eval | ✅ 24-row baseline captured (`eval_runs/2026-06-04.jsonl`) |
| 3.5 | Reframe: prompt-fix re-baseline + gold + N-sample (the control) | eval/train | ✅ steps 1–2 done — rules + `temperature=0`; `assignment_accuracy` now **embedding-based** (cosine ≥ 0.30, calibrated); gold for 5 cases (bd-01/02/03, md-12, md-13); N-sample baseline `eval_runs/nsample/2026-06-07.jsonl`. ← next: scope-aware `A` + under-routing cases; structural fix = deliverable-level `decompose` output |
| 4 | Consensus loop | Phase 4 | Reason passed, cap enforced, escape valve + iter-logging |
| 5 | Re-measure | both | A↑, F/labels hold-or-up, token cost vs. quality recorded |
| 6+ | Label → train → calibrate → fuse | eval | Classifier feeds the confidence score / router reward |

---

## Open items / decisions still to make

- **Iteration count as a feature vs. metadata.** Logged from Session 2 for forward-compat. Whether it becomes a 5th model feature (a process-conformance signal: how much retrying a run needed) is deferred until after Step 3 shows whether it predicts quality. Out of scope for D1–D8 as currently written.
- **Confidence calibration check.** Once labels exist, verify the escape valve's `confidence: low` tag actually correlates with worse `y`. If "low confidence" runs are not measurably worse, the tag is dishonest and needs rework — another thing eval makes testable.
- **Labeling depth for the baseline (Session 3).** Process-only baseline (`A`, `F`) is enough to start; label depth can grow over later sessions without blocking the consensus-loop comparison on `A`.
- **Agent clarification loop.** Agents may produce questions instead of deliverables; the orchestrator should surface these to the user, collect answers, and re-run the agent until satisfied. When this lands: (1) F and A must be computed on the final output only, not on intermediate question rounds; (2) `iteration` in the eval row should reflect real clarification round depth, not just supervisor retry count.

---

*Warlock v0.1 — oathbreaker*
