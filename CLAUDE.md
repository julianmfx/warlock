# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

See `constitution.md` for the spirit, collaboration rules, and core principles of this project.

## Project

Warlock is a multi-agent AI platform built from scratch — no LangChain. It receives a raw problem, routes it to specialist agents via an orchestrator, and synthesizes a unified output. The architecture is intentionally layered and decoupled: agents never call each other directly; shared memory is the only communication bus.

## Stack

- Python 3.14, managed with `uv`
- LLM backend: Anthropic Claude API (use `claude-sonnet-4-6` as default model)
- Memory: in-process dict (phase 1), upgradeable to Redis/vector store later
- Serving: FastAPI (phase 5, not yet started)

## Commands

```bash
uv run main.py          # run the entrypoint
uv add <package>        # add a dependency
uv sync                 # install dependencies from lockfile
```

No test runner or linter is configured yet. When adding them, prefer `pytest` and `ruff`.

## Architecture

Four layers, built in order:

1. **Orchestrator** (`warlock/orchestrator.py`) — decomposes the problem, routes to agents, manages lifecycle
2. **Specialist Agents** (`warlock/agents/`) — one class per domain, each inherits from a base `Agent`; domains: `data_engineer`, `ml_engineer`, `analytics`, `devops_mlops`, `data_scientist`, `software_dev`
3. **Shared Memory** (`warlock/memory.py`) — a key-value store (`problem_statement`, `task_decomposition`, `agent_outputs`, `iteration`); the only way agents share state
4. **Supervisor** (`warlock/supervisor.py`) — validates agent outputs, challenges decompositions, participates in triangle consensus (Phase 4)

## Core principles (from plan.md)

- **One agent, one domain.** No agent crosses boundaries.
- **Memory is the bus.** Agents never call each other directly.
- **The triangle owns truth.** Orchestrator, Supervisor, and Agents are equal peers — any corner can reject or push back.
- **Cost discipline.** Default to `claude-haiku-4-5` for routing/classification tasks, `claude-sonnet-4-6` for reasoning, `claude-opus-4-7` only when depth demands it. Always use prompt caching (`cache_control`) on large shared context (system prompts, memory dumps). Track token spend per agent run.
- **Learn by doing.** Ship the simplest working version at each phase before designing the next. Every phase must produce something runnable.
- Build what *should* exist, not what already does.

## Build sequence

See `plan.md` for the phased checklist. Phases 1–3 are complete. Phase 4 is in progress: `Supervisor` ships (validates outputs, tracks tokens/timing); the consensus retry loop, escape valve, and parallel multi-agent run are still open. Known P0–P3 issues are tracked in `plan.md` under Phase 4.

A separate **evaluation track** is designed in `.specs/eval_ml_plan.md`: score each run on `[C, R, A, F]` (coverage, routing precision, acceptance rate, output relevance). Decisions D1–D8 are settled. The curated case suite (`warlock/eval/cases.py` — 24 cases spanning routing width, each carrying a `verified` flag) and the read-only logger (`warlock/eval/metrics.py`, `warlock/eval/run_logger.py`) are built; `log_run()` is wired into `main.py` and appends one feature row per run — stamped with run provenance (`git_sha`/`-dirty`, router model, temperature, token/timing spend) so re-baselines compare as a time series — to `eval_runs/<date>.jsonl`. The full-suite baseline is captured (`eval_runs/2026-06-04.jsonl`, 24 rows). Reviewing that baseline (`warlock/eval/EVAL_REFERENCE.md`, `warlock/eval/suite_notes.md`) found `coverage` and `routing_precision` trustworthy at the set level, `acceptance_rate` and `output_fidelity` not — and `routing_precision` blind to task→domain assignment within the expected set (the drift→devops_mlops misassignment passed undetected in all three broad cases). The track is now **reframed from measuring a run to training a small LLM (router-first)** — plan in `warlock/eval/training_eval_plan.md`. The **prompt-fix re-baseline control** (training plan §10 step 1) is captured: `Orchestrator.decompose` now carries a domain-ownership charter + the `agent_contracts.md` boundary rules and runs at `temperature=0`; re-running the suite improved routing precision on ~15/24 cases (one stable regression, md-12) and is recorded in `eval_runs/2026-06-07.jsonl`. A per-deliverable `assignment_accuracy` metric is built — now **embedding-based** (cosine of the gold deliverable vs the best task in its expected domain, `threshold=0.30`, calibrated offline in `warlock/eval/calibrate_assignment.py`; the keyword `match` field was removed). `gold_decomposition` targets are authored for the five discriminating cases (bd-01/bd-02/bd-03, md-12, md-13). A decompose-only **N-sample baseline** (`warlock/eval/run_baseline.py`) captured 24 cases × 5 samples to `eval_runs/nsample/2026-06-07.jsonl`, confirming `temperature=0` decompositions are non-deterministic — per-case numbers are read as means. Root-cause finding: every `assignment_accuracy` matching wart traces to a granularity mismatch (per-deliverable gold vs the orchestrator's one-paragraph-per-domain output); the real fix is making `decompose` emit `{deliverable, domain}` directly (exact, deterministic scoring that also matches the SFT target shape), deferred to the orchestrator/training rework. `.specs/next-steps.md` sequences the eval and consensus tracks across sessions. Domain boundaries resolved by eval cases are recorded in `warlock/eval/agent_contracts.md`.

## Behavioral guidelines

Reduce common LLM coding mistakes. These guidelines bias toward caution over speed — use judgment on trivial tasks. See `EXAMPLES.md` for annotated before/after examples of each principle.

### 1. Think Before Coding

Don't assume. Don't hide confusion. Surface tradeoffs.

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```
