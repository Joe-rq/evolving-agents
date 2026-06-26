"""core/engine.py — orchestrates the 5 factors + rules into one loop.

Ties memory / meta_learner / evolver / novelty / rules together with a domain
adapter (the 5 protocols). The adapter fills domain knowledge; the engine runs
the universal loop:

    score → block-check → sort → execute(callback) → record → pivot-check

execute is a callback the domain supplies (returns {success, weak,
evidence_kinds}); without it the engine dry-runs (scores only, records
hypothetical outcomes).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from core.memory import Attempt, Memory
from core.meta_learner import MetaLearner
from core.evolver import Evolver
from core.novelty import crowding_penalty, novelty_score
from core.protocols import DeadEndContext
from core.rules import RuleSpec, rule_adjustment, rule_block_reason


@dataclass
class ScoredCandidate:
    candidate: Any
    score: float
    family: str
    family_score: float
    novelty: float
    rule_adjustment: float
    crowding: float
    block_reason: str


class Engine:
    """The universal self-evolution loop, parameterized by a domain adapter."""

    def __init__(
        self,
        adapter,
        memory: Memory,
        rule_specs: list[RuleSpec],
        meta_learner: MetaLearner | None = None,
        evolver: Evolver | None = None,
        weights: dict[str, float] | None = None,
    ) -> None:
        self.adapter = adapter
        self.memory = memory
        self.rule_specs = rule_specs
        self.ml = meta_learner or MetaLearner()
        self.ev = evolver or Evolver()
        w = {"family": 0.3, "novelty": 0.3, "rule": 1.0, "crowding": 1.0}
        if weights:
            w.update(weights)
        self.weights = w

    def score_candidate(self, candidate: Any, universe: str) -> ScoredCandidate:
        family = self.adapter.classify(candidate)
        features = self.adapter.extract(candidate)
        motif = self.adapter.motif_of(candidate)
        rules = self.memory.project_rules(self.rule_specs, universe)
        family_scores = self.ml.score_families(self.memory, universe)
        family_score = family_scores.get(family, self.ml.cold_start_score)

        nov = novelty_score(features, self.memory, universe)
        r_adj = rule_adjustment(motif, rules)
        crowd = crowding_penalty(motif, self.memory, universe)

        # block = rule-projected (Factor 1/3) OR adapter-known dead-end (Factor 1)
        rule_block = rule_block_reason(motif, rules)
        ctx = DeadEndContext(universe=universe, tested_bodies=self.memory.tested_bodies(universe))
        dead_end = self.adapter.dead_end_reason(candidate, ctx)
        block = rule_block or dead_end

        score = (
            self.weights["family"] * max(family_score, 0.0)
            + self.weights["novelty"] * nov
            + self.weights["rule"] * r_adj
            + self.weights["crowding"] * crowd
        )
        return ScoredCandidate(candidate, score, family, family_score, nov, r_adj, crowd, block)

    def run(
        self,
        candidates: list,
        universe: str,
        execute: Callable | None = None,
        max_execute: int = 3,
    ) -> dict:
        """One mining round: score all → drop blocked → sort → execute top → record → pivot-check."""
        scored = [self.score_candidate(c, universe) for c in candidates]
        eligible = [s for s in scored if not s.block_reason]
        eligible.sort(key=lambda s: s.score, reverse=True)
        to_run = eligible[:max_execute]

        executed: list = []
        for sc in to_run:
            outcome = execute(sc.candidate) if execute else None
            success = bool(outcome.get("success", False)) if outcome else False
            weak = bool(outcome.get("weak", False)) if outcome else False
            evidence = set(outcome.get("evidence_kinds", set())) if outcome else set()
            self.memory.record(
                Attempt(
                    body=getattr(sc.candidate, "body", str(sc.candidate)),
                    universe=universe,
                    success=success,
                    weak=weak,
                    family=sc.family,
                    features=self.adapter.extract(sc.candidate),
                    motif=self.adapter.motif_of(sc.candidate),
                    evidence_kinds=evidence,
                )
            )
            executed.append((sc, outcome))

        family_scores = self.ml.score_families(self.memory, universe)
        pivot = self.ev.should_pivot(self.memory, universe, family_scores)
        recommendation = (
            self.ev.pivot_recommendation(self.memory, universe, family_scores) if pivot else ""
        )
        return {
            "scored": scored,
            "executed": executed,
            "pivot": pivot,
            "pivot_recommendation": recommendation,
        }
