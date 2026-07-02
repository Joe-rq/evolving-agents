"""symreg adapter — symbolic regression domain for the evolving-agents engine.

A formula-discovery domain where candidates are AST expressions and success is
graded by R² against a hidden target. The graded gate (0→0.5→0.9→1.0) gives
evolution a continuous gradient to climb — unlike maze's low ceiling or 2048's
binary gate — and the memory-aware generator's AST-grafting makes each
evolutionary step a visible structural growth, not an invisible weight nudge.

See adapter.py (5 protocols + RuleSpecs), env.py (AST + R² + hidden targets),
candidate.py (baseline + memory-aware grafting generators).
"""
from adapters.symreg.adapter import SymregAdapter, SYMREG_RULE_SPECS, make_execute
from adapters.symreg.candidate import (
    Expr, make_expr, generate_pool, generate_pool_aware, family_of,
)
from adapters.symreg.env import (
    Const, Var, Add, Mul, Square, Sin, get_target, target_label,
    r_squared, TARGETS,
)

__all__ = [
    "SymregAdapter",
    "SYMREG_RULE_SPECS",
    "make_execute",
    "Expr",
    "make_expr",
    "generate_pool",
    "generate_pool_aware",
    "family_of",
    "Const", "Var", "Add", "Mul", "Square", "Sin",
    "get_target", "target_label", "r_squared", "TARGETS",
]
