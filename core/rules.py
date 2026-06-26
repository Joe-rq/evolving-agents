"""core/rules.py — declarative rule objects projected from the ledger.

Factor 1/3 upgrade: instead of implicit scoring functions, the ledger is
projected into explicit Rule objects carrying confidence + evidence
traceability. This is the machine-readable strategy memory; the projection
machinery is domain-agnostic, the domain specifics (which motifs, which
weights) are the adapter's job.

Division of labor:
  - engine (this module): Rule / RuleSpec dataclasses, the confidence curve,
    the projection loop. Domain-agnostic.
  - adapter: the actual RuleSpec list ("close_yield + corr_failed → block
    -0.8") and the evidence_kinds tags on each Attempt. Domain-specific.

This is what makes the engine *auditable* — a Rule can answer "why does this
candidate get penalized?" with concrete evidence ids, which is the honesty
edge over uncontrolled "self-evolution" marketing.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    """One executable rule, projected from ledger evidence."""
    motif: str
    scope: str                       # universe label, or "GLOBAL"
    action: str                      # "block" / "penalize" / "cooldown" / ...
    score_adjustment: float
    confidence: float
    evidence_count: int
    evidence_ids: tuple[str, ...]    # traceable to specific failures
    reason: str

    @property
    def rule_id(self) -> str:
        return f"{self.scope}:{self.motif}:{self.action}"


@dataclass(frozen=True)
class RuleSpec:
    """Domain-defined projection: when `motif` accumulates >= `min_evidence`
    attempts tagged with `evidence_kind`, emit a Rule with `action`/`adjustment`.

    The adapter owns these (they encode domain knowledge: which motifs exist,
    what failure kinds matter, how harsh each response is).
    """
    motif: str
    evidence_kind: str               # domain failure tag ("weak", "corr_failed", ...)
    min_evidence: int
    action: str
    adjustment: float
    reason: str = ""
    global_scope: bool = False       # cross-universe rule (fires across ponds)


def confidence(count: int, base: float = 0.55, step: float = 0.10, cap: float = 0.95) -> float:
    """Confidence grows with evidence count, capped. More failures → more trust."""
    return min(cap, base + step * max(count - 1, 0))


def project_rules(
    attempts: list,
    specs: list[RuleSpec],
    scope: str = "ALL",
) -> list[Rule]:
    """Project attempts into Rule objects via the domain's RuleSpecs.

    For each spec, count attempts whose motif matches AND whose evidence_kinds
    contain the spec's evidence_kind. If count >= min_evidence, emit a Rule
    carrying the evidence ids (capped at 6 for readability).
    """
    # aggregate (motif, evidence_kind) → evidence ids
    agg: dict[tuple[str, str], list[str]] = {}
    for a in attempts:
        motif = getattr(a, "motif", "") or ""
        if not motif:
            continue
        for kind in (getattr(a, "evidence_kinds", None) or set()):
            agg.setdefault((motif, kind), []).append(_attempt_id(a))

    rules: list[Rule] = []
    for spec in specs:
        ids = agg.get((spec.motif, spec.evidence_kind), [])
        if len(ids) < spec.min_evidence:
            continue
        rules.append(
            Rule(
                motif=spec.motif,
                scope="GLOBAL" if spec.global_scope else scope,
                action=spec.action,
                score_adjustment=spec.adjustment,
                confidence=confidence(len(ids)),
                evidence_count=len(ids),
                evidence_ids=tuple(ids[:6]),
                reason=spec.reason,
            )
        )
    return rules


def matching_rules(candidate_motif: str, rules: list[Rule]) -> list[Rule]:
    """All rules whose motif matches the candidate's motif."""
    if not candidate_motif:
        return []
    return [r for r in rules if r.motif == candidate_motif]


def rule_adjustment(candidate_motif: str, rules: list[Rule]) -> float:
    """Sum of non-block adjustments for matching rules (block is handled separately).

    Takes the harshest adjustment per motif to avoid double-counting one
    evidence cluster. Capped to [-1.0, 0.5].
    """
    matching = [r for r in matching_rules(candidate_motif, rules) if r.action != "block"]
    if not matching:
        return 0.0
    total = sum(r.score_adjustment for r in matching)
    return max(-1.0, min(0.5, total))


def rule_block_reason(candidate_motif: str, rules: list[Rule]) -> str:
    """Return the first block reason for the candidate's motif, or empty string."""
    for r in matching_rules(candidate_motif, rules):
        if r.action == "block":
            return f"rule_block:{r.rule_id}"
    return ""


def _attempt_id(a: object) -> str:
    """Best-effort id for evidence traceability; domain may use a richer one."""
    for attr in ("candidate_id", "expression_id", "body"):
        v = getattr(a, attr, None)
        if v:
            return str(v)
    return "(unknown)"


__all__ = [
    "Rule",
    "RuleSpec",
    "confidence",
    "project_rules",
    "matching_rules",
    "rule_adjustment",
    "rule_block_reason",
]
