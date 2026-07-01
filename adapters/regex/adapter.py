"""adapters/regex/adapter.py — the 5 evolving-agents protocols over regex patterns.

Mirrors the symreg adapter structure. A candidate is a RegexExpr; execute()
compiles it and evaluates F1 against a hidden target's example set.

Success grading (graded F1 gate):
  success = F1 >= F1_SUCC (0.85)
  weak    = F1_WEAK <= F1 < F1_SUCC (0.50)
  fail    = F1 < F1_WEAK
"""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.regex.candidate import RegexExpr, family_of
from adapters.regex.env import evaluate, get_target

F1_SUCC = 0.85
F1_WEAK = 0.50

# Domain-defined projection rules (Factor 1/3 audit).
REGEX_RULE_SPECS: list = [
    RuleSpec("overgeneral", "overgeneral", 3, "penalize", -0.35,
             "wildcard-heavy patterns match too broadly (low precision)"),
    RuleSpec("overgeneral", "false_positives", 4, "block", -1.00,
             "consistently accepts negatives — structurally too wide"),
    RuleSpec("toorestrict", "toorestrict", 3, "penalize", -0.30,
             "over-anchored patterns miss valid examples"),
    RuleSpec("literal_only", "false_negatives", 4, "penalize", -0.35,
             "bare literals can't cover a varied example set"),
]


def _pattern_of(candidate) -> str:
    return getattr(candidate, "pattern", None) or getattr(candidate, "body", "")


class RegexAdapter:
    """Implements the 5 evolving-agents protocols over RegexExpr candidates."""

    def classify(self, candidate) -> str:
        if hasattr(candidate, "family"):
            return candidate.family
        return family_of(_pattern_of(candidate))

    def extract(self, candidate) -> list:
        pat = _pattern_of(candidate)
        fam = self.classify(candidate)
        return [f"fam:{fam}", f"len:{min(len(pat), 20)}",
                f"has_anchor:{int('^' in pat or '$' in pat)}",
                f"has_class:{int('[' in pat)}"]

    def motif_of(self, candidate) -> str:
        pat = _pattern_of(candidate)
        fam = self.classify(candidate)
        if fam == "wildcard" or (".*" in pat and "[" not in pat):
            return "overgeneral"
        if pat.count("^") + pat.count("$") >= 2 and "[" not in pat:
            return "toorestrict"
        if fam == "literal" and len(pat) <= 3:
            return "literal_only"
        return ""

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        body = getattr(candidate, "body", str(candidate))
        if body in context.tested_bodies:
            return "already_tested"
        return ""

    def is_success(self, result) -> bool:
        return bool(result.get("success", False)) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak", False)) if isinstance(result, dict) else False


def make_execute(universe: str = "date_iso"):
    """Build the deterministic execute() callback.

    execute(candidate) compiles the regex and evaluates F1 against the hidden
    target named by `universe`. F1 is also bucketed into an evidence_kind tag
    (f1:N) so the memory-aware generator can recover 'how good was each past
    attempt' from the ledger.
    """
    target = get_target(universe)

    def execute(candidate):
        pattern = _pattern_of(candidate)
        if not pattern:
            return {"success": False, "weak": False,
                    "evidence_kinds": {"unparseable"}, "f1": 0.0, "complexity": 0}
        q = evaluate(pattern, target)
        f1 = q["f1"]
        kinds = set(q["evidence_kinds"])
        kinds.add(f"f1:{int(f1 * 10)}")  # bucket for generator
        return {
            "success": f1 >= F1_SUCC,
            "weak": F1_WEAK <= f1 < F1_SUCC,
            "evidence_kinds": kinds,
            "f1": f1,
            "precision": q["precision"],
            "recall": q["recall"],
            "complexity": q["complexity"],
        }

    return execute


def _selftest():
    from adapters.regex.candidate import make_regex
    from adapters.regex.env import get_target
    print(f"targets: {list(__import__('adapters.regex.env', fromlist=['TARGETS']).TARGETS.keys())}")
    for tname in ("date_iso", "email", "phone_cn"):
        t = get_target(tname)
        print(f"\ntarget: {tname} ({t.label})")
        exe = make_execute(tname)
        tests = {"wide": ".*"}
        if tname == "date_iso":
            tests["3groups"] = "[0-9]+-[0-9]+-[0-9]+"
            tests["perfect"] = "[0-9]{4}-[0-9]{2}-[0-9]{2}"
        elif tname == "email":
            tests["at_domain"] = ".*@.*\\..*"
            tests["perfect"] = "[a-z.]+@[a-z]+\\.[a-z]+"
        elif tname == "phone_cn":
            tests["11digits"] = "[0-9]{11}"
            tests["perfect"] = "1[0-9]{10}"
        for label, pat in tests.items():
            out = exe(make_regex(pat))
            print(f"  {label:10s} {pat:28s} F1={out['f1']:.2f} "
                  f"succ={out['success']} weak={out['weak']}")


if __name__ == "__main__":
    _selftest()
