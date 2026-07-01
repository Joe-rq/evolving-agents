"""adapters/codegen/adapter.py — 5 protocols over code variants."""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.codegen.candidate import CodeExpr, family_of
from adapters.codegen.env import evaluate, get_task

SCORE_SUCC = 0.99   # must pass ALL tests
SCORE_WEAK = 0.40

CODEGEN_RULE_SPECS: list = [
    RuleSpec("type_error", "typeerror", 2, "penalize", -0.40,
             "type errors indicate wrong operand usage"),
    RuleSpec("stub", "wrong_answer", 3, "penalize", -0.30,
             "returning a constant rarely solves a real problem"),
    RuleSpec("index_only", "wrong_answer", 3, "penalize", -0.25,
             "hardcoded indices don't generalize"),
]


def _code_of(candidate) -> str:
    return getattr(candidate, "body_code", None) or getattr(candidate, "body", "")


class CodegenAdapter:
    def classify(self, candidate) -> str:
        if hasattr(candidate, "family"):
            return candidate.family
        return family_of(_code_of(candidate))

    def extract(self, candidate) -> str:
        code = _code_of(candidate)
        fam = self.classify(candidate)
        has_loop = int("for " in code)
        has_sum = int("sum(" in code)
        has_return = int("return" in code)
        return [f"fam:{fam}", f"loop:{has_loop}", f"sum:{has_sum}", f"return:{has_return}"]

    def motif_of(self, candidate) -> str:
        code = _code_of(candidate).lower().strip()
        if code in ("return 0", "return 1", "return none", "return len(lst)"):
            return "stub"
        if "lst[0]" in code and "for " not in code:
            return "index_only"
        if "+" not in code and "*" not in code and "return lst" in code:
            return "type_error"
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


def make_execute(universe: str = "sum_squares"):
    task = get_task(universe)

    def execute(candidate):
        code = _code_of(candidate)
        if not code:
            return {"success": False, "weak": False, "evidence_kinds": {"empty"}, "score": 0}
        r = evaluate(code, task)
        score = r["score"]
        kinds = set(r["evidence_kinds"])
        kinds.add(f"score:{int(score * 10)}")
        return {
            "success": score >= SCORE_SUCC,
            "weak": SCORE_WEAK <= score < SCORE_SUCC,
            "evidence_kinds": kinds,
            "score": score,
            "passed": r.get("passed", 0),
            "total": r.get("total", 0),
        }

    return execute
