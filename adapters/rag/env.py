"""adapters/rag/env.py — RAG retrieval strategy evaluation (stdlib only).

A candidate is a retrieval strategy CONFIG (not keywords). This is the key
insight: RAG's evolution space isn't "which keywords to search" (too coarse —
one keyword hits ceiling), but "how to structure the retrieval pipeline"
(chunk size, rerank, threshold, top_k, query expansion).

The cost model simulates how each config choice affects retrieval quality,
based on known RAG best practices. No real embeddings — a deterministic
rule-based simulator, same design as SQL's cost model.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RAGTask:
    """A retrieval optimization task."""
    name: str
    description: str
    optimal: dict    # the ideal config (agent never sees this)


TASKS = {
    "general_qa": RAGTask(
        "general_qa",
        "General QA over a document corpus",
        {"chunk_size": 150, "rerank": True, "query_expand": True, "threshold": 0.7, "top_k": 4},
    ),
    "precise_lookup": RAGTask(
        "precise_lookup",
        "Precise fact lookup (high precision needed)",
        {"chunk_size": 100, "rerank": True, "query_expand": False, "threshold": 0.8, "top_k": 3},
    ),
}


def get_task(name: str) -> RAGTask:
    return TASKS[name]


def evaluate(strategy: dict, task: RAGTask) -> dict:
    """Evaluate a retrieval strategy config. Returns score in [0, 1].

    Based on RAG best practices:
      - chunk_size: 100-200 optimal (too large loses precision, too small loses context)
      - rerank: always improves precision
      - query_expand: improves recall slightly
      - threshold: 0.6-0.8 optimal (too low = noise, too high = misses)
      - top_k: 3-5 optimal (too many = diluted, too few = missed)
    """
    score = 0.4  # baseline

    cs = strategy.get("chunk_size", 200)
    if 100 <= cs <= 200:
        score += 0.2
    elif 50 <= cs < 100 or 200 < cs <= 500:
        score += 0.05
    elif cs > 500:
        score -= 0.15
    elif cs < 50:
        score -= 0.1

    if strategy.get("rerank", False):
        score += 0.15

    if strategy.get("query_expand", False):
        score += 0.05

    th = strategy.get("threshold", 0.7)
    if 0.6 <= th <= 0.8:
        score += 0.1
    elif th < 0.4:
        score -= 0.15
    elif th > 0.9:
        score -= 0.05

    tk = strategy.get("top_k", 5)
    if 3 <= tk <= 5:
        score += 0.1
    elif tk > 10:
        score -= 0.1
    elif tk > 5:
        score -= 0.03

    score = max(0.0, min(1.0, score))
    issues = set()
    if cs > 500: issues.add("chunk_too_large")
    elif cs < 50: issues.add("chunk_too_small")
    if th < 0.4: issues.add("threshold_too_low")
    elif th > 0.9: issues.add("threshold_too_high")
    if tk > 10: issues.add("topk_too_large")
    if not strategy.get("rerank", False): issues.add("no_rerank")

    return {"score": round(score, 4), "evidence_kinds": issues}


def _selftest():
    print("=== RAG strategy evaluator selftest ===")
    for tname in ("general_qa",):
        t = get_task(tname)
        print(f"\ntask: {tname} ({t.description})")
        tests = {
            "naive": {"chunk_size": 1000, "rerank": False, "query_expand": False, "threshold": 0.3, "top_k": 20},
            "bad_chunk": {"chunk_size": 500, "rerank": False, "query_expand": False, "threshold": 0.5, "top_k": 10},
            "better": {"chunk_size": 200, "rerank": False, "query_expand": False, "threshold": 0.7, "top_k": 5},
            "good": {"chunk_size": 150, "rerank": True, "query_expand": False, "threshold": 0.7, "top_k": 5},
            "optimal": {"chunk_size": 150, "rerank": True, "query_expand": True, "threshold": 0.7, "top_k": 4},
        }
        for label, s in tests.items():
            r = evaluate(s, t)
            print(f"  {label:12s} score={r['score']:.2f} issues={sorted(r['evidence_kinds']) or 'none'}")


if __name__ == "__main__":
    _selftest()
