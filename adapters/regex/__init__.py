"""regex adapter — regex synthesis domain for the evolving-agents engine.

A program-synthesis domain where candidates are regex patterns and success is
graded by F1 against a hidden target's labeled examples (dates, emails, phones).
Like symreg, F1 has a continuous gradient and the memory-aware generator's
constraint-grafting makes each evolutionary step a visible tightening of the
pattern — from too-wide (`.*`) toward just-right (`[0-9]{4}-[0-9]{2}-[0-9]{2}`).
"""
from adapters.regex.adapter import RegexAdapter, REGEX_RULE_SPECS, make_execute
from adapters.regex.candidate import (
    RegexExpr, make_regex, generate_pool, generate_pool_aware, family_of,
)
from adapters.regex.env import evaluate, get_target, target_label, Target, TARGETS

__all__ = [
    "RegexAdapter", "REGEX_RULE_SPECS", "make_execute",
    "RegexExpr", "make_regex", "generate_pool", "generate_pool_aware", "family_of",
    "evaluate", "get_target", "target_label", "Target", "TARGETS",
]
