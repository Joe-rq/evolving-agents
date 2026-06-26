"""adapters/mock/adapter.py — reference mock adapter (toy domain).

Shows how a domain implements the 5 core protocols. Candidates are simple
tagged objects; this exists so the engine has a runnable reference and so the
demo/tests don't depend on any real domain.

The real quantitative adapter lives in a **private host repo** and implements
these same five methods against a real domain — see
examples/case-study-pond-switch.md for what it produced.
evolving-agents itself stays domain-free.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from core.protocols import DeadEndContext


@dataclass
class MockCandidate:
    body: str
    family: str = "other"
    features: list[str] = field(default_factory=list)
    motif: str = ""


class MockAdapter:
    """Reference implementation of the 5 protocols over MockCandidate.

    A real adapter replaces each method with domain logic:
        classify      ← expression → economic family
        extract       ← expression → field tokens
        motif_of      ← expression → failure motif
        dead_end_reason ← known-bad-structure / already-tested check
        is_success/is_weak ← gate check on a result row
    """

    def classify(self, candidate) -> str:
        return candidate.family

    def extract(self, candidate) -> list[str]:
        return list(candidate.features)

    def motif_of(self, candidate) -> str:
        return candidate.motif

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        return "already_tested" if candidate.body in context.tested_bodies else ""

    def is_success(self, result) -> bool:
        return bool(result.get("success")) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak")) if isinstance(result, dict) else False
