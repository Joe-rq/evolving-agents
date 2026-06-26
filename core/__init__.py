"""evolving-agents core — domain-agnostic self-evolution engine.

Five protocols (adapters fill these) + four engine modules:
    protocols.py     — the 5 adapter protocols (domain interface)
    memory.py        — append-only ledger, universe-scoped          [Factor 1]
    meta_learner.py  — score search branches, strike, class penalty  [Factor 2,3]
    evolver.py       — pivot policy (strike → switch structure)      [Factor 4]
    novelty.py       — novelty score + crowding penalty              [Factor 5]
"""
from core.protocols import (
    DeadEndContext,
    CandidateClassifier,
    FeatureExtractor,
    FailureMotifExtractor,
    DeadEndDetector,
    ResultEvaluator,
)

__all__ = [
    "DeadEndContext",
    "CandidateClassifier",
    "FeatureExtractor",
    "FailureMotifExtractor",
    "DeadEndDetector",
    "ResultEvaluator",
]
