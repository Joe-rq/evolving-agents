"""adapters/sql/adapter.py — 5 evolving-agents protocols over SQL queries.

Mirrors the regex adapter. A candidate is a Query; execute() evaluates its
cost via the anti-pattern cost model. Success = low cost (high score).
"""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.sql.candidate import Query, family_of, detect_anti_patterns
from adapters.sql.env import evaluate, get_task

SCORE_SUCC = 0.80   # score >= 0.80 = success (cost <= ~5)
SCORE_WEAK = 0.40   # 0.40 <= score < 0.80 = weak

SQL_RULE_SPECS: list = [
    RuleSpec("cartesian_join", "cartesian_join", 2, "block", -1.00,
             "JOIN without ON produces a cross product — always avoid"),
    RuleSpec("select_star", "select_star", 3, "penalize", -0.40,
             "SELECT * wastes I/O — specify columns"),
    RuleSpec("leading_wildcard", "leading_wildcard", 2, "penalize", -0.50,
             "LIKE '%...' can't use index — use prefix match"),
    RuleSpec("join_no_filter", "join_no_filter", 2, "penalize", -0.35,
             "JOIN without WHERE/ON scans too many rows"),
]


def _sql_of(candidate) -> str:
    return getattr(candidate, "sql", None) or getattr(candidate, "body", "")


class SQLAdapter:
    def classify(self, candidate) -> str:
        if hasattr(candidate, "family"):
            return candidate.family
        return family_of(_sql_of(candidate))

    def extract(self, candidate) -> list:
        sql = _sql_of(candidate)
        fam = self.classify(candidate)
        has_join = int("JOIN" in sql.upper())
        has_where = int("WHERE" in sql.upper())
        has_limit = int("LIMIT" in sql.upper())
        return [f"fam:{fam}", f"join:{has_join}", f"where:{has_where}", f"limit:{has_limit}"]

    def motif_of(self, candidate) -> str:
        issues = detect_anti_patterns(_sql_of(candidate))
        if "cartesian_join" in issues:
            return "cartesian_join"
        if "leading_wildcard" in issues:
            return "leading_wildcard"
        if "select_star" in issues:
            return "select_star"
        if "join_no_filter" in issues:
            return "join_no_filter"
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


def make_execute(universe: str = "join_filter"):
    """Build the deterministic execute() callback."""
    task = get_task(universe)

    def execute(candidate):
        sql = _sql_of(candidate)
        if not sql:
            return {"success": False, "weak": False, "evidence_kinds": {"empty"}, "cost": 99, "score": 0}
        r = evaluate(sql, task)
        score = r["score"]
        kinds = set(r["evidence_kinds"])
        kinds.add(f"score:{int(score * 10)}")
        return {
            "success": score >= SCORE_SUCC,
            "weak": SCORE_WEAK <= score < SCORE_SUCC,
            "evidence_kinds": kinds,
            "cost": r["cost"],
            "score": score,
        }

    return execute
