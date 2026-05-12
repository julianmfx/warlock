# Warlock — Agent Specifications
> *One agent, one domain. Memory is the bus.*

---

## Spec Review Protocol

Every time progress is made on this project — after any agent is built, modified, or tested — do the following:

1. **Review** all files in `.specs/` to check for outdated information
2. **Update** this file to reflect the current state of each agent (planned, in-progress, done)
3. **Update** `plan.md` and `warlock_session.md` with decisions made during the agent build
4. **Analyze** what the next agent now requires given what was just shipped — adjust specs based on what was learned, not speculation

This keeps `.specs/` as the living source of truth for agent design.

---

## Base Agent

**File:** `warlock/agent.py`
**Status:** done — provider-agnostic, live API call confirmed, token tracking confirmed working

Every specialist agent inherits from this class.

```
Agent
├── name        → unique identifier (e.g. "data_engineer")
├── identity    → the agent's self-description / system prompt anchor
├── memory      → reference to the shared Memory instance
├── _client     → any LLMClient implementation (internal)
├── _model      → model string passed to the client (e.g. "claude-haiku-4-5-20251001")
├── run(task)   → calls client.complete(), writes output to agent_outputs, tracks token_spend
└── describe()  → debug helper: prints name, identity, memory state
```

**Model:** passed at construction — defaults to `claude-haiku-4-5-20251001` in `main.py`
**Caching:** handled inside the provider adapter — `AnthropicClient` adds `cache_control: ephemeral` on system prompt
**Token tracking:** `token_spend` dict written to memory after every run (`input_tokens`, `output_tokens`, `cache_read_tokens`)
**Next:** create `warlock/agents/data_engineer.py` — first specialist, inherits Agent

---

## Specialist Agents

| Agent | File | Domain | Status |
|---|---|---|---|
| `data_engineer` | `warlock/agents/data_engineer.py` | Pipelines, ingestion, transformation, schemas | planned |
| `ml_engineer` | `warlock/agents/ml_engineer.py` | Model design, training, evaluation, deployment | planned |
| `analytics` | `warlock/agents/analytics.py` | EDA, metrics, dashboards, insight generation | planned |
| `devops_mlops` | `warlock/agents/devops_mlops.py` | Infra, CI/CD, model serving, monitoring | planned |
| `bi_agent` | `warlock/agents/bi_agent.py` | SQL, reports, KPIs, data storytelling | planned |
| `software_dev` | `warlock/agents/software_dev.py` | APIs, services, integrations, tooling | planned |

---

## Agent Interface (contract)

Each specialist agent must:

1. **Read** `problem_statement` and `task_decomposition` from shared memory at the start of its run
2. **Act** within its domain only — no agent touches another's scope
3. **Write** its output to `agent_outputs[self.name]` in shared memory when done
4. **Track** token usage per run and write it to memory for cost accounting
5. **Flag** uncertainty or low-confidence outputs — this triggers the triangle consensus loop rather than silently emitting a weak answer

---

## Tools per Agent (planned)

### `data_engineer`
- `read_source` — inspect a data source schema or file
- `design_schema` — propose a target schema given a source
- `generate_pipeline` — produce a pipeline spec (e.g. dbt model, Airflow DAG, Spark job)
- `validate_pipeline` — check a pipeline for common issues

### `ml_engineer`
- `design_model` — propose model architecture for a given problem
- `write_training_script` — generate a training script skeleton
- `evaluate_model` — assess model outputs against metrics
- `write_deployment_config` — produce serving config (e.g. FastAPI endpoint, batch job)

### `analytics`
- `run_eda` — summarize a dataset (distributions, nulls, outliers)
- `define_metrics` — propose KPIs or metrics for a business question
- `generate_dashboard_spec` — describe a dashboard layout and charts

### `devops_mlops`
- `write_dockerfile` — produce a Dockerfile for a given service
- `write_ci_config` — generate a CI/CD pipeline config
- `write_monitoring_config` — propose alerting and observability setup

### `bi_agent`
- `write_sql` — produce a SQL query for a reporting question
- `design_report` — describe a report structure and data sources
- `define_kpis` — propose KPI definitions given a business context

### `software_dev`
- `design_api` — propose an API spec (endpoints, payloads, auth)
- `write_service` — generate a service skeleton (FastAPI, etc.)
- `write_integration` — produce integration code for a given external system

---

*v0.1 — oathbreaker*
