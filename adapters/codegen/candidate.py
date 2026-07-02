"""adapters/codegen/candidate.py — code variant candidates + generators.

A candidate is a CodeExpr wrapping a function body string. Family = the
dominant operation pattern. Evolution = grafting fixes onto near-miss code.

Graft operations (fix common bugs in generated code):
  fix_op     — x*2 → x**2 (wrong operator)
  fix_loop   — add proper iteration structure
  fix_init   — add initialization (total=0)
  fix_return — fix return statement
  use_hint   — incorporate a correct template fragment
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from adapters.codegen.env import get_task


@dataclass(frozen=True)
class CodeExpr:
    """One candidate: a function body string + lineage."""
    body_code: str
    body: str
    parent_body: str = ""
    graft: str = ""
    inherited: tuple = ()

    @property
    def family(self) -> str:
        return family_of(self.body_code)

    def to_json(self) -> dict:
        return {"body": self.body, "family": self.family, "code": self.body_code,
                "parent_body": self.parent_body, "graft": self.graft}


def make_code(body_code: str, parent_body: str = "", graft: str = "",
              inherited: tuple = ()) -> CodeExpr:
    return CodeExpr(body_code=body_code, body=body_code, parent_body=parent_body,
                    graft=graft, inherited=inherited)


def family_of(code: str) -> str:
    """Family = dominant pattern: comprehension / loop / builtin / expression."""
    c = code.lower()
    if "for" in c and "return" not in c.split("\n")[-1]:
        return "loop"
    if "sum(" in c or "max(" in c or "min(" in c or "len(" in c:
        return "comprehension"
    if "for " in c:
        return "comprehension"
    return "expression"


# Common buggy patterns for random generation
_BUGGY_TEMPLATES = {
    "sum_squares": [
        "return lst + 1",
        "return sum(x*2 for x in lst)",
        "return sum(x for x in lst)",
        "return x**2",
        "total = 0\nfor x in lst:\n    total = x\nreturn total",
    ],
    "count_vowels": [
        "return len(s)",
        "return sum(1 for c in s)",
        "return s.count('a')",
        "count = 0\nreturn count",
    ],
    "max_diff": [
        "return max(lst)",
        "return abs(lst[0] - lst[1])",
        "return 0",
        "return sum(lst)",
    ],
}


def _rand_code(rng: random.Random, task_name: str) -> str:
    """Generate a random (usually buggy) code body."""
    task = get_task(task_name)
    r = rng.random()
    if r < 0.3:
        # use a correct hint (sometimes)
        return rng.choice(task.hints)
    elif r < 0.8:
        # use a buggy template
        templates = _BUGGY_TEMPLATES.get(task_name, ["return None"])
        return rng.choice(templates)
    else:
        # pure random expression
        return f"return {rng.choice(['0', '1', 'lst', 's', 'None', 'len(lst)'])}"


def generate_pool(round_idx: int, seed: int, n: int = 10, task_name: str = "sum_squares") -> list:
    """Memory-INdependent pool of random code variants. Mostly buggy."""
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool = []
    for _ in range(n):
        pool.append(make_code(_rand_code(rng, task_name)))
    rng.shuffle(pool)
    return pool


def _graft(parent: str, rng: random.Random, task_name: str = "") -> tuple:
    """Apply ONE fix graft to a near-miss code body.

    Strategy: identify the likely bug and apply the matching fix.
    Returns (new_code, graft_description).
    """
    task = get_task(task_name) if task_name else get_task("sum_squares")
    c = parent.lower()

    # fix wrong operator: x*2 → x**2 (for square tasks)
    if "x*2" in c or "(x*2)" in c:
        new = parent.replace("x*2", "x**2").replace("x * 2", "x ** 2")
        if new != parent:
            return new, "x*2→x**2"

    # fix: using sum without square → add square
    if "sum(x for x in" in c and "sum_squares" in task_name:
        new = parent.replace("sum(x for x in", "sum(x**2 for x in")
        if new != parent:
            return new, "+**2"

    # fix: counting all chars instead of vowels
    if "sum(1 for c in s)" in c and "count_vowels" in task_name:
        new = parent.replace("sum(1 for c in s)", "sum(1 for c in s if c.lower() in 'aeiou')")
        return new, "+vowel_filter"

    # fix: s.count('a') → count all vowels
    if "s.count('a')" in c and "count_vowels" in task_name:
        new = parent.replace("s.count('a')", "sum(s.lower().count(v) for v in 'aeiou')")
        return new, "'a'→all_vowels"

    # fix: loop without accumulation
    if "total = x" in c:
        new = parent.replace("total = x", "total += x*x")
        return new, "=→+= (fix accumulation)"

    # fix: return 0 / return None → use a hint
    if parent.strip() in ("return 0", "return none", "return none", "return 1"):
        hint = rng.choice(task.hints)
        return hint, "stub→hint"

    # fix: only uses lst[0] or lst[1] → generalize to loop
    if "lst[0]" in c and "for" not in c:
        hint = rng.choice(task.hints)
        return hint, "index→loop"

    # last resort: try a correct hint as a structural replacement
    if rng.random() < 0.5:
        hint = rng.choice(task.hints)
        return hint, "→hint"

    return parent, "no-op"


def generate_pool_aware(memory, round_idx: int, seed: int, universe: str,
                        n: int = 10, explore_ratio: float = 0.3) -> list:
    """Memory-AWARE evolution: graft fixes onto highest-score code."""
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0xC0DE)
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n, universe)

    clues = []
    for a in attempts:
        score = -1
        for k in (a.evidence_kinds or set()):
            if isinstance(k, str) and k.startswith("score:"):
                try:
                    score = int(k.split(":")[1])
                except ValueError:
                    pass
        if score >= 0:
            clues.append((score, a.body))

    if not clues:
        return generate_pool(round_idx, seed, n, universe)

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
    weights = [1.0 / (i + 1) for i in range(len(roots))]

    for _ in range(n_extrapolate):
        root = rng.choices(roots, weights=weights, k=1)[0]
        new_code, graft_desc = _graft(root, rng, universe)
        pool.append(make_code(new_code, parent_body=root,
                              graft=graft_desc, inherited=("root",)))

    for _ in range(n_explore):
        pool.append(make_code(_rand_code(rng, universe)))

    rng.shuffle(pool)
    return pool
