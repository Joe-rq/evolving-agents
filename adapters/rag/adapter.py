"""adapters/rag/adapter.py — 5 protocols over RAG retrieval strategies."""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.rag.candidate import Strategy, family_of
from adapters.rag.env import evaluate, get_task

SCORE_SUCC = 0.85
SCORE_WEAK = 0.50

RAG_RULE_SPECS: list = [
    RuleSpec("chunk_too_large", "chunk_too_large", 2, "penalize", -0.40,
             "chunk_size > 500 loses precision — split smaller"),
    RuleSpec("threshold_too_low", "threshold_too_low", 2, "penalize", -0.35,
             "threshold < 0.4 admits too much noise"),
    RuleSpec("topk_too_large", "topk_too_large", 2, "penalize", -0.30,
             "top_k > 10 dilutes results"),
    RuleSpec("no_rerank", "no_rerank", 3, "penalize", -0.25,
             "no rerank step — precision suffers"),
]


def _config_of(candidate) -> dict:
    return getattr(candidate, "config", {})


class RAGAdapter:
    def classify(self, candidate) -> str:
        if hasattr(candidate, "family"):
            return candidate.family
        return family_of(_config_of(candidate))

    def extract(self, candidate) -> list:
        c = _config_of(candidate)
        return [f"fam:{self.classify(candidate)}",
                f"chunk:{c.get('chunk_size', 200)}",
                f"rerank:{int(c.get('rerank', False))}",
                f"th:{c.get('threshold', 0.7)}"]

    def motif_of(self, candidate) -> str:
        c = _config_of(candidate)
        if c.get("chunk_size", 200) > 500: return "chunk_too_large"
        if c.get("threshold", 0.7) < 0.4: return "threshold_too_low"
        if c.get("top_k", 5) > 10: return "topk_too_large"
        if not c.get("rerank", False): return "no_rerank"
        return ""

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        body = getattr(candidate, "body", str(candidate))
        if body in context.tested_bodies:
            return "already_tested"
        return ""

    def is_success(self, result) -> bool:
        return bool(result.get("success", False)) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak", False)) if isinstance(result, dict) else False


def make_execute(universe: str = "general_qa"):
    task = get_task(universe)

    def execute(candidate):
        config = _config_of(candidate)
        if not config:
            return {"success": False, "weak": False, "evidence_kinds": {"empty"}, "score": 0}
        r = evaluate(config, task)
        score = r["score"]
        kinds = set(r["evidence_kinds"])
        kinds.add(f"score:{int(score * 10)}")
        return {
            "success": score >= SCORE_SUCC,
            "weak": SCORE_WEAK <= score < SCORE_SUCC,
            "evidence_kinds": kinds,
            "score": score,
        }

    return execute
