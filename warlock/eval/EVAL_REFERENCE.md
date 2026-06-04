# Multi-Agent Routing Eval Suite — Consolidated Reference

A complete review of all 24 test cases and the four metrics that score them
(`coverage`, `routing_precision`, `acceptance_rate`, `output_fidelity`), with the
problems found and the fixes for each.

---

## 1. Executive summary

Two things were under review: the **test cases** (are the gold `expected_domains`
and exclusion notes correctly specified?) and the **metrics** (do the four scores
measure what they're meant to?).

**Test cases — almost entirely sound.** Of 24 cases, **23 were correctly specified as
written.** Exactly one (`sd-02`) needed a real specification fix — **since applied** (the
§8 rewrite is now in `cases.py`); the analysis below is retained as the rationale. One
other (`md-04`) has an optional hardening. The notes get stronger over the suite, introducing conditional
clauses, handoff triggers, and artifact-ownership reasoning that make the gold labels
principled and robust to problem variants.

**Metrics — two of four are trustworthy, two are not.**

| Metric | Verdict |
|---|---|
| `coverage` | **Trustworthy.** Correctly reports whether all expected domains were invoked, in all 24 cases. |
| `routing_precision` | **Trustworthy at the set level**, but **set-based** — blind to *which deliverable was assigned to which domain* within the expected set. Misses the exact boundary-note distinctions the big cases test (proven by bd-01, bd-02, bd-03). |
| `acceptance_rate` | **Not a scope signal.** Tracks inconsistent per-agent behavior (ship-vs-defer, truncation, lane-discipline, inter-task over-reach), never consults `expected_domains`, and can invert, scramble, or coincidentally agree with routing depending only on how agents behaved. |
| `output_fidelity` | **Weakest.** Measures task-vocabulary overlap; mostly a function of task breadth, output length, preamble, and truncation. Uncorrelated with run quality — the only perfect run (bd-01) scored *lowest*. |

The single most important conclusion: **`routing_precision` and `coverage` reflect
your scope notes; `acceptance_rate` and `output_fidelity` do not, and should never be
read as if they corroborate routing.** Where acceptance appears to agree with routing
(md-06, md-12, md-15, bd-01), the agreement is coincidental.

---

## 2. What each metric actually measures

### coverage
`len(invoked ∩ needed) / len(needed)`. Fraction of expected domains that were invoked.
Recall over domains. Correct and reliable. Returns `None` when no expected domains.
**No change needed.**

### routing_precision
`len(invoked ∩ needed) / len(invoked)`. Fraction of invoked domains that were expected.
Precision over domains. Correct **as a set-membership check**. Its limitation, surfaced
by the big cases: it operates on the *set of domains invoked*, not on the *task→domain
assignment*. A decomposition that invokes the right domains but routes a deliverable to
the wrong (but still expected) domain scores perfectly on the swap.

### acceptance_rate
`sum(verdict["accepted"]) / len(verdicts)`. Fraction of agent tasks the LLM-judge
validator marked accepted. **The validator judges each agent against the task the
orchestrator assigned it — never against `expected_domains`.** As a result it measures
agent execution behavior, not scope correctness.

### output_fidelity
Mean cosine similarity (MiniLM) between each task's *instruction text* and that domain's
*agent output text*. Measures topical/vocabulary adherence of the answer to the prompt —
not correctness, not scope, not quality. Note: `agent_outputs` is keyed by domain, not
by task, so when a domain appears multiple times in `task_decomposition` (e.g., devops_mlops
with five tasks in bd-03) all task entries are compared against the same single output —
which explains the anomalously low fidelity on sprawling platform problems.

---

## 3. The acceptance_rate problem in detail

Across 24 cases, `acceptance_rate` verdicts were driven by at least four behavior-level
factors, none of which is "is this domain in `expected_domains`?", all applied
inconsistently — sometimes within a single case:

1. **Ship-vs-defer.** Agents that opened with clarifying questions or framing challenges
   instead of delivering finished artifacts were frequently rejected — but the *same*
   preamble behavior was accepted for other agents in the same case (sd-02, md-02, md-09,
   md-13, bd-02).
2. **Truncation.** Outputs cut off mid-stream were sometimes rejected for being
   "incomplete" (sd-06) and sometimes waved through (md-06, bd-01).
3. **Lane-discipline / task-adherence.** Agents that produced the whole solution instead
   of their assigned slice were rejected (md-07: all three rejected for this reason alone;
   bd-03 software_dev: rejected for expanding into promotion-criteria and drift-detection
   design that belongs to expected domains). Note: bd-03 is one of the few cases where
   this rejection is substantively correct — the agent did produce work belonging to
   in-scope domains, not just a deferral.
4. **Inter-task over-reach.** Agents that reached into a sibling task's lane were
   rejected (md-03, md-08, md-12, md-15) — a scope-flavored judgment, but about the
   orchestrator's task partition, not `expected_domains`.

Consequences observed:

- **Rewards out-of-scope work.** Excluded domains that executed tidily were accepted:
  md-01, md-02, md-04, md-08, md-11, md-13, bd-03 (analytics). Agents that *announced*
  they were out of scope and worked anyway were still accepted (md-01, md-02, md-04, md-14).
- **Penalizes scope-aware behavior.** Agents that correctly declined out-of-scope work —
  matching your exclusion reasoning — were rejected: md-03, md-09, md-11, md-12, md-13,
  bd-02, bd-03. This hit `analytics` five times and `data_scientist` notably.
- **Inverts against scope.** In sd-06, md-05, md-08, md-10, md-12 an out-of-scope domain
  was accepted while a required domain was rejected.
- **Maximal inversion.** In md-11 and md-13 (both `Acceptance == Routing == 0.4` with
  *disjoint* numerators) the entire correct decomposition was rejected while only the
  excluded infrastructure domains were accepted.
- **Manufactures out-of-taxonomy reasons.** In md-11 the validator rejected `ml_engineer`
  by invoking a "compliance specialist" domain that does not exist in the six-domain
  ontology.
- **Contradicts an explicit gold clause.** In md-13 the validator rejected `data_scientist`
  on the reasoning that the task was "too specified for data-science judgment" — the exact
  reasoning the spec's "training always belongs to data_scientist regardless of how
  specified" clause was written to refute.
- **Non-deterministic on the same behavior.** In md-14 the validator *rewarded*
  `ml_engineer` and *rejected* `data_scientist` for the identical move (declining
  out-of-scope work) in the same case.
- **Factually contradicts the artifact.** In md-10 `devops_mlops` was rejected for
  "crossing into application/infrastructure code" while writing *less* such code than the
  accepted `software_dev` agent.

**Coincidental agreement is not scope-tracking.** In md-06, md-12, md-15, bd-01 routing
and acceptance both implicated the same domain — but via inter-task over-reach (or, in
bd-01, simply no spurious domains existing plus well-behaved agents), never via scope.
The control in each: a lane-disciplined version of the out-of-scope agent would have been
accepted.

---

## 4. The routing_precision set-vs-assignment gap

Validated as scope-truthful at the set level in all 24 cases, but the three large cases
prove it cannot score *task→domain assignment*:

- **bd-01** (all six domains, Routing = 1.0): the LLM routed **drift monitoring to
  devops_mlops** when the spec assigns it to **ml_engineer**. Both are expected domains,
  so the swap is invisible — perfect routing despite failing the exact distinction the
  spec's boundary notes were built to test.
- **bd-02** (five domains, Routing = 0.833): the LLM routed **training to ml_engineer**
  (spec: data_scientist) and **packaging/integration/drift to devops_mlops** (spec:
  ml_engineer). Routing dropped to 0.833 **only** because of the out-of-set `software_dev`;
  the three-way in-set seat-shuffle was uncounted.
- **bd-03** (four domains, Routing = 0.667): the LLM routed **promotion criteria to
  ml_engineer** (spec: data_scientist) and **feature drift detection to data_scientist**
  (spec: ml_engineer). Routing's 0.667 is fully explained by the two out-of-set domains
  (analytics, software_dev); the in-set misassignments are invisible.

The ml_engineer-vs-devops_mlops drift-ownership boundary was probed in all three big
cases and **failed all three times in the same direction** (drift pushed toward
devops_mlops). The current metrics will not surface this.

---

## 5. The fidelity problem

Fidelity values across the suite:

```
sd-01 0.685  sd-02 0.608  sd-03 0.544  sd-04 0.543  sd-05 0.650  sd-06 0.517
md-01 0.623  md-02 0.613  md-03 0.580  md-04 0.489  md-05 0.620  md-06 0.644
md-07 0.614  md-08 0.576  md-09 0.592  md-10 0.508  md-11 0.507  md-12 0.474
md-13 0.556  md-14 0.507  md-15 0.710
bd-01 0.470  bd-02 0.590  bd-03 0.478
```

Range ~0.47–0.71, clustered ~0.55–0.62. Findings:

- **Uncorrelated with quality.** bd-01 (the only Routing 1.0 / Acceptance 1.0 run)
  scored the **lowest** Fidelity (0.470). md-15 (clean two-domain) scored **highest**
  (0.710). The metric inverts the actual quality ordering on the strongest cases.
- **Tracks task breadth and output shape.** Lower on sprawling multi-deliverable problems
  (bd-01, bd-03, md-11, md-12, md-14), higher on tight concrete ones (md-15, sd-01).
- **Shares acceptance's confounds.** Long framing preambles and truncated outputs both
  pull the output's vocabulary away from the task text — the same behaviors that move
  acceptance.
- **Rewards parroting over solving.** Cosine similarity between task text and output text
  is highest when the answer echoes the prompt's words. An agent that correctly reframes a
  problem by introducing the right technical vocabulary is penalized; a fluent,
  on-vocabulary, wrong answer scores high.
- **Accidental partial signal.** In bd-01, fidelity (0.470) accidentally caught the
  drift-monitoring misassignment: the drift-task text embedded poorly against the
  devops_mlops agent's A/B-focused output, pulling the average down. This is a side
  effect of the multi-task-one-output collision, not by design.

It has marginal value only as a **within-case relative flag** — which of this run's agents
drifted furthest from its assigned task. As an absolute cross-case quality number it is
not actionable.

---

## 6. Per-case verdicts

All cases correctly specified except where noted.

| Case | Expected domains | Routing | Acceptance | Spec verdict |
|---|---|---|---|---|
| sd-01 | software_dev | 0.33 | 1.0 | Correct — Slack-alert ownership via lifecycle rule |
| sd-02 | analytics | 0.33 | 0.67 | **FIXED** — view/semantic-layer ownership now assigned to analytics; see §8 |
| sd-03 | ml_engineer | 0.33 | 0.67 | Correct — tightest single-domain note |
| sd-04 | data_scientist | 0.50 | 0.50 | Correct — analytics-vs-DS axis is the test |
| sd-05 | devops_mlops | 0.50 | 0.50 | Correct |
| sd-06 | software_dev | 0.50 | 0.50 | Correct — first routing/acceptance inversion |
| md-01 | data_engineer, analytics | 0.50 | 0.75 | Correct — both out-of-scope domains accepted |
| md-02 | ml_engineer, devops_mlops | 0.40 | 0.80 | Correct — best note (conditional DS exclusion) |
| md-03 | data_scientist, analytics | 0.67 | 0.0 | Correct — validator misfiled routing error as acceptance rejection |
| md-04 | data_engineer, ml_engineer | 0.50 | 1.0 | Correct — **optional hardening** on devops exclusion; see §8 |
| md-05 | software_dev, data_engineer | 0.67 | 0.67 | Correct — rejection reason contradicts artifact |
| md-06 | data_scientist, analytics | 0.67 | 0.67 | Correct — coincidental agreement (inter-task over-reach) |
| md-07 | devops_mlops, software_dev | 0.67 | 0.0 | Correct — all three rejected for lane-discipline; content was good |
| md-08 | data_engineer, data_scientist, ml_engineer | 0.60 | 0.40 | Correct — two in-scope rejected, out-of-scope ml_engineer accepted |
| md-09 | ml_engineer, devops_mlops | 0.75 | 0.50 | Correct — best multi-domain routing |
| md-10 | software_dev, ml_engineer, devops_mlops | 0.75 | 0.75 | Correct — same scores, opposite domains; reason factually inverted |
| md-11 | data_scientist, ml_engineer | 0.40 | 0.40 | Correct — disjoint 0.4; out-of-taxonomy rejection reason |
| md-12 | analytics, software_dev | 0.50 | 0.75 | Correct — analytics owns query logic |
| md-13 | data_scientist, ml_engineer | 0.40 | 0.40 | Correct — disjoint 0.4; validator contradicts gold's central clause |
| md-14 | data_engineer, devops_mlops, analytics | 0.50 | 0.67 | Correct — same move rewarded (ML) and punished (DS) in one case |
| md-15 | devops_mlops, data_engineer | 0.67 | 0.67 | Correct — "owns files vs. owns whether project supports them" |
| bd-01 | all six | 1.0 | 1.0 | Correct — routing 1.0 hides drift→devops misassignment |
| bd-02 | DE, DS, ML, devops, analytics | 0.83 | 0.83 | Correct — training→ML and drift→devops misassignments invisible to routing |
| bd-03 | DE, DS, ML, devops | 0.67 | 0.83 | Correct — criteria→ML swap hidden; analytics accepted out-of-scope |

---

## 7. Recurring orchestrator failure modes

**Keyword-triggered decomposition.** The orchestrator pattern-matches surface tokens
("Slack alert" → software_dev, "Docker" → devops_mlops, "SQL queries" → data_engineer,
"automate" → software_dev) instead of reading the lifecycle of the primary task.
Observed in every group.

**The ml_engineer-vs-devops_mlops confusion.** Drift monitoring (spec: ml_engineer) was
pushed to devops_mlops in bd-01, bd-02, and bd-03 — all three cases that explicitly tested
this boundary, all three failed in the same direction. The orchestrator treats "monitoring"
as an infrastructure/ops keyword regardless of whether the monitoring is model-health or
serving-infra.

**The data_scientist-vs-ml_engineer confusion.** Training (spec: data_scientist) was
pushed to ml_engineer in bd-02 and bd-03. The orchestrator conflates "build a model" with
"ML engineering" regardless of the "training always belongs to data_scientist" rule.

**Chain-shifting.** In bd-02 and bd-03 the orchestrator slid every ML-axis responsibility
one domain downstream simultaneously (training → ml_engineer, packaging/drift → devops_mlops,
scheduling → software_dev), rather than making a single targeted misassignment.

---

## 8. The two spec fixes

### sd-02 — required fix *(applied)*

**Status:** done — the fix below is now live in `cases.py`. Retained as the rationale for
the change.

**Problem:** `expected_domains=["analytics"]`. The note excludes `data_engineer` as
"explicitly scoped out," but the problem only scopes out *pipelines*, not the
*view/semantic layer* the KPIs require. Whether analytics writes those SQL views or
consumes views built by data_engineer is unstated — which is why the LLM split three
ways and validators contradicted each other (identical view-writing work accepted for
data_engineer, rejected for software_dev).

**Fix:** rewrite the note to assign the view/semantic layer explicitly to analytics,
consistent with the suite-level lifecycle rule (§9):

> Included: analytics — KPI definitions, the SQL view/semantic layer behind the
> dashboard, and the Metabase build; writing aggregation SQL for one's own dashboard is
> analytics work, not data engineering.
> Excluded: data_engineer — *ingestion and source-table maintenance* are scoped out
> ("handled separately"); the dashboard's own derived views are not data engineering.
> software_dev — building Metabase cards/views is not a deployable service.

This makes over-decomposition penalizable: spinning up data_engineer to re-model tables
that already exist is the routing error routing_precision should catch.

### md-04 — optional hardening

**Problem (minor):** the `devops_mlops` exclusion rests on "no scheduling or monitoring
asked," but a streaming Kafka→Redis pipeline with backfill and online update *implies* an
ops surface. The spec is correct as written (it draws the line at *what was asked*), but
the reasoning is looser here than elsewhere.

**Hardening:** add one clause tying it to the suite-level rule:

> operational concerns (scheduling, lag monitoring) live inside the data_engineer pipeline
> unless a separate deployment/observability deliverable is explicitly requested.

---

## 9. The suite-level ownership rule

The exclusion reasoning across the suite is consistent and can be stated once so each
case's notes point at it rather than re-deriving it:

> **Ownership is decided by the lifecycle of the artifact a piece of work lives inside,
> not by keyword.** Operational hooks (schedule, alert, retry, a webhook call) belong to
> the domain that owns the artifact they live in, *unless* they have independent lifecycle
> (their own deployability, interface contract, and operational surface). The test is
> complexity/lifecycle, not the mere presence of a word like "alert," "schedule," or "SQL."

Corollaries used throughout (all consistent with the cases):

- A webhook/alert call inside an error handler → the pipeline's domain, not software_dev
  (sd-01). Alerting *with* dedup/escalation/on-call *as a requested system* acquires
  independent lifecycle → software_dev/devops_mlops.
- **Training and held-out evaluation always belong to data_scientist**, regardless of how
  specified the approach is (md-13, bd-02, bd-03). Only a *deployed scoring pipeline* is
  ml_engineer.
- **Drift monitoring per model → ml_engineer; A/B routing and serving-infra monitoring →
  devops_mlops** (bd-01/bd-02/bd-03 boundary). The orchestrator failed this distinction
  in all three big cases in the same direction.
- **software_dev owns the API surface; ml_engineer owns the inference layer behind it**
  (bd-01).
- Writing aggregation SQL for one's own dashboard is **analytics**, not data engineering
  (sd-02, md-12).
- Scheduling/alerting *explicitly requested* is a real devops_mlops deliverable (md-05,
  bd-02); scheduling/alerting merely *implied* by a pipeline is not (md-04) — resolve by
  "what was asked."
- A persona that *owns an existing artifact* validates it even when no new artifact is
  built (analytics sign-off, md-14).
- A domain is included for *design* work only when design is actually required; if the
  metric/threshold/approach is pre-agreed, the design domain is excluded (md-02, md-09,
  bd-03 conditional clauses).

---

## 10. Fixes for the metrics

### 10.1 acceptance_rate — make it scope-aware and unbundle it

The root cause: the validator grades each agent against the orchestrator's assigned task,
never against `expected_domains`. Two complementary fixes:

**Fix A — feed the validator `expected_domains`.** Add a hard rule: an agent operating
in a domain not in `expected_domains` is rejected regardless of execution quality. This
makes acceptance and routing aligned by construction rather than by luck, and stops
acceptance rewarding out-of-scope work (md-01/02/04/08/11/13, bd-03) and inverting
against required domains (sd-06, md-05/08/10/12). Implementation: a post-hoc override in
the eval layer — two lines in `run_logger.py` or `metrics.py` — without touching the
supervisor's production behavior.

**Fix B — split the accept bit into independent signals.** The current single boolean
conflates at least three orthogonal judgments. Replace with separate fields:

- `in_scope` — is this domain in `expected_domains`? Deterministic, from the gold. No
  LLM judge needed.
- `executed` — did the agent deliver an artifact vs. defer or clarify only? Captures the
  ship-vs-defer axis without contaminating scope reads.
- `stayed_in_lane` — did the agent confine itself to its assigned slice vs. answer the
  whole problem or reach into sibling tasks? Captures the md-07/inter-task-over-reach
  axis.

With these separated, "the analytics agent correctly declined out-of-scope work" is no
longer punishable as a scope failure, and "the agent shipped good in-scope work" is no
longer confounded by truncation.

**Also constrain the validator prompt** to: never invent domains outside the six-domain
taxonomy (md-11's "compliance specialist"), and never reject an agent it explicitly judges
to have made the right call (md-03's "routing error" recorded as an acceptance rejection).

### 10.2 routing_precision — add a per-deliverable assignment metric

Keep `coverage` and `routing_precision` as set-level signals (they're correct), but add a
metric that scores **task→domain assignment**, since that is where the boundary-note
distinctions live and where bd-01/bd-02/bd-03 actually failed invisibly.

**`assignment_accuracy`:** add a `gold_assignments: list[dict]` field to `EvalCase` for
cases whose discriminating content is in the boundary notes. Each entry maps a
deliverable keyword to its expected domain:

```python
gold_assignments=[
    {"deliverable": "drift monitoring", "domain": "ml_engineer"},
    {"deliverable": "A/B routing",      "domain": "devops_mlops"},
    {"deliverable": "API endpoint",     "domain": "software_dev"},
    {"deliverable": "inference layer",  "domain": "ml_engineer"},
]
```

Then `assignment_accuracy = fraction of LLM tasks whose (deliverable_keyword,
assigned_domain) matches the gold`. This would have caught drift→devops_mlops (bd-01),
training→ml_engineer (bd-02), and promotion-criteria→ml_engineer (bd-03) — all invisible
to set-based routing. Apply to bd-01, bd-02, bd-03, md-13, and any future spec with
explicit boundary notes; not warranted for the full suite.

### 10.3 output_fidelity — reframe or replace

As built (task-text ↔ output-text cosine similarity) it rewards restating the prompt and
is uncorrelated with quality. Two options:

**Reframe (cheap):** keep the implementation but label it explicitly "topical adherence to
the assigned task." Use it only as a *within-case relative* flag — which of this run's
agents drifted furthest from its task. Never read a high absolute value as validation
(md-15 0.71 vs. bd-01 0.47 inverts the actual quality ordering). Fix the docstring in
`metrics.py`: the current description says "original problem statement" but it computes
against the per-task instruction text, not the problem statement.

**Replace (better signal):** compare the output to a *gold reference* of what a good
on-scope answer contains, or use a substance-focused LLM judge. Task-text↔output
similarity rewards parroting; output↔gold-reference measures whether the right work was
done.

---

## 11. Priority order

1. **Fix sd-02's note** (§8) — **done.** The one real spec defect; the case mislabeled
   view-writing ownership and undermined the lifecycle rule it should exemplify. The fix
   is now in `cases.py`.
2. **Capture the suite-level ownership rule** (§9) as a header comment in `cases.py` and
   point each case's notes at it — prevents future drift and is the cheapest
   high-leverage change.
3. **Make acceptance_rate scope-aware** (Fix A, §10.1) — a post-hoc override in the eval
   layer, two lines; largest reduction in misleading numbers.
4. **Unbundle acceptance into three signals** (Fix B, §10.1) — separates scope from
   execution and lane-discipline; enables future analysis on which failure mode dominates.
5. **Add `assignment_accuracy`** (§10.2) — the only way to score the ml_engineer-vs-devops
   and training-ownership distinctions the big cases were built to test and currently fail
   invisibly.
6. **Reframe or replace fidelity** (§10.3) — lowest urgency; at minimum fix the docstring
   and stop reading it as a quality score.
7. **Optionally harden md-04's note** (§8) — cosmetic; spec is correct as written.

---

## 12. Bottom line

The test cases are well-built — 23 of 24 correct as written, with only sd-02 having needed
a real fix (since applied) and md-04 an optional one; the notes are a model of principled,
variant-robust gold labels.
The scoring is where the work is. `coverage` and `routing_precision` faithfully track
scope at the set level, but `routing_precision` is blind to task→domain assignment within
the expected set — it silently passed the drift-ownership failures in all three big cases,
where the decomposer assigned drift monitoring to devops_mlops when every spec said
ml_engineer, and neither metric registered it. `acceptance_rate` does not track scope at
all: it grades agents against the orchestrator's task partition, rewarding out-of-scope
work and penalizing scope-aware refusal, inconsistently, with documented cases of
factual contradiction and out-of-taxonomy reasoning. `output_fidelity` measures
prompt-echo, not quality — it rated the only perfect run worst. Fix acceptance by feeding
it `expected_domains` and splitting scope from execution; add `assignment_accuracy` to
capture the boundary-note distinctions that set-based routing cannot see; and either
reframe fidelity as a relative drift flag or replace it with a reference-based measure.
