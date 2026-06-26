"""core/protocols.py — the 5 domain-agnostic adapter protocols.

Each factor maps to protocol(s) the domain must implement. The engine
(memory / meta_learner / evolver / novelty) depends only on these protocols,
never on domain specifics.

    Factor 1 Remember your failures   → DeadEndDetector, FeatureExtractor
    Factor 2 Score the search          → CandidateClassifier
    Factor 3 Learn failure modes       → FailureMotifExtractor
    Factor 4 Pivot structure           → (engine-internal: evolver.py)
    Factor 5 Seek novelty              → FeatureExtractor (overlap → novelty)

A domain provides these by wrapping its existing functions in classes; see
adapters/wq/ for the quantitative reference adapter.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class DeadEndContext:
    """State the dead-end detector needs: which environment, what's been tried."""
    universe: str = ""
    tested_bodies: set[str] = field(default_factory=set)


@runtime_checkable
class CandidateClassifier(Protocol):
    """Factor 2 — Score the search, not the candidate.

    Map a candidate to its strategy class (a family / dimension / branch).
    The engine scores these classes by hit rate and steers generation
    toward high-EV directions."""

    def classify(self, candidate: Any) -> str: ...


@runtime_checkable
class FeatureExtractor(Protocol):
    """Factor 1 / 5 — extract comparable features from a candidate.

    Used for novelty scoring (overlap with history) and memory keying."""
    def extract(self, candidate: Any) -> list[str]: ...


@runtime_checkable
class FailureMotifExtractor(Protocol):
    """Factor 3 — Learn failure modes, not single failures.

    Map a candidate to a failure motif — a *class* of related candidates that
    tend to fail together. Empty string if the candidate has no known motif."""
    def motif_of(self, candidate: Any) -> str: ...


@runtime_checkable
class DeadEndDetector(Protocol):
    """Factor 1 — Remember your failures.

    Return a non-empty reason if this candidate is a known dead-end (already
    tested, known-bad structure, disabled pattern). Empty string = proceed."""
    def dead_end_reason(self, candidate: Any, context: DeadEndContext) -> str: ...


@runtime_checkable
class ResultEvaluator(Protocol):
    """Classify an outcome so the engine knows what to remember as failure vs win."""
    def is_success(self, result: Any) -> bool: ...
    def is_weak(self, result: Any) -> bool: ...


__all__ = [
    "DeadEndContext",
    "CandidateClassifier",
    "FeatureExtractor",
    "FailureMotifExtractor",
    "DeadEndDetector",
    "ResultEvaluator",
]
