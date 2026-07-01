"""adapters/symreg/adapter.py — the 5 evolving-agents protocols over formula ASTs.

Mirrors the 2048/maze adapter structure: RuleSpec list + evidence_kinds
projection + classify/motif_of mapping + make_execute. A candidate is an Expr
(see candidate.py); execute() fits it against a hidden target and grades by R².

Success grading (the graded gate that makes evolution visible):
  success = R² >= R2_SUCC          (0.90) — a strong fit
  weak    = R2_WEAK <= R² < R2_SUCC (0.50) — partial fit, on the right track
  fail    = R² < R2_WEAK            — wrong structure
This three-band gate is what maze lacked: there is ALWAYS a gradient to climb.
"""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.symreg.candidate import Expr, family_of, _reparse
from adapters.symreg.env import (
    fit_quality, r_squared, get_target, _complexity, _sample_points,
)

R2_SUCC = 0.90
R2_WEAK = 0.50

# Domain-defined projection rules (Factor 1/3 audit).
SYMREG_RULE_SPECS: list = [
    RuleSpec("trig_misfit", "wrong_sign", 3, "penalize", -0.40,
             "sin-based formulas structurally cannot fit polynomial targets"),
    RuleSpec("trig_misfit", "numeric_instability", 2, "block", -1.00,
             "sin of large args blows up numerically"),
    RuleSpec("const_trivial", "too_simple", 3, "penalize", -0.35,
             "bare constants can never fit a target with x-dependence"),
    RuleSpec("near_miss", "partial_fit", 3, "penalize", -0.20,
             "structurally close but missing a term (e.g. no offset)"),
]


def _ast_of(candidate):
    """Get the AST node from an Expr or fall back to reparsing its body."""
    if hasattr(candidate, "ast"):
        return candidate.ast
    return _reparse(getattr(candidate, "body", ""))


class SymregAdapter:
    """Implements the 5 evolving-agents protocols over Expr candidates."""

    def classify(self, candidate) -> str:
        """Factor 2 — family = dominant operator class (poly/trig/linear/const)."""
        if hasattr(candidate, "family"):
            return candidate.family
        ast = _ast_of(candidate)
        return family_of(ast) if ast is not None else "unknown"

    def extract(self, candidate) -> list:
        """Factor 1/5 — feature tokens for novelty + memory keying."""
        fam = self.classify(candidate)
        ast = _ast_of(candidate)
        cx = _complexity(ast) if ast is not None else 0
        return [f"fam:{fam}", f"cx:{min(cx, 8)}",
                f"depth:{min(cx, 4) // 2}"]

    def motif_of(self, candidate) -> str:
        """Factor 3 — predicted failure motif at scoring time.

        Structural risk classes that tend to fail together against a poly target.
        """
        fam = self.classify(candidate)
        ast = _ast_of(candidate)
        cx = _complexity(ast) if ast is not None else 0
        if fam == "trig":
            return "trig_misfit"
        if fam == "const" or cx <= 1:
            return "const_trivial"
        # a poly/linear that's close (cx>=4) but might be missing a term
        if fam in ("poly", "linear") and cx >= 4:
            return "near_miss"
        return ""

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        """Factor 1 — block already-tested formulas (exact body match)."""
        body = getattr(candidate, "body", str(candidate))
        if body in context.tested_bodies:
            return "already_tested"
        return ""

    def is_success(self, result) -> bool:
        return bool(result.get("success", False)) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak", False)) if isinstance(result, dict) else False


def make_execute(universe: str = "poly2_offset"):
    """Build the deterministic execute() callback.

    execute(candidate) fits the formula against the hidden target named by
    `universe` and grades R² into success/weak/fail. No stochasticity —
    fitting is pure evaluation over fixed sample points, so amnesic vs full
    would face identical outcomes (the control integrity the engine relies on).

    R² is also bucketed into an evidence_kind tag (r2:N) so the memory-aware
    generator can recover 'how good was each past attempt' from the ledger
    without needing the numeric field — the engine only persists booleans +
    evidence_kinds, so we encode the graded signal here.
    """
    target = get_target(universe)
    xs = _sample_points()

    def execute(candidate):
        ast = _ast_of(candidate)
        if ast is None:
            return {"success": False, "weak": False, "evidence_kinds": {"unparseable"},
                    "r2": -1.0, "complexity": 0}
        q = fit_quality(ast, target, xs)
        r2 = q["r2"]
        kinds = set(q["evidence_kinds"])
        # encode R² as a bucketed tag so the generator can read "positive clues"
        bucket = f"r2:{int(r2 * 10)}"  # r2:3 means R²~0.3
        kinds.add(bucket)
        return {
            "success": r2 >= R2_SUCC,
            "weak": R2_WEAK <= r2 < R2_SUCC,
            "evidence_kinds": kinds,
            "r2": round(r2, 4),
            "complexity": q["complexity"],
        }

    return execute


def _selftest():
    from adapters.symreg.candidate import make_expr
    from adapters.symreg.env import Const, Var, Add, Mul, Square, Sin
    target = "poly2_offset"
    print(f"target: {target} (hidden: 2*x^2+1)")
    tests = [
        ("perfect", Add(Mul(Const(2.0), Square(Var())), Const(1.0))),
        ("poly no offset", Mul(Const(2.0), Square(Var()))),
        ("linear", Add(Mul(Const(5.0), Var()), Const(0.0))),
        ("const", Const(5.0)),
        ("sin", Sin(Mul(Const(2.0), Var()))),
    ]
    exe = make_execute(target)
    for name, ast in tests:
        out = exe(make_expr(ast))
        print(f"  {name:16s} R²={out['r2']:+.3f} succ={out['success']} weak={out['weak']} kinds={sorted(out['evidence_kinds'])}")


if __name__ == "__main__":
    _selftest()
