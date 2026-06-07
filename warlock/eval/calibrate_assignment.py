"""Offline threshold calibration for the embedding-based assignment_accuracy.

Re-scores the captured N-sample decompositions locally (no API calls —
all-MiniLM runs on CPU). For every gold deliverable it computes the best
cosine similarity to a task *in the expected domain*, then shows where real
hits and misses separate so we can pick a threshold.

    uv run python -m warlock.eval.calibrate_assignment
"""

import json
from collections import defaultdict
from statistics import mean

from warlock.eval.cases import ALL_CASES
from warlock.eval.metrics import _cosine, _embedding

ROWS_PATH = "eval_runs/nsample/2026-06-07.jsonl"
THRESHOLDS = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]

GOLD = {c.id: c for c in ALL_CASES if c.gold_decomposition}

_cache: dict[str, object] = {}


def embed(text):
    if text not in _cache:
        _cache[text] = _embedding(text)
    return _cache[text]


def best_sim(deliverable: str, domain: str, task_decomposition: list[dict]):
    """Best similarity between the deliverable and any task in its domain.

    Returns None when the expected domain is absent from the decomposition
    (an automatic miss at every threshold)."""
    g = embed(deliverable)
    sims = [embed(t["task"]) for t in task_decomposition if t["domain"] == domain]
    return max((_cosine(g, e) for e in sims), default=None)


def main():
    rows = [json.loads(line) for line in open(ROWS_PATH)]
    rows = [r for r in rows if r["case_id"] in GOLD]

    # per (case, deliverable): list of best-sim across the case's samples
    by_deliverable: dict[tuple, list] = defaultdict(list)
    # per row: best-sim per gold (aligned to gold order), for the threshold sweep
    row_sims: list[tuple[str, list]] = []

    for r in rows:
        case = GOLD[r["case_id"]]
        vals = []
        for g in case.gold_decomposition:
            s = best_sim(g["deliverable"], g["domain"], r["task_decomposition"])
            vals.append(s)
            by_deliverable[(case.id, g["domain"], g["deliverable"])].append(s)
        row_sims.append((case.id, vals))

    print("== best similarity within expected domain (mean [min-max] over samples) ==")
    print("   sorted ascending — low values are candidate misses, high are hits\n")
    table = []
    for (cid, dom, deliv), vals in by_deliverable.items():
        present = [v for v in vals if v is not None]
        score = mean(present) if present else -1.0
        table.append((score, cid, dom, deliv, present, len(vals)))
    for score, cid, dom, deliv, present, n in sorted(table):
        if present:
            cell = f"{mean(present):.2f} [{min(present):.2f}-{max(present):.2f}]"
        else:
            cell = "DOMAIN ABSENT (auto-miss)"
        print(f"  {cid:>6} {dom:>14}  {cell:<22} {deliv}")

    print("\n== Assignment per case at each threshold (mean over 5 samples) ==")
    header = "  case  " + "".join(f"{t:>6}" for t in THRESHOLDS)
    print(header)
    per_case_rows = defaultdict(list)
    for cid, vals in row_sims:
        per_case_rows[cid].append(vals)
    for cid in sorted(per_case_rows):
        sample_vals = per_case_rows[cid]
        cells = []
        for t in THRESHOLDS:
            per_sample = [
                sum(1 for s in vals if s is not None and s >= t) / len(vals)
                for vals in sample_vals
            ]
            cells.append(f"{mean(per_sample):>6.2f}")
        print(f"  {cid:>6}" + "".join(cells))


if __name__ == "__main__":
    main()
