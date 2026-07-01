"""adapters/symreg/candidate.py — formula candidates + generators.

A candidate is an Expr wrapping an AST (see env.py). The body string is the
canonical AST string (so dead_end dedup works). Family = the dominant operator
class — the Factor-2 axis the engine steers generation along.

Two generators, same split as maze:
  generate_pool(round_idx, seed, n)           — memory-INdependent baseline.
  generate_pool_aware(memory, ..., target)    — memory-AWARE evolution.

The aware generator's extrapolation is GROWTH, not recombination: it takes a
winning formula's AST and GRAFTS a new subtree onto it (add a const offset,
wrap in a deeper op, multiply by a sibling). This is discrete structural
growth — each child is visibly more complex than its parent, climbing the R²
gradient toward the target. That is what "evolution" looks like here.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from adapters.symreg.env import (
    Const, Var, Add, Mul, Square, Sin, Node, _complexity,
)


@dataclass(frozen=True)
class Expr:
    """One candidate: an AST + its canonical body string + lineage."""
    ast: Node
    body: str
    parent_body: str = ""          # the winner this was extrapolated from
    graft: str = ""                # what structural graft was applied
    inherited: tuple = ()          # which sub-expressions were kept from parent

    @property
    def family(self) -> str:
        return family_of(self.ast)

    def to_json(self) -> dict:
        return {
            "body": self.body,
            "formula": str(self.ast),
            "family": self.family,
            "complexity": _complexity(self.ast),
            "parent_body": self.parent_body,
            "graft": self.graft,
            "inherited": list(self.inherited),
        }


def make_expr(ast: Node, parent_body: str = "", graft: str = "",
              inherited: tuple = ()) -> Expr:
    return Expr(ast=ast, body=str(ast), parent_body=parent_body,
                graft=graft, inherited=inherited)


# --- family classification (Factor 2) ---

def family_of(ast: Node) -> str:
    """Dominant operator family: poly / trig / linear / const.

    poly wins if any square/mul appears; trig if sin appears; linear if only
    add/mul over x+const; const if no x at all.
    """
    has_square = has_mul = has_sin = has_x = False

    def walk(n):
        nonlocal has_square, has_mul, has_sin, has_x
        if isinstance(n, Const):
            return
        if isinstance(n, Var):
            has_x = True
            return
        if isinstance(n, Square):
            has_square = True
            walk(n.a)
        if isinstance(n, Sin):
            has_sin = True
            walk(n.a)
        if isinstance(n, Mul):
            has_mul = True
            walk(n.a); walk(n.b)
        if isinstance(n, Add):
            walk(n.a); walk(n.b)

    walk(ast)
    if has_sin:
        return "trig"
    if has_square:
        return "poly"
    if has_mul and has_x:
        return "linear"
    if has_x:
        return "linear"
    return "const"


# --- random AST generation (the primitives both generators use) ---

def _rand_const(rng: random.Random) -> Const:
    # small integer consts, biased toward [-3, 3] where most fit-critical
    # coefficients live (the hidden targets use coeffs like 2, 1, 3).
    return Const(float(rng.randint(-3, 4)))


def _rand_ast(rng: random.Random, depth: int, max_depth: int) -> Node:
    """Grow a random AST. depth-bounded so complexity stays tractable."""
    if depth >= max_depth or (depth > 0 and rng.random() < 0.4):
        # leaf
        return Var() if rng.random() < 0.5 else _rand_const(rng)
    op = rng.choice(["add", "mul", "square", "sin"])
    if op == "add":
        return Add(_rand_ast(rng, depth + 1, max_depth), _rand_ast(rng, depth + 1, max_depth))
    if op == "mul":
        return Mul(_rand_ast(rng, depth + 1, max_depth), _rand_ast(rng, depth + 1, max_depth))
    if op == "square":
        return Square(_rand_ast(rng, depth + 1, max_depth))
    return Sin(_rand_ast(rng, depth + 1, max_depth))


# --- baseline generator (memory-independent) ---

def generate_pool(round_idx: int, seed: int, n: int = 10, max_depth: int = 2) -> list:
    """Deterministic, memory-INdependent pool of random formulas.

    Mixes depths so both simple (linear/const) and nonlinear (poly/trig)
    families appear. Deterministic for (round_idx, seed). Never reads Memory.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool = []
    # guarantee family diversity: one shallow-ish of each archetype
    archetypes = [
        Mul(_rand_const(rng), Var()),                      # linear
        Mul(_rand_const(rng), Square(Var())),              # poly
        Sin(Mul(_rand_const(rng), Var())),                 # trig
        _rand_const(rng),                                   # const
    ]
    for a in archetypes:
        pool.append(make_expr(a))
    for _ in range(max(0, n - len(archetypes))):
        d = rng.choice([1, 1, 2, 2, 3])
        pool.append(make_expr(_rand_ast(rng, 0, d)))
    rng.shuffle(pool)
    return pool


# --- memory-AWARE generator (evolution: graft onto winners) ---

def _graft(parent: Node, rng: random.Random) -> tuple:
    """Apply ONE structural graft to a winning formula's AST.

    Returns (new_ast, graft_description). Each graft is a discrete structural
    step that climbs complexity by exactly one operation — the unit of
    evolutionary growth in this domain.

    Graft distribution is NOT uniform: add_const / mul_const are weighted
    highest because scaling + offsetting are the operations that turn a
    structurally-correct-but-magnitude-wrong formula (e.g. x*x vs 2*x²+1)
    into a fit. The structural grafts (square/sin/sibling) are kept but
    rarer — they're for exploring new shape families, not refining magnitude.
    """
    kind = rng.choices(
        ["add_const", "mul_const", "square_wrap", "add_sibling", "sin_wrap"],
        weights=[5, 5, 2, 3, 1],  # bias toward magnitude-refining ops
    )[0]

    if kind == "add_const":
        c = _rand_const(rng)
        return Add(parent, c), f"+{c}"
    if kind == "mul_const":
        c = _rand_const(rng)
        if c.c == 0:
            c = Const(1.0)  # avoid zeroing the formula
        return Mul(parent, c), f"*{c}"
    if kind == "square_wrap":
        return Square(parent), "^2"
    if kind == "add_sibling":
        sib = _rand_ast(rng, 0, rng.choice([1, 2]))
        return Add(parent, sib) if rng.random() < 0.5 else Add(sib, parent), f"+({sib})"
    return Sin(parent), "sin-wrap"


def generate_pool_aware(
    memory,
    round_idx: int,
    seed: int,
    universe: str,
    n: int = 10,
    explore_ratio: float = 0.3,
    max_depth: int = 4,
) -> list:
    """Memory-AWARE evolution generator: graft new structure onto winners.

    What it does that generate_pool cannot:
      1. Reads memory.attempts(universe) and recovers each past formula's R²
         from the bucketed `r2:N` evidence_kind the adapter stamps on. ANY
         formula with R² > 0 is a positive clue (not just hard successes) —
         evolution seeds from weak/partial fits, which is how the gradient
         gets climbed in practice.
      2. Picks the best-R² roots and GRAFTS one structural op onto each —
         add a const offset, square, attach a sibling. Each child is one
         structural step more complex, climbing the R² gradient.
      3. Keeps an explore_ratio of pure-random formulas (Factor 5 novelty).

    Children carry parent_body + graft description → a traceable lineage tree
    showing how complex formulas grew out of simpler near-winners.

    Round 0 (no attempts / no positive clues) falls back to a baseline pool.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0x5ECA)  # 'REG'
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n)

    # recover R² from the bucketed evidence_kind tags; keep positive clues
    clues = []  # (r2_bucket_int, body)
    for a in attempts:
        r2_bucket = -2
        for k in (a.evidence_kinds or set()):
            if isinstance(k, str) and k.startswith("r2:"):
                try:
                    r2_bucket = int(k.split(":")[1])
                except ValueError:
                    pass
        if r2_bucket > 0:  # any positive R² is an evolutionary clue
            clues.append((r2_bucket, a.body))

    if not clues:
        return generate_pool(round_idx, seed, n)

    # rank clues by R² (desc), take the top distinct bodies as graft roots
    clues.sort(key=lambda t: t[0], reverse=True)
    seen = set()
    roots = []
    for _, body in clues:
        if body not in seen:
            seen.add(body); roots.append(body)
        if len(roots) >= 6:
            break

    pool = []
    n_extrapolate = max(1, int(round(n * (1.0 - explore_ratio))))
    n_explore = n - n_extrapolate

    for i in range(n_extrapolate):
        root_body = rng.choice(roots)
        ast = _reparse(root_body)
        if ast is None:
            ast = _rand_ast(rng, 0, 2)
        new_ast, graft_desc = _graft(ast, rng)
        if _complexity(new_ast) > max_depth * 3:
            new_ast = ast
            graft_desc = "no-op"
        pool.append(make_expr(new_ast, parent_body=root_body,
                              graft=graft_desc, inherited=("root",)))

    for _ in range(n_explore):
        d = rng.choice([1, 2, 2, 3])
        pool.append(make_expr(_rand_ast(rng, 0, d)))

    rng.shuffle(pool)
    return pool


# --- minimal body-string → AST reparser (for lineage grafting) ---
# This handles the canonical strings produced by __str__ in env.py. It is
# intentionally a small recursive-descent parser for our 6 node types.

class _Parser:
    def __init__(self, s: str):
        self.s = s.replace(" ", "")
        self.i = 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def parse(self):
        return self._expr()

    def _expr(self):
        c = self.peek()
        if c == "(":
            return self._paren()
        if c == "x":
            self.i += 1
            return Var()
        if c == "s":  # sin( or square( — disambiguate
            if self.s[self.i:self.i + 3] == "sin":
                self.i += 3
                self._expect("(")
                a = self._expr()
                self._expect(")")
                return Sin(a)
            if self.s[self.i:self.i + 6] == "square":
                # not used (we print ^2), but handle just in case
                self.i += 6
                self._expect("(")
                a = self._expr()
                self._expect(")")
                return Square(a)
        # number or const
        return self._number()

    def _paren(self):
        self._expect("(")
        left = self._expr()
        op = self.peek()
        if op in "+*":
            self.i += 1
            right = self._expr()
            self._expect(")")
            # detect "^2" pattern: (...)^2 is printed by Square
            if self.s[self.i:self.i + 2] == "^2":
                self.i += 2
                return Square(left)
            return Add(left, right) if op == "+" else Mul(left, right)
        # unary inside parens? e.g. (x)^2  → left then ^2
        self._expect(")")
        if self.s[self.i:self.i + 2] == "^2":
            self.i += 2
            return Square(left)
        return left

    def _number(self):
        j = self.i
        while j < len(self.s) and (self.s[j].isdigit() or self.s[j] in ".-"):
            j += 1
        tok = self.s[self.i:j]
        self.i = j
        try:
            return Const(float(tok))
        except ValueError:
            return Const(0.0)

    def _expect(self, ch):
        if self.peek() == ch:
            self.i += 1
        # else: tolerate (best-effort parser)


def _reparse(body: str):
    """Best-effort reparse of a canonical body string into an AST. None on fail."""
    try:
        p = _Parser(body)
        ast = p.parse()
        if p.i < len(body) - 2:  # didn't consume most of it → suspect
            return None
        return ast
    except Exception:
        return None


TARGET_NAMES = ("poly2_offset", "poly2_sin", "linear")


def _selftest():
    print("=== baseline pool ===")
    pool = generate_pool(0, 1, 8)
    for e in pool[:6]:
        print(f"  fam={e.family:7s} cx={_complexity(e.ast)}  {e.body}")
    print("\n=== aware generator (graft onto a winner) ===")
    from core.memory import Memory, Attempt
    from adapters.symreg.env import get_target, r_squared
    mem = Memory()
    winner_ast = Mul(Const(2.0), Square(Var()))  # R²~0.996, no offset
    w = make_expr(winner_ast)
    mem.record(Attempt(body=w.body, universe="poly2_offset", success=True,
                       family="poly", features=[], motif="", evidence_kinds=set()))
    aware = generate_pool_aware(mem, 1, 1, "poly2_offset", 8)
    for e in aware:
        tag = f"← graft from {e.parent_body[:20]}" if e.parent_body else "(random)"
        print(f"  fam={e.family:7s} cx={_complexity(e.ast)} graft={e.graft:10s} {e.body}  {tag}")


if __name__ == "__main__":
    _selftest()
