"""evolving-agents core — domain-agnostic self-evolution engine.

Five protocols (adapters fill these) + ledger + rule projection + three engine modules:
    protocols.py     — 5 adapter protocols (domain interface)
    memory.py        — append-only ledger, universe-scoped          [Factor 1]
    rules.py         — declarative Rule objects projected from ledger [Factor 1/3 audit]
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
from core.memory import Memory, Attempt
from core.rules import (
    Rule,
    RuleSpec,
    project_rules,
    matching_rules,
    rule_adjustment,
    rule_block_reason,
)

__all__ = [
    "DeadEndContext",
    "CandidateClassifier",
    "FeatureExtractor",
    "FailureMotifExtractor",
    "DeadEndDetector",
    "ResultEvaluator",
    "Memory",
    "Attempt",
    "Rule",
    "RuleSpec",
    "project_rules",
    "matching_rules",
    "rule_adjustment",
    "rule_block_reason",
]
