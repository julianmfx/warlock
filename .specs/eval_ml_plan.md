# Eval ML Plan — From Heuristic Rubric to Learned Classifier

**Status:** proposed — awaiting agreement. Once agreed, we start *today* with Step 1 only (logging every run).

**Goal:** evaluate a Warlock run end-to-end — take an input, judge whether the *process* and the *output* are correct — and have that judgment **improve from data** rather than from hand-tuned constants.

---

## 0. The honest framing

What we designed first is a **heuristic scoring function** wearing a softmax costume:

- Four metrics `[C, R, A, F]` → centroid-distance logits → softmax → `{excellent, acceptable, poor}`.
- The centroids, the temperature `γ`, and the equal metric weights are **typed in by hand**, not estimated.
- So `P(excellent) = 0.91` does **not** mean "91% of runs like this are excellent." It means "`x` landed near a point we declared excellent." The probability is decorative.

That is a fine **v0 bootstrap** to get signal where we have none. It becomes real ML when **exactly one thing changes**: the parameters are *learned from labeled runs* instead of guessed. Everything else — the metrics, the feature vector, the softmax — we keep. A softmax classifier *is* multinomial logistic regression; we are only swapping hand-set centroids for learned weights `W, b`.

```
zₖ = -γ‖x - μₖ‖²        →        zₖ = Wₖ·x + bₖ
(heuristic, hand-set)             (learned via cross-entropy on labels)
```

**The single hard constraint: you cannot do ML without labels.** So the first build is not a model — it is the data pipeline that produces `(x, y)` pairs. Logging that data starts today; everything else is standard machinery once the data exists.

---

## 1. Codebase grounding (what actually exists)

Verified against `warlock/memory.py`, `orchestrator.py`, `supervisor.py`, `trace_logger.py`.

**Memory keys present after a run:**

| Key | Shape | Source |
|---|---|---|
| `problem_statement` | `str` | orchestrator |
| `task_decomposition` | `list[{"domain": str, "task": str}]` | orchestrator |
| `agent_outputs` | `dict[domain → output_str]` | each agent |
| `validation_results` | `dict[domain → {"accepted": bool, "reason": str}]` | supervisor |
| `token_spend` | `dict[agent → {input, output, cache_read}]` | all |
| `timing` | `dict[agent → seconds]` | orchestrator |

**Two corrections to the original metric draft (it referenced things that don't exist):**

1. **There is no `synthesis` key.** `Orchestrator.run()` ends after the agent loop — nothing synthesizes a unified output. F is therefore computed over agent outputs, not a synthesis (see D1).
2. **Acceptance is not in `agent_outputs`.** It lives in `validation_results[domain]["accepted"]`. The metric A must read from there.

**A per-run logger already exists.** `TraceLogger` writes one JSONL line *per (agent, task)* to `traces/<date>/<run_id>.jsonl`. Step 1 **extends** this idea into a per-run feature+label record — it does not replace it. TraceLogger = per-task forensic trace; the new run-logger = per-run feature row. Different grain, different purpose.

---

## 2. The feature vector — three honest axes

For one run, `x = [C, R, A, F] ∈ [0,1]⁴`. Each feature is tagged by **what it honestly measures** (see D5). Features *predict* quality; they are not quality itself — the ground truth is the label `y`.

### Process-conformance: did the orchestrator route correctly?

Both C and R compare the orchestrator's `task_decomposition` against `expected_domains` — defined per problem as the **minimal sufficient set of domains this problem needs** (D2). They are the **only** two features needing a case; both go `null` for uncased runs (D7). **Not all problems need all domains.** A simple problem may legitimately need a single domain; routing it there *and nowhere else* is a perfect run. Coverage of the full 6-domain roster is **never** a goal — breadth earns nothing.

So routing is a set-matching problem with two sides:

**C — Coverage = routing recall**
```
C = |D_invoked ∩ D_needed| / |D_needed|
D_invoked = {t["domain"] for t in task_decomposition}
```
Catches *misses* — a needed domain that was never invoked.

**R — Routing precision**
```
R = |D_invoked ∩ D_needed| / |D_invoked|
```
Catches *extras* — invoking domains the problem doesn't need. **R is what stops the orchestrator from throwing every domain at a one-domain problem.**

Worked example, problem needs only `{analytics}`:

| Run routes to | C | R | Reading |
|---|---|---|---|
| `{analytics}` | 1.0 | 1.0 | Perfect — correct narrow routing |
| `{analytics, ml_engineer, devops}` | 1.0 | 0.33 | Over-routed — R punishes it |
| `{devops}` | 0.0 | 0.0 | Mis-routed — C catches the miss |

Both are **necessary-not-sufficient**: a run can score C = R = 1.0 and still produce garbage. They gate; they don't certify quality. `clf.coef_` will later show empirically how much they predict the label, and whether R is redundant with C.

### Self-report (suspect): the Supervisor's own verdict

**A — Acceptance rate** — read from `validation_results`:
```
A = (1/n) Σᵢ 𝟙[ validation_results[domainᵢ]["accepted"] ]
```
⚠️ A is the LLM grading its own team's output. A sycophantic Supervisor inflates A directly. We do **not** hand-weight it down — the learned `W` decides empirically whether A carries signal. If its coefficient shrinks toward zero, the data confirmed the suspicion.

### Output-relevance (the load-bearing axis): does the output address the problem?

**F — Output fidelity = embedding cosine similarity.** See D1 for why keyword recall is rejected.
```
F = mean_i [ cos( embed(task_decomposition[i].task), embed(agent_outputs[i]) ) ]
```
Honesty caveat: cosine similarity measures *relevance / topicality*, not *correctness*. On-topic ≠ right. F is the best **cheap, automatic** quality proxy; the actual ground truth is the label `y`. F's job is to be the one feature *grounded in the output text* — without it, the feature set can only ever learn a process-conformance detector (D5).

---

## 3. Open decisions

### D1 — F is embedding cosine similarity, computed Day-1 *(decided)*
Keyword-substring recall is rejected for **two** reasons:
1. **Gameable** — "model" matches "remodel," "models"; a synthesis that name-drops keywords without solving anything scores high.
2. **Length bias (fatal)** — concatenating N agent outputs means more text → more keyword hits → F rises with the *number of agents invoked* → **F gets contaminated by C through sheer text volume.** That makes it partly re-measure coverage, not relevance.

Fix: F = the **mean of per-agent cosine similarities** between each agent's *assigned task* (`task_decomposition[i].task`) and that agent's output (average per-output similarities; do **not** concatenate). Measuring each output against its own assigned task — rather than against the whole problem — is a sharper per-agent relevance signal: it asks "did this agent answer the task it was given?", which a single broad problem embedding would blur across agents. Magnitude-normalized, so it's length-invariant and needs no synthesis step. **Embedding-F is a Step 1 requirement, not a later upgrade** — it is the only output-grounded feature, so without it the Day-1 dataset has no honest quality axis.

**Embedding source: `sentence-transformers`, local *(decided)*.** No API key, no second vendor, free to run on every row — the Anthropic API has no embeddings endpoint, so this avoids adding one. Default model `all-MiniLM-L6-v2` (384-dim, small, fast, general-purpose); revisit only if relevance signal proves too coarse. Cost: one new dependency (`uv add sentence-transformers`) + a one-time model download. Wrap it behind a small `embed(text) -> list[float]` seam in `metrics.py` so the provider stays swappable.

### D2 — `expected_domains` is the *minimal sufficient* set per problem *(decided)*
Whoever authors an eval case writes the minimal set of domains the problem genuinely needs — which **may be one**. Not a maximal wishlist. Authored by someone *other than* the routing logic, or C and R become circular (measuring the system against its own expectations). A single-domain problem's expected set has one entry, and a run is excellent if it routes there and nowhere else. Inclusion test per domain: *"if this domain were missing, would the problem be unsolved?"* — yes → in, enhancement → out. Each case carries per-domain reasoning comments so the ground truth is auditable and challengeable.

### D6 — Case source: a curated eval suite *(decided)*
The source of **cased** rows (complete `[C, R, A, F]`) is a fixed, hand-authored suite of **15–30 cases** in `cases.py`. The suite spans routing width: ~6 single-domain (one per domain), ~12 two-to-three-domain, ~4 broad (4+). Each domain appears as *needed* in several cases and *not-needed* in others, so R has over-routing to catch. **Ground truth is human-owned:** the suite is drafted with per-domain reasoning, then reviewed/corrected by a human who is not the routing logic. (Uncased runs are still logged — see D7 — so the suite is the source of *complete* rows, not the only source of rows.)

### D7 — No-case runs: log every run, null only what's truly uncomputable *(decided)*
"Log every run" is literally true. A run with no case still produced real, expensive, irreproducible data — and three of four signals don't need a case:
- **A** — from `validation_results` only. Computed always.
- **F** — cosine of each output vs. its *assigned task* (from `task_decomposition` in memory, not the case). Computed always.
- **C, R** — the *only* two needing `expected_domains`. These go `null` when no case exists.

So an uncased run blanks exactly two fields, not the row. The row carries an explicit **`has_case: bool`** so the absence is queryable and never silently coerced to `0.0` (which would poison Step 3). Consumers filter: `has_case == true` is the trainable set for any C/R model; *all* rows are the corpus for A/F-only analysis and for labeling. **Never let `null` carry meaning alone — pair it with the flag.**

Payoff: the label budget (Step 2) is no longer gated by the case budget — the LLM-judge reads `problem + raw_outputs` and never touches C/R, so an uncased run is fully labelable. Cost: dataset heterogeneity (two row types); mild, since C/R models filter on `has_case` anyway.

### D8 — Storage: gitignore the dataset *(decided)*
`eval_runs/` is **gitignored**, not committed. `raw_outputs` holds every agent's full text; keeping it out of git avoids sensitive input landing permanently in history (painful to scrub) and follows the ML convention that datasets don't live in source control. Commit only `cases.py` (the inputs); the cased portion of the dataset is regenerable from cases + code, and the dataset itself lives locally / in external storage later.

### D3 — Labeling source for `y`
LLM-as-judge for bulk + human-verified sample (Step 2). The judge reads the **raw output text only, never `[C,R,A,F]`** — otherwise it re-derives our heuristic and the labels are circular.

### D4 — Label vocabulary
`{excellent, acceptable, poor}`.

### D5 — Every feature is tagged by axis; the set must contain ≥1 output-grounded feature *(decided)*
The honest taxonomy is three axes plus the label:

| Axis | Features | Honestly measures | Trust |
|---|---|---|---|
| **Process-conformance** | C, R | Did the orchestrator route as expected? | Gating; necessary-not-sufficient |
| **Output-relevance** | F | Is the output on-topic for the problem? | The load-bearing output-grounded signal |
| **Self-report** | A | Supervisor's own verdict | Suspect; `W` audits it |
| **Ground-truth quality** | `y` (label) | Is the run actually good? | What we predict — *not a feature* |

**Rule:** the feature set must contain at least one output-grounded feature (currently F), or the model can only learn a process-conformance detector — it cannot recover quality signal the features never captured. This is why F is non-negotiable and Day-1.

---

## 4. Step-by-step roadmap

### Step 1 — Log every run as a feature+label-ready record  ← **START TODAY**
**Goal:** every run appends one row. Cased run:
`(run_id, timestamp, problem, C, R, A, F, has_case=true, raw_outputs, label=null)`.
Uncased run: same shape with `C=null, R=null, has_case=false` — A and F still computed (D7).

- `warlock/eval/metrics.py`: pure functions `coverage`, `routing_precision`, `acceptance_rate`, `output_fidelity` reading the **real** memory keys above. `output_fidelity` calls the embedding model (D1); `coverage`/`routing_precision` take `expected_domains` and return `None` when it's absent.
- `warlock/eval/run_logger.py`: after a run, reads memory, computes A and F always, computes C and R only if a case is supplied, sets `has_case`, writes one JSON line to `eval_runs/<date>.jsonl`. `label` starts `null` (filled in Step 2). Store raw outputs too, so features are re-computable if a metric definition changes (and so C/R can be backfilled if a case is authored later).
- `warlock/eval/cases.py`: `expected_domains` (minimal set, D2) + per-problem text per eval case.
- Add `eval_runs/` to `.gitignore` before the first row is written (D8).
- **Verify:** run on 2–3 problems → confirm `eval_runs/*.jsonl` has in-range `[A,F]` on every row; a **cased single-domain** problem scores `C=R=1.0` when routed correctly with `has_case=true`; an **uncased** run produces `C=R=null, has_case=false` with A/F populated and in range; raw outputs captured; `label` is `null`.

### Step 2 — Collect labels (`y`)
- LLM-as-judge reads `problem + raw_outputs` (never the metrics, D3) → `{excellent, acceptable, poor}`. Backfills `label`.
- Human-verify a random ~100. If judge agrees with humans ≥ ~85%, trust it for bulk.
- Target ~150–300 labeled rows (4 features → no need for thousands).
- **Verify:** labeled dataset with a measured judge-vs-human agreement rate.

### Step 3 — Train multinomial logistic regression
```python
from sklearn.linear_model import LogisticRegression
clf = LogisticRegression(multi_class="multinomial", max_iter=1000).fit(X_train, y_train)
```
- `clf.coef_` *is* the learned `W` — reading it tells us which metrics actually predict quality (auto-solves the "uniform weighting" assumption, exposes whether A self-grading and R routing carry signal).
- Start linear, not a neural net: 4 features + a few hundred rows → logistic regression wins on accuracy, interpretability, calibration. Revisit gradient boosting only with many more features and thousands of rows.
- **Verify:** model trains; coefficients printed and sanity-checked against the axis taxonomy.

### Step 4 — Split honestly + meta-evaluate
```python
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)
```
- Never touch `X_test` until the end. Prefer k-fold CV for small data.
- Inspect `classification_report` + `confusion_matrix`. excellent↔acceptable confusion is forgivable; excellent↔poor is a serious failure.
- **Verify:** held-out metrics reported; confusion matrix reviewed.

### Step 5 — Calibrate + abstain
```python
from sklearn.calibration import CalibratedClassifierCV
calibrated = CalibratedClassifierCV(clf, method="isotonic", cv=5).fit(X_train, y_train)
```
- Reliability diagram (predicted prob vs. actual frequency; well-calibrated sits on the diagonal).
- **Abstain / off-distribution branch:** if `x` is far from all training data or the max class probability is below a threshold, return *no verdict* instead of a confident misclassification. Fixes the degenerate-run failure the heuristic hides.
- **Verify:** reliability diagram near-diagonal; degenerate input triggers abstain.

### Step 6 — Close the loop (what makes it a *process*)
```
new runs → compute [C,R,A,F] + predict → sample some for labeling
        → append (x,y) → retrain + re-evaluate on fresh held-out set
        → promote new model only if metrics improved → repeat
```
- **Verify:** a second training round on accumulated data measurably matches/beats the first.

---

## 5. Proposed file layout
```
warlock/eval/
  metrics.py      # C, R, A, F — pure functions over memory keys; F calls embeddings (Step 1)
  run_logger.py   # per-run feature row → eval_runs/<date>.jsonl (Step 1)
  cases.py        # expected_domains (minimal set) + problem text per case (Step 1, D2)
  label.py        # LLM-as-judge backfill (Step 2)
  train.py        # split, fit, evaluate, calibrate, persist model (Steps 3–5)
eval_runs/        # JSONL feature+label dataset
```

---

## 6. What we do today

**Step 1 only.** Build `metrics.py` + `run_logger.py` + `cases.py` (including embedding-F per D1), wire the logger into a run, and confirm `eval_runs/*.jsonl` fills with correct `[C,R,A,F]` + raw outputs + `label=null`. No model, no labels yet — just the data pipeline that makes all later steps possible.
