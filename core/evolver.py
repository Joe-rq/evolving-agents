"""core/evolver.py — Factor 4 (pivot structure, not tactics).

Detects when the current structural frame is exhausted and emits a pivot
recommendation. It does NOT choose what to pivot to — that stays with the
adapter / human. This is the agent-proposes / human-approves split documented
in examples/case-study-pond-switch.md: the agent observed "TOP3000 is wrong for
these crowded signals," the human approved the universe switch.

Exhaustion signals (either triggers a pivot recommendation):
  - N strategy classes struck (zero success after enough tries)
  - a failure motif hit >= motif_strike_count times in the current universe
"""
from __future__ import annotations

from core.memory import Memory


class Evolver:
    """Factor 4 — detect frame exhaustion, recommend a structural pivot."""

    def __init__(self, family_strike_count: int = 2, motif_strike_count: int = 3) -> None:
        self.family_strike_count = family_strike_count
        self.motif_strike_count = motif_strike_count

    @staticmethod
    def struck_families(family_scores: dict[str, float]) -> list[str]:
        """Classes the MetaLearner has struck (score < 0)."""
        return [f for f, s in family_scores.items() if s < 0]

    def exhausted_motifs(self, memory: Memory, universe: str = "") -> list[str]:
        """Motifs that failed >= motif_strike_count times — a class-level stall."""
        return [
            m for m, c in memory.motif_fail_counts(universe).items()
            if c >= self.motif_strike_count
        ]

    def should_pivot(
        self, memory: Memory, universe: str, family_scores: dict[str, float]
    ) -> bool:
        if len(self.struck_families(family_scores)) >= self.family_strike_count:
            return True
        if self.exhausted_motifs(memory, universe):
            return True
        return False

    def pivot_recommendation(
        self, memory: Memory, universe: str, family_scores: dict[str, float]
    ) -> str:
        """A human-readable trigger reason — for the agent-proposes / human-approves loop."""
        strikes = self.struck_families(family_scores)
        if len(strikes) >= self.family_strike_count:
            return (
                f"{len(strikes)} strategy classes struck in '{universe}' "
                f"({', '.join(strikes[:3])}) — switch structural frame, not parameters."
            )
        motifs = self.exhausted_motifs(memory, universe)
        if motifs:
            return (
                f"Motif(s) {', '.join(motifs[:3])} failed >= {self.motif_strike_count}x "
                f"in '{universe}' — this is an environment problem, not a parameter one."
            )
        return ""
