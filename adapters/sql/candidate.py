"""adapters/sql/candidate.py — SQL query candidates + generators.

A candidate is a SQL query string. Family = the dominant anti-pattern class
(or "clean" if no anti-patterns). The evolution direction is the same as
regex: TIGHTEN — from costly queries toward optimized ones.

Grafts remove anti-patterns or add missing optimization:
  add_on       — add ON clause to a cartesian join
  star_to_cols — replace SELECT * with SELECT id
  fix_wildcard — remove leading % from LIKE
  add_where    — add a WHERE filter to an unfiltered JOIN
  add_limit    — add LIMIT 1
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from adapters.sql.env import get_task, detect_anti_patterns


@dataclass(frozen=True)
class Query:
    """One candidate: a SQL query string + lineage."""
    sql: str
    body: str
    parent_body: str = ""
    graft: str = ""
    inherited: tuple = ()

    @property
    def family(self) -> str:
        return family_of(self.sql)

    def to_json(self) -> dict:
        return {"body": self.body, "sql": self.sql, "family": self.family,
                "parent_body": self.parent_body, "graft": self.graft}


def make_query(sql: str, parent_body: str = "", graft: str = "",
               inherited: tuple = ()) -> Query:
    return Query(sql=sql, body=sql, parent_body=parent_body,
                 graft=graft, inherited=inherited)


def family_of(sql: str) -> str:
    """Family = dominant anti-pattern, or 'clean' if none."""
    issues = detect_anti_patterns(sql)
    if not issues:
        return "clean"
    # pick the most severe
    severity = {"cartesian_join": 0, "leading_wildcard": 1, "select_star": 2,
                "join_no_filter": 3, "not_in": 4, "or_in_where": 5, "no_limit": 6}
    ranked = sorted(issues, key=lambda i: severity.get(i, 99))
    return ranked[0]


def _rand_query(rng: random.Random, task_name: str) -> str:
    """Generate a random (usually bad) query for the task's tables."""
    task = get_task(task_name)
    t = task.tables[0]
    parts = ["SELECT"]

    # SELECT clause: sometimes * (bad), sometimes specific cols
    if rng.random() < 0.5:
        parts.append("*")
    else:
        parts.append(rng.choice(["id", "name", "id, name"]))

    parts.append("FROM")
    parts.append(t)

    # sometimes add a JOIN (sometimes without ON = bad)
    if len(task.tables) > 1 and rng.random() < 0.5:
        parts.append("JOIN")
        parts.append(task.tables[1])
        if rng.random() < 0.4:
            parts.append(f"ON {t}.id = {task.tables[1]}.id")

    # sometimes add WHERE
    if rng.random() < 0.4:
        if rng.random() < 0.3:
            parts.append(f"WHERE name LIKE '%{rng.choice(['a','b','test'])}%'")
        else:
            parts.append(f"WHERE {rng.choice(['id','status','name'])} = '{rng.choice(['1','active','x'])}'")

    # sometimes add LIMIT
    if rng.random() < 0.3:
        parts.append("LIMIT 1")

    return " ".join(parts)


def generate_pool(round_idx: int, seed: int, n: int = 10, task_name: str = "join_filter") -> list:
    """Memory-INdependent pool of random queries. Mostly bad — high cost."""
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool = []
    for _ in range(n):
        pool.append(make_query(_rand_query(rng, task_name)))
    rng.shuffle(pool)
    return pool


def _graft(parent: str, rng: random.Random) -> tuple:
    """Apply ONE optimization graft to a costly query.

    Picks the most severe anti-pattern in the parent and fixes it.
    Returns (new_query, graft_description).
    """
    issues = detect_anti_patterns(parent)
    if not issues:
        # already clean — try minor optimization
        if "LIMIT" not in parent.upper():
            return parent + " LIMIT 1", "+LIMIT"
        return parent, "no-op"

    q = parent
    # fix the most impactful issue first
    if "cartesian_join" in issues:
        # add ON clause — parse table names from ORIGINAL case (not uppercased)
        if " JOIN " in q.upper():
            # find the table after FROM (original case)
            after_from = q.upper().split("FROM", 1)[1].strip() if "FROM" in q.upper() else ""
            t1 = after_from.split()[0].strip().rstrip(";") if after_from else "t1"
            # find the table after JOIN (search original string, case-insensitive)
            join_idx = q.upper().find(" JOIN ")
            after_join = q[join_idx + 6:].strip() if join_idx >= 0 else ""
            t2 = after_join.split()[0].strip().rstrip(";,") if after_join else "t2"
            old_frag = f" JOIN {t2}"
            new_frag = f" JOIN {t2} ON {t1}.id = {t2}.id"
            q = q.replace(old_frag, new_frag, 1)
            if q != parent:
                return q, "+ON"

    if "leading_wildcard" in issues:
        q = q.replace("LIKE '%", "LIKE '").replace("LIKE \"%", "LIKE \"")
        return q, "fix_wildcard"

    if "select_star" in issues:
        q = q.upper().replace("SELECT *", "SELECT id", 1)
        # preserve original case for the rest
        idx = parent.upper().index("SELECT *")
        q = parent[:idx] + "SELECT id" + parent[idx + 8:]
        return q, "*→id"

    if "join_no_filter" in issues:
        # add a WHERE clause
        insert_pos = q.upper().rfind("LIMIT")
        if insert_pos == -1:
            q = q + " WHERE status = 'active'"
        else:
            q = q[:insert_pos] + "WHERE status = 'active' " + q[insert_pos:]
        return q, "+WHERE"

    if "no_limit" in issues:
        return q + " LIMIT 1", "+LIMIT"

    if "not_in" in issues:
        q = q.upper().replace("NOT IN", "NOT EXISTS")
        return q, "NOT IN→EXISTS"

    if "or_in_where" in issues:
        # can't easily fix OR without restructuring — mark as explored
        return q, "OR_explored"

    return q, "no-op"


def generate_pool_aware(memory, round_idx: int, seed: int, universe: str,
                        n: int = 10, explore_ratio: float = 0.3) -> list:
    """Memory-AWARE evolution: graft optimizations onto low-cost queries.

    Reads past queries' scores from evidence_kinds, picks the lowest-cost
    (best score) as grafting roots, and applies one optimization to each.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0x5D71)  # 'SQ'
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n, universe)

    # recover score from evidence_kinds
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

    clues.sort(key=lambda t: t[0], reverse=True)  # highest score first
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
        new_sql, graft_desc = _graft(root, rng)
        pool.append(make_query(new_sql, parent_body=root,
                               graft=graft_desc, inherited=("root",)))

    for _ in range(n_explore):
        pool.append(make_query(_rand_query(rng, universe)))

    rng.shuffle(pool)
    return pool


def _selftest():
    print("=== SQL candidate selftest ===")
    pool = generate_pool(0, 1, 6, "join_filter")
    for q in pool[:4]:
        print(f"  fam={q.family:18s} {q.body[:55]}")
    print("\n=== graft test ===")
    bad = "SELECT * FROM orders JOIN customers"
    new, desc = _graft(bad, random.Random(1))
    print(f"  before: {bad}")
    print(f"  after:  {new}  (graft: {desc})")
    new2, desc2 = _graft(new, random.Random(1))
    print(f"  after2: {new2}  (graft: {desc2})")


if __name__ == "__main__":
    _selftest()
