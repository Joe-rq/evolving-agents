"""core/meta_learner.py — Factor 2 (score the search) + Factor 3 (learn failure modes).

The two mechanisms that make the engine *meta*-learning: it scores which
strategy class is worth searching (not just which candidate is good), and it
down-weights a whole failure-motif class rather than single instances.

Both are pure functions over Memory — no domain knowledge. The quantitative
specifics (which motifs exist, per-motif weights, cold-start order) are the
adapter's job; here we provide the generic scoring + strike + class-penalty.
"""
from __future__ import annotations

from math import sqrt

from core.memory import Memory


class MetaLearner:
    """Factor 2 branch scoring + Factor 3 class-level penalty."""

    def __init__(
        self,
        strike_threshold: int = 5,
        cold_start_score: float = 0.3,
        hit_rate_w: float = 0.5,
        recency_w: float = 0.2,
        freshness_w: float = 0.3,
    ) -> None:
        self.strike_threshold = strike_threshold
        self.cold_start_score = cold_start_score
        self.hit_rate_w = hit_rate_w
        self.recency_w = recency_w
        self.freshness_w = freshness_w

    def score_families(
        self,
        memory: Memory,
        universe: str = "",
        known_families: list[str] | None = None,
    ) -> dict[str, float]:
        """Factor 2 — score each strategy class by hit rate × recency × freshness.

        Strike rule: total >= strike_threshold with zero success → -1.0 (excluded).
        Families with no history get cold_start_score if passed in known_families.
        """
        stats = memory.family_stats(universe)
        scored: dict[str, float] = {}
        for family, s in stats.items():
            total = s["total"]
            success = s["success"]
            if total >= self.strike_threshold and success == 0:
                scored[family] = -1.0  # struck — stop searching this branch
                continue
            hit_rate = success / max(total, 1)
            recency = 1.0 if success > 0 else 0.0
            freshness = 1.0 / sqrt(max(total, 1))
            scored[family] = (
                self.hit_rate_w * hit_rate
                + self.recency_w * recency
                + self.freshness_w * freshness
            )
        if known_families:
            for fam in known_families:
                if fam not in scored:
                    scored[fam] = self.cold_start_score
        return scored

    def motif_penalty(
        self,
        candidate_motif: str,
        memory: Memory,
        universe: str = "",
        per_fail: float = 0.2,
        floor: float = -0.9,
    ) -> float:
        """Factor 3 — class-level penalty for a candidate whose motif has failed.

        Scales with the motif's failure count: one failure teaches the whole
        class (not just the instance). Adapter may override per_fail/floor per
        motif if some classes deserve harsher treatment.
        """
        if not candidate_motif:
            return 0.0
        fails = memory.motif_fail_counts(universe).get(candidate_motif, 0)
        if fails == 0:
            return 0.0
        return max(floor, -per_fail * fails)
