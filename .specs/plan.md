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
| `analytics` | Analytics | EDA, metrics, dashboards, insight generation |
| `devops_mlops` | DevOps / MLOps | Infra, CI/CD, model serving, monitoring |
| `bi_agent` | Business Intelligence | SQL, reports, KPIs, data storytelling |
| `software_dev` | Software Development | APIs, services, integrations, tooling |

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

### Phase 3 — Full Agent Fleet
- [ ] `ml_engineer` agent
- [ ] `analytics` agent
- [ ] `devops_mlops` agent
- [ ] `bi_agent` agent
- [ ] `software_dev` agent

### Phase 4 — Triangle
- [ ] `Supervisor` class — validates outputs, challenges decompositions, participates in consensus
- [ ] Triangle consensus loop — any corner can reject or push back, decision confirmed on agreement
- [ ] Escape valve — after 3 iterations emit best-effort output with confidence score
- [ ] Multi-agent run: all agents in parallel, triangle converges outputs

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
