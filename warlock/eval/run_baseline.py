"""Decompose-only N-sample routing baseline.

Samples the orchestrator's router (`decompose`) N times per case and logs one
routing-only row per sample. Agents never run, so Acceptance/Fidelity stay null
and this isolates the routing target the training reframe cares about — far
cheaper than full `orchestrator.run()`. Rows land in eval_runs/nsample/<date>.jsonl
to keep them separate from the single-sample baselines.

    uv run python -m warlock.eval.run_baseline --samples 5
    uv run python -m warlock.eval.run_baseline --samples 8 --cases md-12,bd-02,bd-03,md-13
"""

import argparse
import json
from statistics import mean

from warlock.agents.analytics import AnalyticsAgent
from warlock.agents.data_engineer import DataEngineerAgent
from warlock.agents.data_scientist import DataScientistAgent
from warlock.agents.devops_mlops import DevOpsMLOpsAgent
from warlock.agents.ml_engineer import MLEngineerAgent
from warlock.agents.software_dev import SoftwareDevAgent
from warlock.eval.cases import ALL_CASES
from warlock.eval.run_logger import log_run
from warlock.memory import Memory
from warlock.orchestrator import Orchestrator
from warlock.providers.anthropic import AnthropicClient
from warlock.supervisor import Supervisor

MODEL = "claude-haiku-4-5-20251001"


def build_orchestrator():
    m = Memory()
    client = AnthropicClient()
    supervisor = Supervisor(memory=m, client=client, model=MODEL)
    orchestrator = Orchestrator(
        memory=m, client=client, model=MODEL, supervisor=supervisor
    )
    for agent_cls in (
        AnalyticsAgent,
        DataEngineerAgent,
        DataScientistAgent,
        DevOpsMLOpsAgent,
        MLEngineerAgent,
        SoftwareDevAgent,
    ):
        orchestrator.register(agent_cls(memory=m, client=client, model=MODEL))
    return m, orchestrator


def _fmt(values):
    vals = [v for v in values if v is not None]
    if not vals:
        return "n/a"
    return f"{mean(vals):.2f} [{min(vals):.2f}-{max(vals):.2f}]"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=int, default=5, help="samples per case")
    parser.add_argument(
        "--cases", default="", help="comma-separated case ids; default = all"
    )
    args = parser.parse_args()

    wanted = {c.strip() for c in args.cases.split(",") if c.strip()}
    cases = [c for c in ALL_CASES if not wanted or c.id in wanted]

    m, orchestrator = build_orchestrator()

    for case in cases:
        rows = []
        for i in range(args.samples):
            try:
                tasks = orchestrator.decompose(case.problem)
                m.write("problem_statement", case.problem)
                m.write("task_decomposition", tasks)
                rows.append(log_run(m, case=case, base_dir="eval_runs/nsample"))
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"  {case.id} sample {i}: skipped ({type(e).__name__}: {e})")
        print(
            f"{case.id:>6}  n={len(rows):<2} "
            f"C={_fmt(r['Coverage'] for r in rows):<16} "
            f"R={_fmt(r['Routing'] for r in rows):<16} "
            f"A={_fmt(r['Assignment'] for r in rows)}"
        )


if __name__ == "__main__":
    main()
