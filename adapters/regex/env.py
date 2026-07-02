"""adapters/regex/env.py — regex synthesis targets + F1 evaluator (stdlib only).

A candidate is a regex pattern (a string that compiles via `re`). "Execute" =
classify a held-out set of positive/negative example strings: does the regex
match all positives and reject all negatives?

This domain mirrors symbolic regression's strengths:
  - Graded F1 gate (0→1 continuous) — not binary like 2048, not ceilinged
    like maze. `.*` matches everything (high recall, low precision → middling
    F1); the right pattern balances both → F1 climbs toward 1.0.
  - Deterministic: same regex + same examples → same F1 (re module is fixed).
  - Discrete AST: regex structure is combinatorial (char-class, repetition,
    anchor, concat), so "grafting" adds a visible structural node, not a
    weight nudge.
  - Rare success: a random regex almost never classifies a realistic example
    set correctly.

Targets are PROGRAM-SYNTHESIS tasks — induce a rule from labeled string
examples (dates, emails, phone numbers). More persuasive than guessing a toy
pattern, and closer to a real use case.
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    """A hidden rule = (positive examples, negative examples, human label)."""
    name: str
    pos: tuple        # strings that SHOULD match
    neg: tuple        # strings that should NOT match
    label: str        # human-readable description of the hidden rule


# Hidden targets — the rule the agent must rediscover from examples.
TARGETS = {
    "date_iso": Target(
        "date_iso",
        ("2024-01-15", "2023-12-31", "2020-06-01", "1999-01-01", "2025-11-20",
         "2000-07-08", "1985-03-22"),
        ("24-01-15", "2024/01/15", "2024-1-5", "2024-13-45", "abc", "2024-01",
         "20240115", "25-12-31", "2024", "01-15-2024"),
        "YYYY-MM-DD date",
    ),
    "email": Target(
        "email",
        ("a@b.com", "user@mail.org", "test@domain.cn", "x.y@z.io", "admin@site.co"),
        ("abc", "@b.com", "a@", "a@b", "a b@c.com", "a@b.c", "plain text", "@@", "a@.com"),
        "email address",
    ),
    "phone_cn": Target(
        "phone_cn",
        ("13800138000", "15912345678", "18600001111", "15098765432", "13311223344"),
        ("1234567890", "1380013800", "138001380001", "abc", "1234", "23800138000",
         "138-0013-8000", " 13800138000 "),
        "Chinese mobile phone (11 digits, starts with 1)",
    ),
}


def get_target(name: str) -> Target:
    return TARGETS[name]


def target_label(name: str) -> str:
    return TARGETS[name].label


def evaluate(pattern: str, target: Target) -> dict:
    """F1 of `pattern` against the target's example set.

    F1 = harmonic mean of precision (of matches, how many are true positives)
    and recall (of true positives, how many are matched). This is stricter
    than accuracy: `.*` has perfect recall but terrible precision → middling
    F1, which is what creates the gradient for evolution to climb.

    Returns F1, precision, recall, complexity, and failure evidence tags.
    """
    try:
        compiled = re.compile(pattern)
    except re.error:
        return {"f1": 0.0, "precision": 0.0, "recall": 0.0,
                "complexity": len(pattern), "evidence_kinds": {"unparseable"}}

    tp = sum(1 for s in target.pos if compiled.fullmatch(s))
    fp = sum(1 for s in target.neg if compiled.fullmatch(s))
    fn = sum(1 for s in target.pos if not compiled.fullmatch(s))

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)
          if (precision + recall) > 0 else 0.0)

    kinds = set()
    if fp > 0:
        kinds.add("false_positives")  # too wide
    if fn > 0:
        kinds.add("false_negatives")  # too narrow
    if precision < 0.4 and recall >= 0.8:
        kinds.add("overgeneral")      # matches too much
    if recall < 0.4 and precision >= 0.8:
        kinds.add("toorestrict")      # matches too little
    if 0.5 <= f1 < 0.85:
        kinds.add("partial_fit")

    return {
        "f1": round(f1, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "complexity": len(pattern),
        "evidence_kinds": kinds,
    }


def _selftest():
    print("=== regex env selftest ===")
    for tname in ("date_iso", "email", "phone_cn"):
        t = get_target(tname)
        print(f"\ntarget: {tname} ({t.label}) — {len(t.pos)} pos, {len(t.neg)} neg")
        tests = {
            ".*": "too wide",
            "[0-9]*": "digits only",
        }
        if tname == "date_iso":
            tests["[0-9]+-[0-9]+-[0-9]+"] = "3 numeric groups"
            tests["[0-9]{4}-[0-9]{2}-[0-9]{2}"] = "YYYY-MM-DD (perfect)"
        elif tname == "email":
            tests[".*@.*"] = "has @"
            tests[".*@.*\\..*"] = "@ + domain"
            tests["[a-z.]+@[a-z]+\\.[a-z]+"] = "full email (perfect)"
        elif tname == "phone_cn":
            tests["1[0-9]{10}"] = "1 + 10 digits (perfect)"
            tests["[0-9]{11}"] = "11 digits (close but allows wrong start)"
        for pat, desc in tests.items():
            q = evaluate(pat, t)
            print(f"  {pat:28s} F1={q['f1']:.2f} P={q['precision']:.2f} "
                  f"R={q['recall']:.2f} kinds={sorted(q['evidence_kinds'])}  {desc}")


if __name__ == "__main__":
    _selftest()
