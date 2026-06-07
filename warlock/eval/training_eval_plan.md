# Training-Oriented Eval Plan — From Measurement to Training Signal

> *How to evolve the eval suite from a tool that **measures** a run into one that can
> **train** a small LLM to route and execute better.*
>
> Companion to `EVAL_REFERENCE.md` (per-case + per-metric correctness review) and
> `suite_notes.md` (how to read aggregate scores). Those two docs answer *"do the
> metrics measure routing quality?"* This doc answers a different, newer question:
> *"is the eval good enough to be a training signal for a small LLM?"* — and what has
> to change before the answer is yes.

---

## 1. Executive summary

The objective has shifted. The eval was built to **measure** one run end-to-end. The
new goal is to **train a small LLM that is better at the tasks the suite tests** —
primarily routing/decomposition, secondarily agent execution. That shift raises the bar
sharply, because a training signal is *optimized against*, and optimization pressure
exploits every flaw a measurement metric is allowed to have.

Five things must change before the suite can train a model:

1. **Pick the target.** Train the **router** (orchestrator) first. It is the task the
   suite already half-measures, its gold is authorable, and it is the highest-leverage
   single component.
2. **Author per-example targets.** Cases carry `expected_domains` (a *set*). You cannot
   supervise a sequence model on a set — you need a **gold decomposition**
   (`[{domain, task}]`) per case. This field does not exist yet.
3. **Quarantine the poison rewards.** `acceptance_rate` inverts against scope and
   `output_fidelity` rewards parroting. As *measurements* they are merely weak; as
   *rewards* they actively teach the wrong behavior. Fix or fence them before any
   training loop reads them.
4. **Add variance the suite lacks.** `Coverage` is `1.0` on all 24 baseline rows — zero
   variance. The suite cannot train or test recall (dropping a needed domain) because it
   contains no case where that is tempting.
5. **Fix the free baseline first.** The orchestrator prompt contains none of the boundary
   rules the cases test. Putting them in the prompt is the cheapest improvement and the
   honest control any fine-tune must beat.

The deepest single point: **the bar for a reward is higher than the bar for a metric.**
Everything below follows from that.

---

## 2. The bar changes — measurement vs. reward

A measurement metric is read by a human who applies judgment, discounts known confounds,
and cross-checks against the artifact. `EVAL_REFERENCE.md` is exactly that judgment layer:
it tells you *"acceptance agreed with routing here, but coincidentally — check the
rejection reason."* A human can hold that nuance.

A training signal has no human in the loop. Whatever scalar you optimize, the model drives
to its maximum by the cheapest available path — including the degenerate one. The
consequences for the four current metrics:

| Metric | Known measurement flaw (from existing docs) | What that flaw becomes under optimization |
|---|---|---|
| `coverage` | None — trustworthy | Useless gradient: it is `1.0` everywhere in the suite (§5.1) |
| `routing_precision` | Set-based; blind to task→domain assignment | **Reward-hackable toward under-routing** — drop domains → fewer "extras" → R rises |
| `acceptance_rate` | Inverts against scope; rewards out-of-scope work | **Teaches over-routing and scope violation directly** — the validator rewards exactly the wrong move (md-03/md-04 proof) |
| `output_fidelity` | Rewards prompt-echo, uncorrelated with quality | **Textbook reward hacking** — the model learns to parrot the task text; bd-01 (the only perfect run) already scores *lowest* fidelity |

This is why "the metrics are mostly fine, just read them carefully" (true for measurement)
does **not** carry over. Two of four are safe to optimize, one is inert, one is dangerous.

---

## 3. What to train, and why the router goes first

| Candidate target | Gold authorability | Signal quality today | Verdict |
|---|---|---|---|
| **Router** (orchestrator: `problem → [{domain, task}]`) | High — gold decomposition is hand-writable from the case notes | `coverage` + `routing_precision` already track it (set-level) | **Train first** |
| **Domain agents** (6 execution models) | Low — gold output text is expensive and subjective | `output_fidelity` is the *wrong* signal (rewards parroting) | Defer; needs a reference-based or judge-based signal first |
| **Supervisor** (validator/judge) | Medium | Training a judge on outputs it also grades is circular | Defer; treat as reward model, not task model (§8) |

The router is also where the suite's discriminating content already lives: every
boundary note, every exclusion rationale, the entire `agent_contracts.md` — all of it is
*routing* knowledge. The suite is, in effect, already a routing-training corpus that has
not been shaped into `(input, target)` pairs.

---

## 4. The blocker: cases have no per-example target

`EvalCase` fields today: `id, problem, expected_domains, notes, verified`. The only
machine-readable gold is `expected_domains` — an unordered set of domain strings.

For **supervised fine-tuning** of a router you need the target *output sequence*: which
deliverables exist, which domain each goes to, and ideally the task text. A set cannot
supply that. `EVAL_REFERENCE.md §10.2` already proposes `gold_assignments`
(`[{deliverable, domain}]`) for *scoring* the boundary distinctions; for *training* extend
it one step to the full gold decomposition:

```python
gold_decomposition = [
    {"deliverable": "train collaborative filtering model", "domain": "data_scientist"},
    {"deliverable": "package + serving integration",        "domain": "ml_engineer"},
    {"deliverable": "prediction drift monitoring",          "domain": "ml_engineer"},
    {"deliverable": "GET /recommendations/{user_id}",        "domain": "software_dev"},
    {"deliverable": "A/B traffic splitting",                 "domain": "devops_mlops"},
    {"deliverable": "CTR / conversion-lift dashboard",       "domain": "analytics"},
    {"deliverable": "clickstream ingestion pipeline",        "domain": "data_engineer"},
]
```

This one field does triple duty:

- **SFT target** — flatten to the orchestrator's JSON output shape and it is the
  supervised label.
- **`assignment_accuracy` score** — the per-deliverable metric that finally catches the
  drift→`devops_mlops` misassignment invisible to set-based routing (bd-01/02/03).
- **Dense reward** — per-decision correctness gives far more gradient than one
  set-level scalar per run.

Author it for the discriminating cases first (bd-01/02/03, md-13, and the boundary
md-\*), exactly the scope `EVAL_REFERENCE §10.2` recommends — not the whole suite.

---

## 5. Empirical findings from the baseline (`eval_runs/2026-06-04.jsonl`)

Read directly off the 24 captured rows, not inferred.

### 5.1 `Coverage` = 1.0 on all 24 cases → recall is untrained and untested

The orchestrator never missed a needed domain in the entire suite; its only failure mode
is over-routing (which is why `Routing` varies 0.33–1.0 while `Coverage` is flat). Two
consequences for training:

- **No gradient on recall.** A model trained against this suite is never penalized for
  dropping a needed domain, because no case makes dropping one tempting.
- **The most dangerous routing error is invisible.** Missing a domain (under-routing) is
  worse than adding one (over-routing), yet the suite only exercises the latter.

**Fix:** author cases where omitting a domain is the *easy* mistake — e.g. a problem that
reads as pure software work but genuinely needs `data_engineer`, or a "just deploy it"
framing that hides a required `ml_engineer` step. Until then, `coverage` is inert as both
metric and reward.

### 5.2 No labels, no labeling pipeline

Every `label` is `null`; there is no `label.py`. Step 2 of `eval_ml_plan.md` has not
started. Nothing supervised — neither the eval-classifier nor a router fine-tune — can be
trained until ground truth exists. Note the two ground-truths are *different artifacts*
(§8): a **run-quality label** `y ∈ {excellent, acceptable, poor}` for the classifier, and a
**gold decomposition** for the router SFT.

### 5.3 The orchestrator routes blind

`Orchestrator.decompose` sends a system prompt (`ROLE`) that lists the six domain *names*
and the output format — and nothing else. None of the ownership rules, none of
`agent_contracts.md`, none of the case notes are in it. The "keyword-triggered
decomposition" failure mode documented across both review docs is therefore not (only) a
model limitation — **the prompt has no rules in it to follow.** This is the single
cheapest lever (§9) and it reframes the training data: the boundary knowledge the model
lacks is precisely what the gold decompositions encode.

### 5.4 Routing is non-deterministic

`Supervisor.validate` passes `temperature=0`; `Orchestrator.decompose` does not. The
baseline is one sample from a distribution. For measurement that adds noise; for RL /
best-of-N / preference data it is a blocker — those need either greedy decode
(`temperature=0`) for reproducibility or *N* samples per problem to estimate the routing
distribution. Decide which and make it explicit.

---

## 6. The metrics as rewards — keep / fix / replace

Builds on `EVAL_REFERENCE §10`, but judged by the optimization bar of §2.

- **`coverage` — keep, but give it variance.** Correct by construction; inert until §5.1
  cases land.
- **`routing_precision` — keep, never alone.** Pair with `coverage` (guards under-routing)
  and `assignment_accuracy` (guards within-set misassignment). Alone it is hackable toward
  dropping domains.
- **`acceptance_rate` — fix before any reward use.** Apply Fix A (`EVAL_REFERENCE §10.1`):
  a post-hoc eval-layer override — domain ∉ `expected_domains` ⇒ rejected — so it stops
  *inverting* against scope. Caveat: Fix A aligns acceptance with routing **by
  construction** (over-routing now drags both down), so the corrected `A` is partly
  redundant with `routing_precision`, and its in-scope subset is *still* graded by the
  inconsistent supervisor (deferral, truncation, lane-discipline). It stops the inversion;
  it does **not** separate scope from execution — that needs the unbundle into `in_scope`
  / `executed` / `stayed_in_lane`. Until then, unsafe to optimize as a standalone reward.
- **`output_fidelity` — do not reward.** Task-text↔output cosine rewards echoing the
  prompt. Replace with output↔gold-reference similarity or a substance-focused LLM judge
  if execution quality must enter the signal. At minimum, document that the implementation
  scores against per-task text (per `eval_ml_plan` D1), since prose elsewhere drifts to
  "problem statement."
- **`assignment_accuracy` — built, now embedding-based.** The dense per-decision signal
  training wants, and the only metric that sees the boundary distinctions the big cases
  were built to test. A substring keyword match was the v0; it false-missed on paraphrase
  (a correctly-routed deliverable phrased without the gold keyword scored wrong), so it was
  replaced with **embedding similarity** (gold deliverable ↔ best task *in the expected
  domain*, cosine ≥ 0.30), calibrated offline against the 2026-06-07 N-sample decompositions
  (`calibrate_assignment.py`). It is correct on bd-01/bd-02/bd-03/md-13, beats keyword on
  every case, and the `match` field is gone. **Root-cause limitation:** embedding matching
  only *bridges* a granularity mismatch — per-deliverable gold vs the orchestrator's
  one-paragraph-per-domain output — it does not remove it, which is why md-12's short "CSV
  export" deliverable stays diluted below threshold. The real fix is structural, in §9
  (orchestrator), not a better matcher.

---

## 7. Scale, augmentation, and a frozen holdout

24 cases is sufficient for the 4-feature logistic-regression eval-classifier
(`eval_ml_plan.md` targets 150–300 rows) but far too few to fine-tune an LLM.

- **Generate, then audit.** Templated problem variants + paraphrase augmentation + a strong
  model (Opus/Sonnet) drafting gold decompositions under the boundary rules — every
  generated gold **human-reviewed** before it becomes a label, per the D2/D6 "ground truth
  is human-owned" rule.
- **Freeze a holdout that never enters training.** With a suite this small, train/test
  contamination will silently inflate every number. The 24 curated cases (once the four
  `verified=False` ones — md-15, bd-01, bd-02, bd-03 — are confirmed) are a natural
  hand-authored **test set**; generated/augmented cases are the **train set**. Keep them
  disjoint by problem, not just by row.
- **Distillation is the likely first method.** SFT a small open model (or a smaller Claude)
  to imitate strong-model gold decompositions, then optionally refine with the eval as a
  reward. Cheaper and more stable than RL-from-scratch at this data scale.

---

## 8. Two "small models" — keep them distinct

`eval_ml_plan.md` already describes a small model: multinomial logistic regression on
`[C, R, A, F] → {excellent, acceptable, poor}`. That is **not** the "small LLM" this plan
targets. The clean division of roles:

| Model | What it is | Trained on | Role |
|---|---|---|---|
| **Eval-classifier** | logreg on `[C, R, A, F]` | run-quality labels `y` | becomes the **reward model / quality gate** |
| **Task-LLM (router)** | fine-tuned decomposer | gold decompositions | the thing we are trying to improve |

The eval suite is the **held-out test** for the task-LLM and — once trustworthy — the
**reward** for refining it. This is also where this plan meets `next-steps.md` touch
point 3: the classifier's probability, originally meant to replace the escape-valve
confidence tag, can double as the router's training reward.

---

## 9. Concrete improvements, by file

**`cases.py`**
- **sd-02 note — already fixed** in the current `cases.py` (working tree): the
  analytics-owns-the-view-layer rewrite from `EVAL_REFERENCE §8` is in place.
  `EVAL_REFERENCE.md` still lists it as `NEEDS FIX`, but the working tree is ahead of that
  doc. No action — listed only so the stale reference doesn't trigger a re-fix (and
  `EVAL_REFERENCE.md`'s verdict table should be reconciled).
- Add **`gold_decomposition`** (and/or `gold_assignments`) to the discriminating cases
  (bd-01/02/03, md-13, boundary md-\*). The SFT target + `assignment_accuracy` source (§4).
- Add **under-routing / hard-negative cases** so `coverage` and recall gain variance (§5.1).
- Confirm the four **`verified=False`** cases (md-15, bd-01, bd-02, bd-03) before they
  become training gold.
- Encode the **suite-level ownership rule** (`EVAL_REFERENCE §9`) as a header so labels
  stop being re-derived per case.

**`metrics.py`**
- **`assignment_accuracy` — built, embedding-based** (cosine ≥ 0.30, calibrated; see §6).
  The keyword `match` field is removed from the gold. Re-calibrate the threshold when the
  gold set grows; the real fix is deliverable-level orchestrator output (orchestrator bullet below).
- Make **`acceptance_rate` scope-aware** (Fix A) — two lines in the eval layer, no change
  to the supervisor's production behavior.
- **Reframe or replace `output_fidelity`**; add a docstring stating what it actually
  computes (per-task instruction ↔ output — the function has none today; the misleading
  "problem statement" wording lives only in the prose docs).

**`run_logger.py` + new `label.py`**
- Build **Step 2 labeling** (does not exist). Produce both label types (§8): run-quality
  `y` for the classifier, gold decomposition for the router SFT. Keep `raw_outputs` and
  `task_decomposition` captured so features/golds are re-computable (already done — good).

**`orchestrator.py`**
- **Done (§10 step 1):** boundary rules in the `decompose` prompt + `temperature=0`,
  re-baselined (`eval_runs/2026-06-07.jsonl`, then N-sample `eval_runs/nsample/`).
- **Structural fix — emit deliverable-level output.** `decompose` returns one prose
  `{domain, task}` per domain, bundling several deliverables into one paragraph. That
  granularity mismatch is the root cause of every `assignment_accuracy` matching wart
  (keyword fragility, embedding dilution) — see §6. Changing the output contract to a list
  of `{deliverable, domain}` makes `assignment_accuracy` an **exact, deterministic set
  comparison** (no embeddings/threshold/judge) *and* makes the orchestrator's output shape
  identical to the gold/SFT target shape (§4). Cost: it changes the production decomposition
  contract (agents consume the task text), invalidates the current baseline, and forces a
  re-capture — so land it with the orchestrator/training rework, not as a metric patch.

---

## 10. Priority order

1. **Load boundary rules into the orchestrator prompt + `temperature=0`, then
   re-baseline.** (sd-02 is already fixed — see §9.) Free; may close much of the gap; the
   mandatory control for any later fine-tune (the "measure before you improve" principle
   from `next-steps.md`, applied to training).
2. **Add `gold_decomposition` + `assignment_accuracy`** to the discriminating cases —
   unlocks honest scoring *and* SFT targets in one move.
3. **Make `acceptance_rate` scope-aware; fence `output_fidelity` out of any reward.**
4. **Author under-routing cases** so recall has variance.
5. **Stand up `label.py`** and begin producing `y` + gold targets.
6. **Generation + frozen holdout** once the gold schema is settled (§7).

Steps 1–4 are pure eval-suite work and unblock everything downstream. Steps 5–6 are the
data-volume work that an actual LLM fine-tune requires.

---

## 11. How this fits the existing tracks

- **`eval_ml_plan.md` (D1–D8)** stands: its classifier is the reward model of §8, not a
  competitor to this plan. The one correction this plan adds: its features were chosen as
  *measurements*; §2 shows two of them are unsafe as *rewards*, so the reward path needs
  `assignment_accuracy` and a scope-aware `A` that the original D1–D8 set did not include.
- **`next-steps.md`** sequencing is compatible: Session 3 (capture baseline) is done;
  this plan inserts the prompt-fix re-baseline (§10.1) as the control, and the gold-target
  work (§10.2) ahead of the consensus-loop comparison so routing quality is trainable, not
  just measurable.
- **`agent_contracts.md`** is the source text for the gold decompositions and the
  orchestrator prompt — the boundaries it records are the labels.

---

## 12. Open fork

**Router-first is the recommendation** (§3). If the intent is instead to fine-tune the
**domain agents**, the plan changes materially: gold becomes reference *outputs* (expensive
to author), `output_fidelity` must be replaced before it can score anything, and the
suite needs per-domain quality rubrics rather than routing golds. Confirm the target before
investing in gold authoring — the data you write is not reusable across the two.

---

## 13. Bottom line

The suite is a strong *measurement* instrument and a near-complete *routing corpus* — but
it is not yet a *training signal*. Three gaps separate the two: it has no per-example
target (only a domain set), two of its four metrics are unsafe to optimize, and it has zero
variance on recall. Close those, fix the orchestrator prompt as the free baseline, and the
same 24 cases that today produce four scalars become the seed of a router fine-tune whose
improvement you can actually prove against a frozen holdout.
