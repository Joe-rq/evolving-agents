"""core/novelty.py — Factor 5 (seek novelty, avoid crowding).

Three mechanisms that keep the search out of local optima:
  - novelty_score: how little a candidate overlaps past attempts (by feature)
  - crowding_penalty: candidates sharing a motif with already-shipped successes
  - exploration_lane: a low-score floor for orthogonal candidates

All take already-extracted features/motifs (the FeatureExtractor /
FailureMotifExtractor protocols produce those); this module is pure scoring.
"""
from __future__ import annotations

from core.memory import Memory


def novelty_score(candidate_features: list[str], memory: Memory, universe: str = "") -> float:
    """1.0 = completely new vs history; lower = overlaps existing attempts.

    Computes average feature-overlap with each past attempt, then 1 − overlap
    (capped so a fully-redundant candidate still scores 0.2, not 0).
    """
    if not candidate_features:
        return 1.0
    past = [a.features for a in memory.attempts(universe) if a.features]
    if not past:
        return 1.0
    cand_set = set(candidate_features)
    overlaps = [len(cand_set & set(p)) / len(cand_set) for p in past]
    avg_overlap = sum(overlaps) / len(overlaps)
    return 1.0 - min(avg_overlap, 0.8)


def crowding_penalty(
    candidate_motif: str,
    memory: Memory,
    universe: str = "",
    per_success: float = 0.15,
    floor: float = -0.45,
) -> float:
    """Penalty when the candidate's motif has already shipped successes.

    A motif that already worked is crowded — re-finding it is low value.
    """
    if not candidate_motif:
        return 0.0
    shipped = sum(1 for a in memory.successes(universe) if a.motif == candidate_motif)
    if shipped == 0:
        return 0.0
    return max(floor, -per_success * shipped)


def qualifies_exploration_lane(
    score: float, main_threshold: float, exploration_threshold: float, is_orthogonal: bool
) -> bool:
    """A candidate below the main execute floor may still run if it is
    structurally orthogonal and clears the lower exploration floor.

    This is the controlled-exploration escape hatch against greedy exploitation
    collapsing into a local optimum.
    """
    if score >= main_threshold:
        return False  # already qualifies the normal way
    return is_orthogonal and score >= exploration_threshold
