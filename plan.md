# Warlock — Build Plan
> *An oathbreaker. A multi-agent platform that resolves problems and creates new realities.*

---

## Vision

Warlock is a multi-agent AI platform operating in the Data & AI domain. It receives a raw problem, decomposes it, routes work to specialist agents, and synthesizes a unified output — a new reality better than any single model could produce alone.

---

## Architecture

### Layer 1 — Orchestrator
`warlock.orchestrator`

The brain of the system. Responsibilities:
- Receive the raw problem statement
- Decompose it into sub-tasks
- Decide which agents run and in what order
- Manage agent lifecycle (spawn, timeout, retry)
- Write decomposition into shared memory

---

### Layer 2 — Specialist Agents

Each agent owns exactly one domain. No agent crosses into another's territory.

| Agent | Domain | Responsibilities |
|---|---|---|
| `data_engineer` | Data Engineering | Pipelines, ingestion, transformation, warehousing |
| `ml_engineer` | Machine Learning | Model design, training, evaluation, deployment |
| `analytics` | Analytics | EDA, metrics, dashboards, insight generation |
| `devops_mlops` | DevOps / MLOps | Infra, CI/CD, model serving, monitoring |
| `bi_agent` | Business Intelligence | SQL, reports, KPIs, data storytelling |
| `software_dev` | Software Development | APIs, services, integrations, tooling |

---

### Layer 3 — Shared Memory

A key-value context store that all agents read from and write to during a run. This is how agents communicate without direct coupling.

| Key | Description |
|---|---|
| `problem_statement` | The original raw input |
| `task_decomposition` | The orchestrator's breakdown of sub-tasks |
| `agent_outputs` | Results written by each specialist agent |
| `iteration` | Current loop count (for self-correcting runs) |

---

### Layer 4 — Synthesizer
`warlock.synthesizer`

The final layer. Responsibilities:
- Collect all agent outputs from shared memory
- Resolve conflicts between agents
- Merge results into a single coherent answer
- Deliver the new reality

---

## Build Sequence

### Phase 1 — Core (Start here)
- [ ] `Orchestrator` class in Python — problem decomposition logic, agent registry, routing engine
- [ ] Shared `Memory` layer — key-value context object agents read/write during a run
- [ ] Base `Agent` class — interface every specialist agent inherits from

### Phase 2 — First Agent
- [ ] `data_engineer` agent — generates pipelines, SQL transforms, schema designs
- [ ] Agent registration into the orchestrator
- [ ] End-to-end test: problem → orchestrator → `data_engineer` → memory → synthesizer → output

### Phase 3 — Full Agent Fleet
- [ ] `ml_engineer` agent
- [ ] `analytics` agent
- [ ] `devops_mlops` agent
- [ ] `bi_agent` agent
- [ ] `software_dev` agent

### Phase 4 — Synthesizer
- [ ] `Synthesizer` class — merge strategy, conflict resolution logic
- [ ] Multi-agent run: all agents in parallel, synthesizer converges outputs

### Phase 5 — Platform
- [ ] CLI interface to submit problems to Warlock
- [ ] Logging and observability per agent
- [ ] Iterative runs (agents can loop until output is accepted)

---

## Principles

- **One agent, one domain.** No agent crosses boundaries.
- **Memory is the bus.** Agents never call each other directly.
- **The synthesizer owns truth.** It has final say on the output.
- **Oathbreaker mindset.** Warlock does not default to what exists. It builds what should exist.
- **Cost discipline.** Every agent call must justify its token spend. Use the cheapest model that can do the job (e.g. Haiku for routing/classification, Sonnet for reasoning, Opus only when depth demands it). Cache aggressively with prompt caching. Measure cost per run.
- **Learn by doing.** Ship the simplest working version first, then iterate. Don't design the full system before writing any code. Each phase should produce something runnable that teaches you what the next phase actually needs.

---

## Stack (proposed)

- Language: Python
- Agent framework: custom (no LangChain dependency at core)
- LLM backend: Anthropic Claude API
- Memory: in-process dict → upgrade to Redis or vector store as needed
- Serving: FastAPI (Phase 5)

---

*v0.1 — oathbreaker*
