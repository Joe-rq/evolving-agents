"""core/memory.py — append-only ledger of attempts, universe-scoped.

Factor 1 (Remember your failures) lives here. Every attempt is persisted and
queryable; isolation is per universe so scars from one environment don't
pollute another — the mechanism behind TOP3000→TOP1000
(see examples/case-study-pond-switch.md).

The Memory stores Attempts whose outcome/family/motif/features/evidence were
already classified by the adapter protocols. Memory itself is pure data,
plus a `project_rules` entry point that turns the ledger into auditable Rule
objects (core/rules.py) — the Factor 1/3 upgrade.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Attempt:
    """One tried candidate + its outcome, classified by the adapter protocols."""
    body: str                                            # canonical candidate string
    universe: str                                        # environment key ("TOP3000", ...)
    success: bool                                        # passed the gate (ResultEvaluator)
    weak: bool = False                                   # weak-signal failure (ResultEvaluator)
    family: str = ""                                     # strategy class (CandidateClassifier)
    features: list[str] = field(default_factory=list)    # (FeatureExtractor)
    motif: str = ""                                      # failure motif (FailureMotifExtractor)
    evidence_kinds: set[str] = field(default_factory=set)  # domain failure tags for rule projection
    timestamp: str = ""                                  # caller-supplied (iso or monotonic)


class Memory:
    """Append-only, universe-scoped ledger of attempts."""

    def __init__(self) -> None:
        self._attempts: list[Attempt] = []

    def record(self, attempt: Attempt) -> None:
        self._attempts.append(attempt)

    # --- universe-scoped queries (the isolation that protects cross-pond) ---
    def attempts(self, universe: str = "") -> list[Attempt]:
        if not universe:
            return list(self._attempts)
        return [a for a in self._attempts if a.universe == universe]

    def has_tested(self, body: str, universe: str) -> bool:
        return any(a.body == body and a.universe == universe for a in self._attempts)

    def tested_bodies(self, universe: str) -> set[str]:
        return {a.body for a in self.attempts(universe)}

    def successes(self, universe: str = "") -> list[Attempt]:
        return [a for a in self.attempts(universe) if a.success]

    def failures(self, universe: str = "") -> list[Attempt]:
        return [a for a in self.attempts(universe) if not a.success]

    def weak_failures(self, universe: str = "") -> list[Attempt]:
        return [a for a in self.failures(universe) if a.weak]

    # --- aggregates consumed by the meta-learner (Factor 2 / 3) ---
    def family_stats(self, universe: str = "") -> dict[str, dict[str, int]]:
        """Per-family {total, success, fail} — feeds Factor 2 branch scoring."""
        stats: dict[str, dict[str, int]] = {}
        for a in self.attempts(universe):
            if not a.family:
                continue
            s = stats.setdefault(a.family, {"total": 0, "success": 0, "fail": 0})
            s["total"] += 1
            s["success" if a.success else "fail"] += 1
        return stats

    def motif_fail_counts(self, universe: str = "") -> dict[str, int]:
        """Per-motif failure count — feeds Factor 3 class-level penalty."""
        counts: dict[str, int] = {}
        for a in self.failures(universe):
            if a.motif:
                counts[a.motif] = counts.get(a.motif, 0) + 1
        return counts

    # --- Factor 1/3 upgrade: project the ledger into auditable Rule objects ---
    def project_rules(self, specs: list, universe: str = "") -> list:
        """Project this universe's attempts into Rule objects via domain RuleSpecs.

        See core/rules.py. Rules carry confidence + evidence_ids, so the engine
        can answer 'why was this candidate penalized?' with concrete failures.
        """
        from core.rules import project_rules as _project
        return _project(self.attempts(universe), specs, scope=universe or "ALL")

    def __len__(self) -> int:
        return len(self._attempts)
