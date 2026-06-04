# Eval Suite Notes

Reference for reading aggregate scores and interpreting per-case results.
Written after reviewing sd-01 through sd-06, md-01 through md-14 (20 cases total).

---

## 1. Suite-Level Ownership Rule

**Operational hooks and subordinate steps live inside the primary domain.**

A task belongs to domain X if its lifecycle is entirely contained within X's deliverable.
Route to a second domain only when the work has an independent lifecycle — its own
deployment, contract, or maintenance cycle separate from the primary task.

Concrete applications:

- A Slack webhook call inside a pipeline's error handler → `data_engineer` (sd-01).
  It is not a standalone notification service.
- A SQL aggregation view written specifically for one dashboard → `analytics` (sd-02).
  It has no lifecycle outside the dashboard it serves.
- A REST inference server baked into a Docker model image → `ml_engineer` (sd-03).
  It exists solely to serve the model; it is not a user-facing service.
- Querying experiment data and plotting treatment effects → `data_scientist` (sd-04).
  They are steps inside the causal analysis, not a separate reporting product.
- Reviewing existing code for containerization readiness → `devops_mlops` (sd-05).
  It is a subordinate step of setting up the pipeline, not an independent software
  engineering deliverable.
- Writing SQL queries for a read-through API endpoint → `software_dev` (sd-06).
  Querying existing tables from inside an endpoint is application work, not data
  engineering — no pipeline, no table creation, no ETL.

**Severity distinction:** "no CI/CD pipeline" (sd-03) is an explicit prohibition —
violating it is a hard error. Splitting `analytics` off for visualization (sd-04) is
a defensible-but-wrong ownership call. Both score in the same routing_precision band
(0.33–0.5) but represent different failure modes. Routing_precision does not
distinguish severity; read the decomposition when diagnosing.

---

## 2. Metric Interpretation Notes

### Coverage
Fraction of expected domains that were actually invoked.
- Measures: did the orchestrator miss a required domain?
- Does not measure: whether extra domains were invoked.
- Typical failure: Coverage < 1.0 means a required agent was never called.
  In sd-01 through sd-04, Coverage = 1.0 in all cases — the orchestrator always
  hit the right domain, it just added more.

### Routing (routing_precision)
Fraction of invoked domains that appear in expected_domains.
- Measures: how focused the decomposition was.
- Does not measure: severity of over-decomposition, or whether the extra domains
  produced useful work.
- Limitation: a "defensible-but-wrong" split (sd-04) and an "explicit-prohibition
  violated" split (sd-03) score identically. Read the decomposition to distinguish.
- **Set-based blindspot (bd-01):** routing_precision operates on the *set* of invoked
  domains, not on which deliverable was assigned to which domain. A within-expected-set
  swap — routing drift-monitoring to devops_mlops when the boundary note assigns it to
  ml_engineer — is invisible to this metric: both domains are in expected_domains, the
  set is correct, and routing = 1.0 is reported despite the misassignment. bd-01 is the
  first case where a spec was explicitly constructed to test a specific task→domain
  boundary (ml_engineer owns drift monitoring; devops_mlops owns A/B routing), the LLM
  failed that test, and routing reported success. All prior cases validated routing as
  scope-truthful at the set level; they remain so — but bd-01 establishes that
  set-level correctness does not imply assignment correctness.
- **Fix, if boundary-note distinctions need scoring:** add a `gold_assignments:
  list[{deliverable, domain}]` field to EvalCase for cases whose discriminating content
  is in task→domain assignment, and compute a per-deliverable assignment accuracy
  against it. Applicable to bd-01, md-13, and any other spec with explicit boundary
  notes. Not warranted for the full suite.

### Acceptance
Fraction of invoked agents whose output was accepted by the supervisor.
- Measures: output quality and scope adherence per agent.
- Known confound: agents that defer ("asked clarifying questions instead of
  delivering") are rejected for execution failure, not scope. Acceptance_rate
  therefore conflates scope correctness with agent verbosity/deferral behavior.
  When acceptance is low, check the rejection reason before concluding the agent
  was out of scope.
- Known inconsistency: the supervisor validates each agent in isolation, with no
  visibility into what other agents were assigned. Identical work (e.g., writing
  SQL views) can be accepted under one domain label and rejected under another
  depending on how the task was phrased. See sd-02.

### Fidelity
Average cosine similarity (MiniLM) between each task's *assigned task text* and the
corresponding domain's agent output. Not similarity to the problem statement — to the
orchestrator-generated task instruction per domain.

- Measures: topical adherence — does the agent's response use vocabulary similar to
  the task it was assigned?
- Does not measure: correctness, routing quality, scope adherence, or output quality.

**Range across the suite (22 cases):**
sd-01 0.685, sd-02 0.608, sd-03 0.544, sd-04 0.543, sd-05 0.650, sd-06 0.517,
md-01 0.623, md-02 0.613, md-03 0.580, md-04 0.489, md-05 0.620, md-06 0.644,
md-07 0.614, md-08 0.576, md-09 0.592, md-10 0.508, md-11 0.507, md-12 0.474,
md-13 0.556, md-14 0.507, md-15 0.710, bd-01 0.470.
Clustered 0.47–0.71, center of mass ~0.56.

**Uncorrelated with run quality.** bd-01 — the only case with Coverage = Routing =
Acceptance = 1.0, all six correct domains, all accepted — has the *lowest* Fidelity
in the suite (0.470). md-15, a clean narrow two-domain case, has the *highest* (0.710).
Fidelity inversely ordered the two best-specified cases. Do not use Fidelity as a
quality or correctness signal, and do not read a high Fidelity number as validation.

**What it does track (weakly): task breadth and abstraction.** Tight, concrete
single-deliverable tasks (md-15, sd-01, sd-05) cluster near the top. Broad
multi-deliverable tasks (bd-01, md-12, md-11, md-14) cluster near the bottom. The
mechanism is lexical: when a task instruction is long and multi-clause, an agent that
correctly answers one slice produces an output whose vocabulary drifts from the full
task embedding.

**Shared confounds with acceptance.** The same two behaviors that suppress acceptance —
long clarifying-question preambles and truncated outputs — also drag Fidelity down.
A preamble of "let me push back on the framing" makes the output text diverge from
the task text before the on-task content appears; truncation removes the implementation
tail and leaves the preamble. Fidelity and acceptance are penalizing the same surface
behaviors, independently and for different reasons.

**Structural problem: rewards parroting, not solving.** Cosine similarity between
task text and output text is maximized when the output echoes the task's vocabulary.
An agent that restates the task and lists what it *would* do can score higher Fidelity
than one that does the correct, harder thing — reframing the problem, narrowing scope,
or introducing the right technical vocabulary that isn't in the task. This is the same
behavior the validator penalizes (see analytics-scope-aware-penalty concentration, §4);
both Fidelity and the validator depress the signal on substantively correct divergence.

**Accidental partial signal (bd-01).** When devops_mlops was assigned the
drift-monitoring task but its agent delivered A/B content instead, Fidelity caught the
mismatch: cosine_sim("drift monitoring task text", A/B-focused output) is low;
cosine_sim("A/B task text", A/B-focused output) is high. The two devops_mlops entries
average to a low score, which pulled bd-01 Fidelity to 0.470. This is not by design —
it is a side effect of the two-task-one-output collision — but it is the only metric
in the suite that registered the drift-vs-A/B misassignment at all.

**Where Fidelity has marginal value.** Very low Fidelity on one domain within a case
is a flag that the agent wandered off its assigned task entirely (md-07 family, where
agents ignored their slice and answered the whole problem). As a *within-case relative*
signal — which of this case's agents drifted farthest — it is more defensible than as
a cross-case absolute number. The narrow dynamic range (0.24 spread) and large
confounds make cross-case comparison unreliable.

**Fix if Fidelity should mean more:** compare output to a *reference* of what a good
on-scope answer contains, not to the task instruction. Task↔output similarity rewards
restating the prompt. Output↔gold-reference similarity (or an LLM judge on substance)
would measure whether the right work was actually done.

### Routing × Acceptance interaction
These two metrics are designed to be orthogonal but can spuriously align or
conflict depending on agent execution quality:
- **Spurious alignment (sd-04, sd-05):** out-of-scope agents were rejected for
  execution failure (deferral, asking for code) rather than for being out of scope.
  Had they delivered competent work, the validator would likely have accepted it —
  producing the same low-routing / high-acceptance split seen in sd-02 and sd-03.
- **Genuine conflict (sd-02, sd-03):** out-of-scope agents produced good output and
  were accepted; routing was low; acceptance was high. The metrics disagreed.
- **Full inversion (sd-06, md-05):** the in-scope agent was rejected while the
  out-of-scope agent was accepted. In sd-06: software_dev (correct) rejected for
  truncation; data_engineer (wrong) accepted for complete output. In md-05:
  data_engineer (correct, required) rejected for "not executing" — despite delivering
  complete BigQuery DDL and gcloud commands — while devops_mlops (wrong) was accepted
  for monitoring work the problem didn't request. The md-05 rejection is the clearest
  factual contradiction in the suite: the validator's stated reason is directly
  contradicted by the artifact. The inversion is not a one-off; it is a reproducible
  property of the validator. Routing is the only metric that got both cases right.
- **Anti-correlated by construction (md-01):** routing = 0.5, acceptance = 0.75. Both
  out-of-scope domains (devops_mlops, data_scientist) were accepted for competent
  execution; the in-scope domain (analytics) was rejected for clarifying questions.
  The two metrics don't just disagree — they are mechanically pushed apart: every
  extra well-executed out-of-scope fragment lifts acceptance by one unit while
  lowering routing by one unit. A model that over-decomposes competently will always
  score low routing and high acceptance. Reading them together here would suggest the
  decomposition was mostly fine (0.75 accepted) when half the domains shouldn't exist.
- **Extreme anti-correlation (md-02):** routing = 0.4 (lowest in the suite), acceptance
  = 0.8 (near-highest). The orchestrator invoked five domains against an expected two.
  Four out-of-scope agents executed competently and were accepted. The one rejected
  agent (data_engineer) was out of scope and rejected for deferral — not scope.
  md-02 is the case to point at when explaining the problem: the worst decomposition
  in the suite earned a near-top acceptance score precisely because the over-decomposition
  was competent. If you co-reported these metrics, md-02 would look like a mostly-good run.

Do not read routing/acceptance agreement as evidence the metrics are consistent.
Check the validator rejection reasons to determine which case applies.

### Root cause of routing/acceptance divergence
The validator grades agents against the orchestrator's task description, not against
`expected_domains`. It sees what the agent was asked to do; it does not know whether
that domain should have been invoked at all. This means:
- `routing_precision` knows `software_dev` is out of scope (not in `expected_domains`).
- The validator does not — it judges execution against the task it was handed.

In sd-05, the validator's rejection reason explicitly endorsed the out-of-scope task
("it should have only reviewed the existing Dockerfile..."), accepting the
orchestrator's decomposition as legitimate ground truth. If the agent had delivered
a clean production-readiness checklist, it would have been accepted — and the metrics
would have disagreed again.

The clearest evidence of this root cause is now across two cases: in md-01 the
devops_mlops agent opened with "This is a data engineering problem, not MLOps"; in
md-02 the software_dev agent opened with "This is crossing a boundary between ML
Engineering and Software Engineering." Both correctly self-diagnosed they were out of
scope, did the work anyway, and were accepted. The validator rewarded agents that
announced they shouldn't be there.

### Validator non-determinism on correct domains
In md-01, the analytics agent (an expected domain) was rejected for asking clarifying
questions about lead definitions and ROAS — legitimate flags given the problem's
ambiguity. In the same run, the data_engineer agent opened with a full constraints
table of unknowns ("what I need to move to a full design") and the data_scientist
produced an entire plan of caveats — both accepted. Identical behavior, opposite
verdicts, within a single run. This is validator non-determinism landing on a correct
domain, which is the worst place for it: it directly suppresses acceptance for an
agent that should be counted as successful.

### The acceptance channel is overloaded (md-03)
md-03 is the anchor case for understanding what acceptance_rate actually measures.
All three agents were rejected; the three rejection reasons reveal three different
criteria applied simultaneously:
- **Inter-agent scope policing**: analytics rejected for proposing significance tests
  assigned to data_scientist. The validator policed overlap between two in-scope agents —
  a criterion that has nothing to do with `expected_domains`.
- **Ship-vs-defer**: data_scientist rejected for methodological framing and incomplete
  code instead of delivering p-values.
- **Misfiled routing judgment**: software_dev rejected even though the validator
  explicitly called the agent correct: "the agent correctly identified that this task
  belongs to analytics/data science... making this a routing error, not an agent failure."
  The validator diagnosed a routing error but had no channel for it except the accept/reject
  bit — contaminating acceptance with a routing judgment.

The md-03/md-04 pair is the complete proof that acceptance_rate is uncorrelated with
scope. In md-03, the software_dev agent refused out-of-scope work — the validator
called it "the right call" — and was rejected. In md-04, the software_dev agent
performed out-of-scope work and was accepted. Same domain, opposite scope behavior:
acceptance rewarded the violation and punished the refusal. There is no reading of
acceptance_rate under which that is measuring "right domain, well executed."

md-04 also produced the maximum anti-correlation in the suite: Acceptance = 1.0,
Routing = 0.5. A perfect-acceptance run doubled the domain count. If these were
ever combined into one quality number, md-04 would read as flawless.

Acceptance = 0 in md-03 does not mean "the decomposition failed." It means the
overloaded accept/reject bit fired on scope policing, deferral, and a misfiled routing
judgment all at once. As a measure of execution quality, this 0 is nearly uninterpretable.
Routing = 0.667 remained clean and correct throughout.

### Decision: how to fix acceptance_rate

Two options, decided after reviewing all six single-domain cases:

**Option A — Keep acceptance as execution-only.** Document clearly that it is not a
scope signal and must never be read alongside routing as corroboration. routing/coverage
judge decomposition quality; acceptance judges execution-given-decomposition. Two
independent axes. Leaves a known confound in place.

**Option B — Pass `expected_domains` to the validator (recommended).** Any agent
operating in a domain not in `expected_domains` is rejected regardless of execution
quality. Makes routing and acceptance aligned by construction. Implementation: post-hoc
override in the eval layer (two lines in `run_logger.py` or `metrics.py`) — does not
touch the supervisor's production behavior. Higher signal per metric; removes the
spurious-alignment / genuine-conflict ambiguity entirely.

### label
Ground truth for classifier training. Set manually after reviewing the run.
- `true`: orchestrator routed correctly and outputs were appropriate.
- `false`: routing was wrong (over- or under-decomposed) regardless of output quality.
- `null`: unlabeled (not yet reviewed).

The label captures routing intent, not output quality. A run where all agents
produced excellent work but the decomposition was wrong is still `label = false`.

---

## 3. Cross-Case Summary (all 24 cases reviewed)

After twenty-two cases, the routing/acceptance relationship has saturated all variants:
- Both agree by luck (sd-04, sd-05) — alignment driven by over-decomposed agent deferring or truncating.
- Acceptance rewards out-of-scope work, lifting it above routing (sd-03, md-01, md-02, md-04).
- Acceptance inverts against routing — in-scope rejected, out-of-scope accepted (sd-06, md-05).
- Acceptance collapses to 0 on scope/deferral/misfiled-routing grounds while routing stays clean (md-03, md-07).
- Acceptance hits 1.0 while routing is mediocre (md-04).
- Inversion amplified at three expected domains (md-08): two in-scope domains rejected,
  one out-of-scope domain (ml_engineer — the one the note most pointedly excludes) accepted
  as "production-ready." acceptance_rate would actively mislead domain-selection if trusted.

In all fourteen, **routing_precision tracked scope notes correctly**. In none of them did
**acceptance_rate reliably track scope**. Its rejections are dominated by three distinct
drivers — ship-vs-defer, inter-task over-reach, and task-adherence/lane-discipline —
applied inconsistently within single cases. At three+ expected domains it can reject the
majority of correct domains while accepting an excluded one.

**Spec quality across all 24 cases:** sd-02 was the only case requiring a real
specification fix. The other twenty-three are correctly specified. coverage and
routing_precision are the trustworthy signals — with the bd-01/bd-02/bd-03 caveat that
they are trustworthy at the *set level* and blind to within-expected-set task→domain
misassignment.

**The md-09/md-10 controlled demonstration:** Both cases have routing = 0.75 (tied for
best multi-domain result, one spurious domain each). Acceptance behaves arbitrarily with
respect to scope in both — in opposite directions:
- md-09: required ml_engineer rejected (deferral), out-of-scope analytics rejected (scope-awareness punished).
- md-10: required devops_mlops rejected (factually inverted reason — see below), out-of-scope analytics accepted.
Same routing quality, opposite acceptance behavior on the out-of-scope domain. Acceptance
is not a function of decomposition quality. Hold routing fixed at 0.75 and acceptance
still does whatever per-agent behavior dictates.

**Matching scores, disjoint domains (md-11, md-13):** In both cases routing = 0.4 and
acceptance = 0.4 — but the domains behind each number share nothing. Routing's 0.4 comes
from the two correct domains; acceptance's 0.4 comes from two excluded infra domains. Both
required domains rejected; both excluded infra domains accepted. The maximal inversion is
now confirmed as a reproducible pattern, not a single anomaly. A matching numeric score
between the two metrics carries no information about scope alignment.

**New validator failure mode (md-11):** The ml_engineer was rejected by appeal to a
"compliance specialist" domain that does not exist in the six-domain taxonomy. The
validator is not applying scope notes inconsistently — it is manufacturing constraints
from outside the system's ontology entirely. Rejections cannot be trusted to stay within
the problem's domain model.

**Strongest factual contradiction in the suite (md-10):** devops_mlops (required) was
rejected for "crossing into application/infrastructure code." But the devops_mlops output
was a PagerDuty integration design with one Python metrics snippet — less application
code than the accepted software_dev agent. Meanwhile the accepted analytics agent crossed
into two other domains (rate limiter and PagerDuty wiring) in its opening paragraph.
The rejection reason does not match the output; it applies more accurately to the
analytics agent that was accepted.

**Caution against over-reading agreement (md-06):** When routing and acceptance
implicate the same domain, check the rejection reason — the alignment is typically
coincidental, driven by inter-task over-reach or deferral, not scope. The two metrics
do not converge as decomposition quality improves; they measure different things at
every quality level.

**bd-01 — only perfect case, and the routing set-based blindspot:**
Coverage = Routing = Acceptance = 1.0. All six domains hit, all accepted. The only run
in the suite where all three scored perfect. Yet the decomposition contained a real,
spec-relevant error: drift monitoring was assigned to devops_mlops when the spec's
boundary note explicitly assigns it to ml_engineer. Both are in expected_domains, so
routing's set intersection returned 1.0. The misassignment is invisible to coverage,
routing_precision, and acceptance_rate alike. It is only visible by reading the task
text against the boundary notes — which none of the metrics perform.
Additional nuance: the devops_mlops agent, handed the drift-monitoring task, silently
corrected the orchestrator by delivering A/B infrastructure (its correct lane) and
punting model concerns elsewhere. The validator accepted it for the A/B work. Acceptance
= 1.0 is consistent with good execution; it just tells you nothing about the routing
error. This is also the case where Fidelity (0.470, lowest in the suite) accidentally
signaled the misassignment: the drift-monitoring task text embedded poorly against the
devops agent's A/B output, pulling the average down. Fidelity was not designed for
this; it is a side effect of the two-task-one-output collision.

**bd-02 — chain shift and capstone evidence for the set-vs-assignment gap:**
Coverage = 1.0, Routing = 0.833, Acceptance = 0.833, Fidelity = 0.590.
The LLM invoked software_dev (spurious; spec excludes it) for "automate every Monday
and alert on failures," then slid every ML-axis responsibility one domain downstream:
training moved from data_scientist to ml_engineer; packaging + batch integration +
drift monitoring moved from ml_engineer to devops_mlops. Both in-set misassignments
are invisible to routing — all three involved domains (data_scientist, ml_engineer,
devops_mlops) are in expected_domains. Routing dropped to 0.833 solely because
software_dev is out of set; a reader seeing 0.833 would conclude "almost perfect, one
extra domain" and would miss that the decomposer also misassigned training and drift
ownership among the correct domains, which is the more serious error.
Acceptance = 0.833 matches routing numerically but for a different reason: software_dev
was rejected for non-delivery ("provided a framework... rather than the actual
orchestration design"), not scope. The agent opened by correctly stating "this is a
data engineering and ML ops problem masquerading as a software engineering problem"
and was penalized for not building the orchestration anyway — the scope-aware-penalty
pattern, sixth-plus occurrence.
bd-02 confirms two recurring failures: (1) the drift-ownership boundary (ml_engineer
owns drift; devops_mlops owns scheduling) has now been probed twice and failed both
times in the same direction — drift assigned to devops_mlops instead of ml_engineer;
(2) the "training always belongs to data_scientist" assertion from md-13 was violated
under the broader problem framing, with training assigned to ml_engineer and accepted.
bd-01 showed the set-vs-assignment gap silently (routing 1.0). bd-02 shows that even
when routing drops, the drop is entirely attributable to the out-of-set domain — the
in-set misassignments remain uncounted. Together they prove the metric responds only
to set membership, never to assignment correctness.

**bd-03 — two spurious domains, three pathologies, suite complete:**
Coverage = 1.0, Routing = 0.667, Acceptance = 0.833, Fidelity = 0.478.
The LLM invoked analytics and software_dev, both excluded. Routing = 0.667 (lowest in
the broad-domain group) correctly reflects two out-of-set domains. Three pathologies
occur simultaneously in this single run:

Pathology 1 — within-set misassignment, third occurrence (bd-01, bd-02, bd-03).
Promotion criteria (spec: data_scientist — "requires design, not just automation") was
assigned to ml_engineer. Feature drift detection (spec: ml_engineer — "drift monitoring
per model") was assigned to data_scientist. These two deliverables swapped domains
within the expected set; both data_scientist and ml_engineer appeared in the
decomposition, so routing sees nothing wrong. Routing's 0.667 is entirely explained by
analytics and software_dev being out of set; the criteria/drift swap is uncounted.
Third confirmation that routing is set-based and blind to task→domain assignment.

Pathology 2 — out-of-scope domain accepted (md-04/md-08 pattern). analytics is
explicitly excluded ("monitoring dashboard is model health owned by ml_engineer and
infra health owned by devops_mlops") yet was accepted — praised for "staying within its
analytics domain... focusing on model performance monitoring, dashboards." The analytics
agent even opened by correctly identifying "this is a system design problem masquerading
as an analytics problem," flagged handoffs to engineering specialists, then delivered the
model-performance-monitoring layer your spec assigns to ml_engineer. Accepted. Routing
correctly penalized analytics for being out of set; acceptance rewarded it for
lane-discipline within that out-of-set assignment. Same domain, opposite verdict from
the two metrics.

Pathology 3 — scope-expansion rejection (distinct from the deferral pattern). software_dev
was rejected for "exceeded its assigned domain by designing core MLOps architecture...
instead of focusing solely on documentation, runbooks, CLI tools." This is the
lane-discipline failure mode (md-07), not deferral: the agent delivered substantial
content but expanded into promotion-criteria design and drift-detection strategy that
belong to expected domains. This is one of the few cases where acceptance caught
something real — an out-of-scope domain that produced work belonging to expected
domains. The deferral control still holds: a software_dev agent that produced only
runbooks would likely have been accepted, yielding out-of-scope acceptance as in
md-04/md-08.

Fidelity = 0.478 (second-lowest, tied with bd-01 range). Mechanism: devops_mlops has
five tasks but one output (observability/logging). Four of the five tasks (Airflow
setup, MLflow deploy, promotion workflow, rollout) embedded poorly against that output.
Same multi-task-one-output collision as bd-01, scaled to five tasks.

**The metric picture — complete across all 24 cases:**
- coverage — tracks "are all expected domains present?" faithfully in all 24 cases.
- routing_precision — tracks set-level scope faithfully in all 24 cases, but bd-01,
  bd-02, and bd-03 prove it is blind to within-expected-set task→domain misassignment.
  The number reflects how many invoked domains were expected, not whether each
  deliverable went to the right one.
- acceptance_rate — does not track scope in any of the 24 cases. Driven by
  ship-vs-defer, truncation, lane-discipline, inter-task over-reach, and a coin-flip
  on scope-aware self-limitation. Inverts, scrambles, or coincidentally agrees with
  routing depending on per-agent behavior — never on decomposition correctness.
- fidelity — tracks task-vocabulary overlap; mostly a function of task breadth, output
  length, preamble, and truncation. Uncorrelated with run quality (bd-01, the only
  perfect run, scored lowest). Useful only as a within-case relative flag.

---

## 4. Recurring Failure Modes (as of sd-01–md-05)

**Keyword-triggered decomposition.** The orchestrator pattern-matches surface tokens
("Slack alert" → software_dev, "nightly" → devops_mlops, "Docker" → devops_mlops,
"SQL queries" → data_engineer) instead of reading the scope of the primary task.
All six cases show this.

**Agent deferral.** Agents preface responses with clarifying questions and partial
plans rather than delivering. The analytics agent in sd-04 produced zero plots; the
software_dev agent in sd-05 delivered nothing but a request for code artifacts; the
data_engineer in md-02 surfaced unknowns and was rejected while the data_scientist in
the same run pushed back on framing, delivered code, and was accepted. The "deferred
vs. delivered" criterion is the dominant driver of rejections across the suite, and it
is applied inconsistently: agents that push back and then deliver are accepted; agents
that push back and deliver less are rejected — but the threshold shifts case to case.
This is a property of the validator, not the test cases.

**Analytics-scope-aware-penalty concentration.** Across md-03, md-09, md-11, md-12, and
md-13, the analytics agent was rejected every time it flagged "is this the right
tool/approach?" before or alongside delivering the assigned work. In md-13 the analytics
agent's self-authored scope map matched the gold note almost word-for-word ("This is not
an analytics project... ML engineering + data engineering project with an analytics layer
on top") before being rejected for "crossing into ML/DS domains." The validator treats
senior-analyst scope-awareness as insubordination, even when the agent's scope reasoning
is correct and it also delivered the assigned artifact. Five consecutive cases; in all
five the excluded infra agents that opened with identical clarifying-question preambles
were accepted.

**Validator contradicting an explicit gold-note clause (md-13):** The data_scientist was
rejected on the reasoning that "the task was too specified for data-science judgment —
fine-tuning BERT is just implementation." But the spec's central clause says "training
and evaluation always belong to data_scientist regardless of how specified the approach
is" — written specifically to foreclose that reading. This is the clearest instance in
the suite of the validator applying the exact inverse of an explicit, deliberate spec
assertion.

**Scope-aware behavior is definitively non-deterministic (md-14):** In the same case,
ml_engineer was accepted for saying "this is not an ML problem" and data_scientist was
rejected for saying "there is no statistical task here" — structurally identical moves,
opposite verdicts. Five prior cases (md-03/md-09/md-11/md-12/md-13) punished this
behavior; md-14 both rewards and punishes it simultaneously. There is no rule; the
verdict is a coin-flip.

**acceptance crediting what routing penalizes (md-14):** ml_engineer was accepted for
agreeing it was out of scope, while routing correctly penalized it for being out of
scope. The two metrics pull apart on the same domain: routing says "spurious domain,
penalize"; acceptance says "correctly self-excluded, reward."

**Acceptance scrambled in both directions (md-14):** With all six domains invoked,
acceptance accepted and rejected within both the in-scope set and the out-of-scope set.
Not a clean inversion, not alignment — just noise. This is the natural terminal state
of a metric driven by inconsistent per-agent behavioral judgments when coverage is
maximal (all domains present).

**Total boundary collapse (md-07).** A second Acceptance = 0, but from a different and
consistent cause: all three agents ignored their assigned task slices and answered the
whole problem end-to-end, overlapping completely. The validator was factually correct in
all three rejections — each agent did produce the other agents' work. This isolates a
third acceptance driver distinct from ship-vs-defer and inter-task over-reach:
*task-adherence / lane-discipline* — did the agent do its assigned slice rather than the
whole job. Critically, the rejected artifacts were among the strongest in the suite
(solid Dockerfile, well-designed health endpoint) — they were rejected for redundancy,
not quality. Acceptance = 0 here does not mean "the work was bad"; it means the agents
didn't respect the orchestrator's task partition. This is the furthest yet from
"did the right domains do good work."

**Output truncation.** Agent output can be cut off mid-function, producing a rejection
for incompleteness rather than scope. sd-06: software_dev was rejected because the
implementation was truncated; the out-of-scope data_engineer agent happened to finish.
Truncation is a generation artifact, not a quality or scope signal. Check for cutoff
before reading a rejection as meaningful.

**Validator inconsistency.** Identical work is scored differently depending on which
domain label it was filed under (sd-02). The data_engineer agent in sd-06 opened with
"This is a straightforward endpoint design question" — it knew it was doing application
work, and the validator accepted it anyway, grading against the assigned task rather
than expected_domains. Root cause: the supervisor validates agents in isolation, without
seeing the full decomposition or the eval case's scope notes. Near-term fix: post-hoc
acceptance override in the eval layer — any agent whose domain is not in expected_domains
gets accepted = false regardless of output quality.
