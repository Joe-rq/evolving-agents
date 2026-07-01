"""adapters/regex/candidate.py — regex pattern candidates + generators.

A candidate is a RegexExpr wrapping a pattern string. Family = the dominant
structural class — the Factor-2 axis. Two generators, same split as symreg:
  generate_pool(round_idx, seed, n)           — memory-INdependent baseline.
  generate_pool_aware(memory, ..., target)    — memory-AWARE evolution.

The aware generator reads F1 buckets from evidence_kinds and grafts a
CONSTRAINT onto high-F1 patterns — the regex evolution space is "from too-wide
to just-right", so grafting = tightening (add anchor, narrow char-class, add
repetition count). Each child is visibly more specific than its parent.
"""
from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexExpr:
    """One candidate: a regex pattern string + lineage."""
    pattern: str
    body: str               # == pattern (canonical)
    parent_body: str = ""
    graft: str = ""
    inherited: tuple = ()

    @property
    def family(self) -> str:
        return family_of(self.pattern)

    def to_json(self) -> dict:
        return {
            "body": self.body, "pattern": self.pattern,
            "family": self.family, "parent_body": self.parent_body,
            "graft": self.graft, "inherited": list(self.inherited),
        }


def make_regex(pattern: str, parent_body: str = "", graft: str = "",
               inherited: tuple = ()) -> RegexExpr:
    return RegexExpr(pattern=pattern, body=pattern, parent_body=parent_body,
                     graft=graft, inherited=inherited)


# --- family classification (Factor 2) ---

def family_of(pattern: str) -> str:
    """Dominant structural family: anchored / class / repeat / wildcard / literal."""
    if "^" in pattern or "$" in pattern:
        return "anchored"
    if "{" in pattern or "+" in pattern or "*" in pattern or "?" in pattern:
        if "[" in pattern:
            return "class"
        if "." in pattern:
            return "wildcard"
        return "repeat"
    if "[" in pattern:
        return "class"
    if "." in pattern:
        return "wildcard"
    return "literal"


# --- random pattern generation ---

CHAR_CLASSES = ["[0-9]", "[a-z]", "[A-Z]", "[a-zA-Z]", "[0-9a-z]", "\\w", "\\d", "."]
LITERALS = ["a", "b", "c", "0", "1", "2", "-", "@", "."]
REPEATS = ["*", "+", "?", "{2}", "{3}", "{4}"]


def _rand_atom(rng: random.Random) -> str:
    """A single regex atom: char-class, literal, or escaped."""
    r = rng.random()
    if r < 0.5:
        return rng.choice(CHAR_CLASSES)
    if r < 0.85:
        return rng.choice(LITERALS)
    return rng.choice(["\\d", "\\w", "\\s"])


def _rand_pattern(rng: random.Random, depth: int) -> str:
    """Grow a random regex of `depth` atoms, each optionally repeated."""
    parts = []
    for _ in range(max(1, depth)):
        atom = _rand_atom(rng)
        if rng.random() < 0.4:
            atom += rng.choice(REPEATS)
        parts.append(atom)
    pat = "".join(parts)
    if rng.random() < 0.25:
        pat = "^" + pat
    if rng.random() < 0.25:
        pat = pat + "$"
    return pat


# --- baseline generator ---

def generate_pool(round_idx: int, seed: int, n: int = 10) -> list:
    """Deterministic, memory-INdependent pool of random regex patterns."""
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool = []
    # seed family diversity
    archetypes = [
        ".*",                    # wildcard
        "[0-9]*",                # class
        "[a-z]+",                # class repeat
        "a",                     # literal
    ]
    for a in archetypes:
        pool.append(make_regex(a))
    for _ in range(max(0, n - len(archetypes))):
        d = rng.choice([1, 2, 2, 3, 3])
        pool.append(make_regex(_rand_pattern(rng, d)))
    rng.shuffle(pool)
    return pool


# --- memory-AWARE generator (evolution: graft constraints onto winners) ---

def _safe_positions(parent: str) -> list:
    """Indices in `parent` that are OUTSIDE char-classes and NOT right before/
    after a quantifier — safe spots to insert or modify structure.

    A blind insert into `[0-9]` corrupts the char-class. This parser tracks
    bracket depth and skips quantifier positions, so grafts land cleanly.
    """
    safe = []
    depth = 0
    quantifiers = set("*+?{}")
    for i, ch in enumerate(parent):
        if ch == "[":
            depth += 1
            continue
        if ch == "]":
            depth = max(0, depth - 1)
            continue
        if depth > 0:
            continue  # inside a char-class → unsafe
        # skip if this char is a quantifier or right after one
        if ch in quantifiers:
            continue
        if i > 0 and parent[i - 1] in quantifiers:
            continue
        if ch in "^$\\":
            continue
        safe.append(i)
    return safe


def _graft(parent: str, rng: random.Random, target_hint: str = "") -> tuple:
    """Apply ONE constraint-tightening graft to a winning pattern.

    Structure-aware: uses _safe_positions to avoid corrupting char-classes or
    double-quantifying. Regex evolution = "from too-wide to just-right":
      anchor      — add ^ or $ to pin position
      narrow      — replace a wide atom (.* → [0-9]*) with a narrower one
      add_repeat  — attach {n} to an unquantified safe atom
      add_literal — insert a literal char (from target's likely alphabet)
      struct_seq  — replace .* with a 2-3 atom SEQUENCE (e.g. [0-9]+-[0-9]+)
                    — this is the key structural growth: a wildcard blob becomes
                    a structured sequence, the unit of regex evolution.

    Returns (new_pattern, graft_description).
    """
    kind = rng.choices(
        ["anchor", "narrow", "add_repeat", "add_literal", "struct_seq"],
        weights=[3, 3, 2, 2, 4],  # struct_seq weighted high — it's the real growth
    )[0]

    if kind == "anchor":
        if not parent.startswith("^") and rng.random() < 0.5:
            return "^" + parent, "+^"
        if not parent.endswith("$"):
            return parent + "$", "+$"
        return parent, "no-op"

    if kind == "narrow":
        replacements = [".*", ".+", "[a-zA-Z]", "[0-9a-z]", "\\w+"]
        narrow_map = {".*": "[0-9]*", ".+": "[0-9]+", "[a-zA-Z]": "[a-z]",
                      "[0-9a-z]": "[0-9]", "\\w+": "[0-9]+"}
        for wide in replacements:
            if wide in parent:
                narrow = narrow_map.get(wide, "[0-9]")
                return parent.replace(wide, narrow, 1), f"{wide}→{narrow}"

    if kind == "add_repeat":
        safe = _safe_positions(parent)
        for i in safe:
            if i + 1 < len(parent) and parent[i + 1] not in "*+?{":
                n = rng.choice(["{2}", "{3}", "{4}", "+"])
                return parent[:i + 1] + n + parent[i + 1:], f"+{n}@{i}"

    if kind == "add_literal":
        # pick a literal likely relevant to the target domain
        lit_pool = {
            "date_iso": ["-", "0", "1", "2", "9"],
            "email": ["@", ".", "a", "c", "o"],
            "phone_cn": ["1", "3", "5", "8", "0"],
        }.get(target_hint, ["-", "0", "a", "1"])
        lit = rng.choice(lit_pool)
        safe = _safe_positions(parent)
        if not safe:
            safe = [len(parent)]
        pos = rng.choice(safe + [0, len(parent)])
        return parent[:pos] + lit + parent[pos:], f"+{lit}"

    if kind == "struct_seq":
        # THE structural growth: replace a wildcard blob with a structured
        # sequence of char-classes + literals. E.g. .* → [0-9]+-[0-9]+
        sequences = {
            "date_iso": ["[0-9]+-[0-9]+", "[0-9]{2}-[0-9]{2}", "[0-9]+-[0-9]+-[0-9]+"],
            "email": ["[a-z]+@", "[a-z]+@[a-z]+", "@[a-z]+\\.[a-z]+"],
            "phone_cn": ["1[0-9]+", "[0-9]{4}[0-9]+", "1[0-9]{4}"],
        }
        seqs = sequences.get(target_hint, ["[0-9]+", "[a-z]+", "[0-9]+-[0-9]+"])
        seq = rng.choice(seqs)
        # try replacing a wide blob first — but strip anchors from parent first
        # to avoid producing broken patterns like [0-9]+^@+
        stripped = parent
        had_start_anchor = stripped.startswith("^")
        had_end_anchor = stripped.endswith("$")
        if had_start_anchor:
            stripped = stripped[1:]
        if had_end_anchor:
            stripped = stripped[:-1]
        for wide in [".*", ".+", "[0-9]*", "[0-9]+"]:
            if wide in stripped:
                result = stripped.replace(wide, seq, 1)
                if had_start_anchor:
                    result = "^" + result
                if had_end_anchor:
                    result = result + "$"
                return result, f"{wide}→{seq}"
        # no blob to replace → use the sequence as the whole pattern (drop junk)
        return seq, f"replace→{seq}"

    return parent, "no-op"


def generate_pool_aware(
    memory,
    round_idx: int,
    seed: int,
    universe: str,
    n: int = 10,
    explore_ratio: float = 0.3,
) -> list:
    """Memory-AWARE evolution generator: graft constraints onto high-F1 patterns.

    Reads memory.attempts, recovers each pattern's F1 from the bucketed `f1:N`
    evidence_kind, ranks by F1 (desc), and grafts a tightening constraint onto
    the best patterns. Round 0 (no positive clues) falls back to baseline.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0x2E65)  # 'RE'
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n)

    # recover F1 bucket from evidence_kinds
    clues = []
    for a in attempts:
        f1_bucket = -1
        for k in (a.evidence_kinds or set()):
            if isinstance(k, str) and k.startswith("f1:"):
                try:
                    f1_bucket = int(k.split(":")[1])
                except ValueError:
                    pass
        if f1_bucket >= 0:  # any F1 >= 0 is a clue (even low F1 has recall signal)
            clues.append((f1_bucket, a.body))

    if not clues:
        return generate_pool(round_idx, seed, n)

    clues.sort(key=lambda t: t[0], reverse=True)  # highest F1 first
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

    # weight toward highest-F1 roots — the best past pattern is the most
    # valuable grafting substrate, but not so steeply that one bad graft
    # on the top root collapses the whole round.
    weights = [1.0 / (i + 1) for i in range(len(roots))]

    for _ in range(n_extrapolate):
        root = rng.choices(roots, weights=weights, k=1)[0]
        new_pat, graft_desc = _graft(root, rng, target_hint=universe)
        if len(new_pat) > 60:  # cap complexity
            new_pat = root
            graft_desc = "no-op"
        pool.append(make_regex(new_pat, parent_body=root,
                               graft=graft_desc, inherited=("root",)))

    for _ in range(n_explore):
        d = rng.choice([1, 2, 2, 3])
        pool.append(make_regex(_rand_pattern(rng, d)))

    rng.shuffle(pool)
    return pool


def _selftest():
    print("=== baseline pool ===")
    pool = generate_pool(0, 1, 8)
    for r in pool[:6]:
        print(f"  fam={r.family:9s}  {r.body}")
    print("\n=== aware generator (graft onto a winner) ===")
    from core.memory import Memory, Attempt
    mem = Memory()
    mem.record(Attempt(body=".*", universe="date_iso", success=True,
                       family="wildcard", features=[], motif="", evidence_kinds={"f1:5"}))
    mem.record(Attempt(body="[0-9]*", universe="date_iso", success=False, weak=True,
                       family="class", features=[], motif="", evidence_kinds={"f1:0"}))
    aware = generate_pool_aware(mem, 1, 1, "date_iso", 8)
    for r in aware:
        tag = f"  [graft {r.graft} ← {r.parent_body}]" if r.parent_body else "  [random]"
        print(f"  fam={r.family:9s} {r.body:28s}{tag}")


if __name__ == "__main__":
    _selftest()
