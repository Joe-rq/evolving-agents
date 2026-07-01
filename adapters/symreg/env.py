"""adapters/symreg/env.py — symbolic regression target + AST evaluator (stdlib only).

A candidate is a formula expression (a small AST over a fixed operator set).
"Execute" = fit/evaluate: does the formula explain a HIDDEN target function?
Unlike maze (binary-ish) or 2048 (binary gate), here success is graded by R²,
which has a continuous gradient from -inf → 1.0. That gradient is what makes
evolution VISIBLE: a trajectory climbs R² = 0.0 → 0.6 → 0.99 → 1.0, and each
step is a structurally new formula (not an invisible weight nudge).

Operator set (deliberately small + discrete):
  const(c)              — a constant leaf
  x                     — the input variable leaf
  add(a, b)             — a + b
  mul(a, b)             — a * b
  square(a)             — a^2
  sin(a)                — sin(a)

Families (the Factor-2 classification axis):
  poly    — uses square or mul as the dominant operator
  linear  — add/mul of x and const, no nonlinearity
  trig    — uses sin
  const   — only constants (degenerate)

Hidden targets (the thing the agent must rediscover). Fixed per run so the
trajectory is reproducible. Each is a closed-form over the same operator set,
so a perfect fit is always achievable IN PRINCIPLE — but random formulas
almost never hit it. That gap is the evolution space.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass


# --- AST nodes ---

@dataclass(frozen=True)
class Const:
    c: float

    def eval(self, x):
        return self.c

    def __str__(self):
        c = self.c
        return f"{int(c)}" if c == int(c) else f"{c:.2f}"


@dataclass(frozen=True)
class Var:
    """The input variable x."""

    def eval(self, x):
        return x

    def __str__(self):
        return "x"


@dataclass(frozen=True)
class Add:
    a: "Node"
    b: "Node"

    def eval(self, x):
        return self.a.eval(x) + self.b.eval(x)

    def __str__(self):
        return f"({self.a}+{self.b})"


@dataclass(frozen=True)
class Mul:
    a: "Node"
    b: "Node"

    def eval(self, x):
        return self.a.eval(x) * self.b.eval(x)

    def __str__(self):
        return f"({self.a}*{self.b})"


@dataclass(frozen=True)
class Square:
    a: "Node"

    def eval(self, x):
        v = self.a.eval(x)
        return v * v

    def __str__(self):
        return f"({self.a})^2"


@dataclass(frozen=True)
class Sin:
    a: "Node"

    def eval(self, x):
        return math.sin(self.a.eval(x))

    def __str__(self):
        return f"sin({self.a})"


Node = Const | Var | Add | Mul | Square | Sin


# --- hidden targets (the discovery goal) ---

TARGETS = {
    # name -> (formula-as-AST, human-readable, difficulty)
    "poly2_offset": (
        Add(Mul(Const(2.0), Square(Var())), Const(1.0)),
        "2*x^2 + 1", "medium",
    ),
    "poly2_sin": (
        Add(Square(Var()), Sin(Var())),
        "x^2 + sin(x)", "hard",
    ),
    "linear": (
        Add(Mul(Const(3.0), Var()), Const(2.0)),
        "3*x + 2", "easy",
    ),
}


def get_target(name: str = "poly2_offset"):
    return TARGETS[name][0]


def target_label(name: str = "poly2_offset"):
    return TARGETS[name][1]


# --- evaluation + R² ---

def _sample_points(n: int = 40, xmin: float = 0.0, xmax: float = 5.0):
    return [xmin + (xmax - xmin) * i / max(1, n - 1) for i in range(n)]


def r_squared(formula: Node, target: Node, xs=None) -> float:
    """R² of `formula` against `target` over sample points.

    R² <= 1.0 always. 1.0 = perfect fit; 0.0 = as good as the mean; <0 = worse.
    Numerically clamped to avoid -inf from exploding sin/overflow (a formula
    that blows up is just a bad fit, not a crash).
    """
    if xs is None:
        xs = _sample_points()
    ys_t = [target.eval(x) for x in xs]
    ybar = sum(ys_t) / len(ys_t)
    ss_tot = sum((y - ybar) ** 2 for y in ys_t) or 1.0
    ss_res = 0.0
    for x, yt in zip(xs, ys_t):
        try:
            yp = formula.eval(x)
            if not math.isfinite(yp):
                yp = 1e6  # blow-up → huge residual → near-worst R²
            yp = max(min(yp, 1e6), -1e6)
        except (ValueError, OverflowError, ZeroDivisionError):
            yp = 1e6
        ss_res += (yt - yp) ** 2
    return 1.0 - ss_res / ss_tot


def fit_quality(formula: Node, target: Node, xs=None) -> dict:
    """Full outcome for one candidate: R² + complexity + evidence tags."""
    xs = xs if xs is not None else _sample_points()
    r2 = r_squared(formula, target, xs)
    cx = _complexity(formula)
    kinds = set()
    if r2 < 0.0:
        kinds.add("wrong_sign")
    if r2 < 0.5 and cx <= 2:
        kinds.add("too_simple")
    if _has_blowup(formula, xs):
        kinds.add("numeric_instability")
    if 0.5 <= r2 < 0.9:
        kinds.add("partial_fit")
    return {"r2": r2, "complexity": cx, "evidence_kinds": kinds}


def _complexity(node: Node) -> int:
    """Node count — a proxy for formula size."""
    if isinstance(node, (Const, Var)):
        return 1
    if isinstance(node, (Square, Sin)):
        return 1 + _complexity(node.a)
    if isinstance(node, (Add, Mul)):
        return 1 + _complexity(node.a) + _complexity(node.b)
    return 1


def _has_blowup(formula: Node, xs) -> bool:
    """Detects formulas that explode (sin of huge arg, etc.)."""
    last = None
    for x in xs:
        try:
            v = formula.eval(x)
            if not math.isfinite(v) or abs(v) > 1e4:
                return True
            if last is not None and abs(v - last) > 1e3:
                return True
            last = v
        except (ValueError, OverflowError, ZeroDivisionError):
            return True
    return False


def _selftest():
    target = get_target("poly2_offset")
    print(f"target: {target_label('poly2_offset')}  (complexity={_complexity(target)})")
    tests = [
        ("perfect", target),
        ("poly2 no offset", Mul(Const(2.0), Square(Var()))),
        ("linear", Add(Mul(Const(5.0), Var()), Const(0.0))),
        ("const", Const(5.0)),
        ("sin blowup", Sin(Mul(Const(100.0), Var()))),
    ]
    xs = _sample_points()
    for name, f in tests:
        q = fit_quality(f, target, xs)
        print(f"  {name:18s} {str(f):30s} R²={q['r2']:+.3f} cx={q['complexity']} kinds={q['evidence_kinds']}")


if __name__ == "__main__":
    _selftest()
