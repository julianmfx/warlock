# Agent Contracts
> *The settled boundary decisions that govern how Warlock decomposes problems.*
>
> Each entry is a rule that has been explicitly decided — not inferred from the code,
> not assumed from domain names. When the orchestrator or supervisor needs to reason
> about who owns what, this is the source of truth.
>
> A new entry is added whenever a boundary dispute is resolved — typically surfaced
> by an eval case where the domain split was non-obvious or initially wrong.

---

## data_scientist ↔ ml_engineer

**Decided in:** mt-11

### Rule

| data_scientist | ml_engineer |
|---|---|
| Problem formulation | Production validation |
| Experiment design | Packaging and registration |
| Feature analysis | Deployment and serving |
| Model training | Monitoring (drift, performance, data quality) |
| Evaluation and interpretation | Retraining pipelines |
| Verdict: "this works, here's why" | |

`data_scientist` owns the full **research cycle** — from "what should we try" to "here is a trained, evaluated model with a clear verdict."

`ml_engineer` owns the full **production cycle** — from "take this verdict" to "the model is running and monitored in prod."

### Handoff trigger

A **production artifact** — a batch scoring job, a serving endpoint, a registered model. Training and evaluation always belong to `data_scientist`, regardless of how specified the approach is. The moment the output is destined for production (scheduled job, deployment, registration), `ml_engineer` takes over.

### Key exclusions

- Training a model is **not** `ml_engineer` unless the approach is fully specified and the research question is closed.
- Feature importance analysis is **not** `ml_engineer` — it is interpretation of a research result, owned by `data_scientist`.
- Operational retraining on a fixed schedule (e.g. retrain weekly, promote if AUC improves) is **not** `data_scientist` — the research question is settled; this is production maintenance, owned by `ml_engineer` + `devops_mlops`.

### Edge cases

- **"Train and deploy"** in one sentence: split it. If there is a research question still open (new features, new approach, significance test), `data_scientist` leads training. If the approach is given and the goal is just to keep the model fresh, `ml_engineer` + `devops_mlops` own it.
- **Experiment tracking (MLflow, W&B):** tooling is `ml_engineer`; the experiments themselves are `data_scientist`.

---

*More boundaries will be added as eval cases surface disputes.*
