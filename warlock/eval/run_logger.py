import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from warlock.eval.cases import EvalCase
from warlock.eval.metrics import (
    acceptance_rate,
    assignment_accuracy,
    coverage,
    output_fidelity,
    routing_precision,
)


def log_run(memory, case: EvalCase | None = None, base_dir: str = "eval_runs"):
    task_decomposition = memory.read("task_decomposition") or []
    agent_outputs = memory.read("agent_outputs") or {}
    validation_results = memory.read("validation_results") or {}
    problem = memory.read("problem_statement") or ""

    has_case = case is not None
    expected_domains = case.expected_domains if has_case else None

    row = {
        "run_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "problem": problem,
        "Coverage": coverage(task_decomposition, expected_domains),
        "Routing": routing_precision(task_decomposition, expected_domains),
        "Assignment": assignment_accuracy(
            task_decomposition, case.gold_decomposition if has_case else None
        ),
        "Acceptance": acceptance_rate(validation_results),
        "Fidelity": output_fidelity(task_decomposition, agent_outputs),
        "has_case": has_case,
        "case_id": case.id if has_case else None,
        "iteration": _max_iteration(validation_results),
        "task_decomposition": task_decomposition,
        "raw_outputs": agent_outputs,
        "validation_results": validation_results,
        "label": None,
    }

    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = Path(base_dir)
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"{date}.jsonl", "a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")

    return row


def _max_iteration(validation_results: dict) -> int:
    # today every agent runs at most once (iteration 0 or 1 blind retry)
    # once the consensus loop lands this will reflect real retry depth
    return 0
