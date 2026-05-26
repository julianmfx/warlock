import json
from datetime import datetime, timezone
from pathlib import Path


class TraceLogger:
    def __init__(self, run_id: str, base_dir: str = "traces"):
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        path = Path(base_dir) / date
        path.mkdir(parents=True, exist_ok=True)
        self._path = path / f"{run_id}.jsonl"
        self.run_id = run_id

    def log(
        self,
        problem: str,
        agent: str,
        task: str,
        output: str,
        accepted: bool,
        reason: str,
        iteration: int,
    ):
        record = {
            "run_id": self.run_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "problem": problem,
            "agent": agent,
            "task": task,
            "output": output,
            "accepted": accepted,
            "reason": reason,
            "iteration": iteration,
        }
        with open(self._path, "a") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
