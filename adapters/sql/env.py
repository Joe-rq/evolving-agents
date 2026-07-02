"""adapters/sql/env.py — SQL query cost evaluator (stdlib only).

No real database — a deterministic cost model that penalizes known SQL
anti-patterns. This is the same design as symreg/regex: a self-contained
mini-environment that makes evolution observable without external deps.

Cost model (lower = better):
  base 1.0 + penalties for each anti-pattern detected:
    select_star      +5   SELECT * wastes I/O
    leading_wildcard +8   LIKE '%...' can't use index
    not_in           +4   NOT IN is slow on large sets
    cartesian_join   +10  JOIN without ON = cross product
    join_no_filter   +6   JOIN but no WHERE to limit rows
    no_limit         +2   large result set without LIMIT
    or_in_where      +3   OR in WHERE prevents index usage

The "target" is an optimal query for a given task spec. We measure cost
as a continuous metric (like R²/F1 in other domains) — evolution climbs
from high-cost (bad query) toward low-cost (optimized query).
"""
from __future__ import annotations

from dataclasses import dataclass

# Anti-pattern penalties
PENALTIES = {
    "select_star": 5,
    "leading_wildcard": 8,
    "not_in": 4,
    "cartesian_join": 10,
    "join_no_filter": 6,
    "no_limit": 2,
    "or_in_where": 3,
}


@dataclass(frozen=True)
class QueryTask:
    """A query optimization task: a schema + the ideal query shape.
    The agent doesn't see the ideal — it discovers low-cost queries by trial."""
    name: str
    description: str
    # the ideal query (for reference; agent never sees this)
    ideal: str
    # table names mentioned (for pool generation context)
    tables: tuple


TASKS = {
    "join_filter": QueryTask(
        "join_filter",
        "Join two tables with a filter",
        "SELECT id FROM orders JOIN customers ON orders.cid = customers.id WHERE status = 'active'",
        ("orders", "customers"),
    ),
    "simple_lookup": QueryTask(
        "simple_lookup",
        "Look up a single row by id",
        "SELECT name FROM users WHERE id = 42 LIMIT 1",
        ("users",),
    ),
    "range_search": QueryTask(
        "range_search",
        "Search within a range with prefix match",
        "SELECT id FROM products WHERE name LIKE 'laptop%' AND price < 1000",
        ("products",),
    ),
}


def get_task(name: str) -> QueryTask:
    return TASKS[name]


def detect_anti_patterns(query: str) -> set:
    """Detect SQL anti-patterns in a query string. Returns a set of tags."""
    q = query.upper().replace("\n", " ")
    issues = set()

    if "SELECT *" in q:
        issues.add("select_star")
    if "LIKE '%" in q or "LIKE \"%" in q:
        issues.add("leading_wildcard")
    if "NOT IN" in q:
        issues.add("not_in")
    if "JOIN" in q and " ON " not in q:
        issues.add("cartesian_join")
    if "JOIN" in q and "WHERE" not in q and " ON " not in q:
        issues.add("join_no_filter")
    if "LIMIT" not in q:
        issues.add("no_limit")
    if " OR " in q and "WHERE" in q:
        issues.add("or_in_where")

    return issues


def evaluate(query: str, task: QueryTask) -> dict:
    """Evaluate a query's cost against a task. Lower cost = better.

    Returns cost (continuous metric), the anti-patterns found, and a
    normalized score in [0, 1] where 1.0 = optimal (cost <= 1.0).
    """
    issues = detect_anti_patterns(query)
    penalty = sum(PENALTIES.get(i, 0) for i in issues)
    cost = 1.0 + penalty

    # normalize: cost 1.0 = perfect, cost >= 20 = terrible
    # score = max(0, 1 - (cost - 1) / 19)
    score = max(0.0, 1.0 - (cost - 1.0) / 19.0)

    # also check: does the query reference the right tables?
    q_lower = query.lower()
    tables_mentioned = sum(1 for t in task.tables if t.lower() in q_lower)
    if tables_mentioned == 0:
        issues.add("wrong_tables")
        score = 0.0

    # syntax sanity: must start with SELECT
    stripped = query.strip().upper()
    if not stripped.startswith("SELECT"):
        issues.add("syntax_error")
        score = 0.0

    return {
        "cost": round(cost, 2),
        "score": round(score, 4),
        "evidence_kinds": issues,
    }


def _selftest():
    print("=== SQL cost evaluator selftest ===")
    for tname in ("join_filter", "simple_lookup", "range_search"):
        t = get_task(tname)
        print(f"\ntask: {tname} ({t.description})")
        tests = {
            "bad_star": f"SELECT * FROM {t.tables[0]}",
            "bad_cartesian": f"SELECT id FROM {t.tables[0]} JOIN {t.tables[1]}" if len(t.tables) > 1 else None,
            "good_no_limit": f"SELECT id FROM {t.tables[0]} WHERE id = 1",
            "optimal": t.ideal,
        }
        for label, q in tests.items():
            if q is None:
                continue
            r = evaluate(q, t)
            print(f"  {label:16s} cost={r['cost']:5.1f} score={r['score']:.2f} issues={sorted(r['evidence_kinds'])}")
            print(f"  {'':16s} {q[:60]}")


if __name__ == "__main__":
    _selftest()
