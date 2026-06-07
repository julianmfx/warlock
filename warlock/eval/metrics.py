from numpy import dot
from numpy.linalg import norm
from sentence_transformers import SentenceTransformer

_model = None


def _embedding(text: str) -> list[float]:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model.encode(text)


def _cosine(a, b) -> float:
    return float(dot(a, b) / (norm(a) * norm(b)))


def coverage(
    task_decomposition: list[dict], expected_domains: list[str] | None
) -> float | None:
    if expected_domains is None:
        return None
    invoked = {task["domain"] for task in task_decomposition}
    needed = set(expected_domains)
    metric = len(invoked & needed) / len(needed)
    return metric


def routing_precision(
    task_decomposition: list[dict], expected_domains: list[str] | None
) -> float | None:
    if expected_domains is None:
        return None
    invoked = {task["domain"] for task in task_decomposition}
    needed = set(expected_domains)
    if not invoked:
        return None
    metric = len(invoked & needed) / len(invoked)
    return metric


def acceptance_rate(validation_results: dict) -> float | None:
    if not validation_results:
        return None
    verdicts = [verdict["accepted"] for verdict in validation_results.values()]
    metric = sum(verdicts) / len(verdicts)
    return metric


def output_fidelity(
    task_decomposition: list[dict], agent_outputs: dict
) -> float | None:
    scores = []
    for task_entry in task_decomposition:
        domain = task_entry["domain"]
        task_text = task_entry["task"]
        output_text = agent_outputs.get(domain)
        if not output_text:
            continue
        task_embeddings = _embedding(task_text)
        output_embeddings = _embedding(output_text)
        score = dot(task_embeddings, output_embeddings) / (
            norm(task_embeddings) * norm(output_embeddings)
        )
        scores.append(score)
    if not scores:
        return None
    metric = sum(scores) / len(scores)
    return float(metric)


def assignment_accuracy(
    task_decomposition: list[dict],
    gold_decomposition: list[dict] | None,
    threshold: float = 0.30,
) -> float | None:
    """Per-deliverable routing accuracy via embedding similarity.

    A gold deliverable scores a hit when the orchestrator produced a task
    *in the expected domain* whose text is semantically close to the
    deliverable (cosine >= threshold). Embedding-based so it is robust to
    paraphrase. threshold=0.30 was calibrated against the 2026-06-07 N-sample
    decompositions (calibrate_assignment.py): correct on bd-01/bd-02/bd-03/md-13,
    one residual false miss on md-12 (short "CSV export" deliverable diluted in
    software_dev's multi-clause task). Re-calibrate when the gold set grows.
    """
    if not gold_decomposition:
        return None
    task_embeddings = [
        (t["domain"], _embedding(t["task"])) for t in task_decomposition
    ]
    hits = 0
    for gold in gold_decomposition:
        gold_embedding = _embedding(gold["deliverable"])
        sims = [
            _cosine(gold_embedding, emb)
            for domain, emb in task_embeddings
            if domain == gold["domain"]
        ]
        if sims and max(sims) >= threshold:
            hits += 1
    return hits / len(gold_decomposition)
