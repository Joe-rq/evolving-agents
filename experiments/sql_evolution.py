"""experiments/sql_evolution.py — observe query optimization evolution.

Same design as symreg/regex evolution: FULL (memory-aware grafting) vs
BASE (memory-independent). Metric is query cost (lower = better).

The story SQL tells: the same "tighten" evolution as regex, but in a
production-relevant domain (query optimization). Grafting removes
anti-patterns: SELECT * → SELECT id, add ON to cartesian join, fix
leading wildcard. Cost drops from ~15 (bad) to ~1 (optimal).

Run:  python3 -m experiments.sql_evolution -R 8
"""
from __future__ import annotations

import argparse
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.engine import Engine
from core.memory import Memory
from adapters.sql import (
    SQLAdapter, SQL_RULE_SPECS, make_execute,
    generate_pool, generate_pool_aware,
)


def _run_trajectory(group, universe, R, pool_n, max_execute, seed):
    adapter = SQLAdapter()
    mem = Memory()
    exe = make_execute(universe)
    rounds = []
    for r in range(R):
        if group == "full":
            pool = generate_pool_aware(mem, r, seed, universe, pool_n)
        else:
            pool = generate_pool(r, seed, pool_n, universe)

        engine = Engine(adapter, mem, SQL_RULE_SPECS)
        res = engine.run(pool, universe=universe, execute=exe, max_execute=max_execute)

        executed = []
        best_cost = 99.0
        for sc, outcome in res["executed"]:
            cost = outcome.get("cost", 99) if outcome else 99
            best_cost = min(best_cost, cost)
            executed.append({
                "body": getattr(sc.candidate, "body", str(sc.candidate)),
                "family": sc.family,
                "cost": cost,
                "score": outcome.get("score", 0) if outcome else 0,
                "success": bool(outcome.get("success")) if outcome else False,
                "parent_body": getattr(sc.candidate, "parent_body", ""),
                "graft": getattr(sc.candidate, "graft", ""),
            })

        lineage = [e for e in executed if e["parent_body"]]
        rules = mem.project_rules(SQL_RULE_SPECS, universe)
        fam_scores = engine.ml.score_families(mem, universe)

        rounds.append({
            "round": r, "pool_size": len(pool), "executed_n": len(executed),
            "blocked_n": sum(1 for s in res["scored"] if s.block_reason),
            "best_cost": round(best_cost, 2),
            "successes_n": sum(1 for e in executed if e["success"]),
            "rules_n": len(rules),
            "family_scores": {k: round(v, 3) for k, v in fam_scores.items()},
            "extrapolated_n": len(lineage), "lineage": lineage,
            "executed": executed,
        })
    return {"group": group, "universe": universe, "rounds": rounds}


def main(R=8, universe="join_filter", pool_n=12, max_execute=5, seed=1, out_path=None):
    print(f"=== SQL evolution | task={universe} R={R} (LOWER cost = better) ===")
    full = _run_trajectory("full", universe, R, pool_n, max_execute, seed)
    base = _run_trajectory("base", universe, R, pool_n, max_execute, seed)

    fc = [rd["best_cost"] for rd in full["rounds"]]
    bc = [rd["best_cost"] for rd in base["rounds"]]
    total_lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])

    print("\nround | FULL best_cost (extrap) | BASE best_cost")
    for fr, br in zip(full["rounds"], base["rounds"]):
        print(f"  {fr['round']:>2}  |   {fr['best_cost']:5.1f}   ({fr['extrapolated_n']} children) |   {br['best_cost']:5.1f}")

    print(f"\nFULL: cost {fc[0]:.1f} -> {fc[-1]:.1f} | graft children: {total_lineage}")
    print(f"BASE: cost {bc[0]:.1f} -> {bc[-1]:.1f}")

    all_succ = [e for rd in full["rounds"] for e in rd["executed"] if e["success"]]
    if all_succ:
        best = min(all_succ, key=lambda e: e["cost"])
        print(f"\nBest FULL query (cost={best['cost']}): {best['body'][:70]}")
        if best["parent_body"]:
            print(f"  grew from: {best['parent_body'][:50]}  via: {best['graft']}")

    result = {"params": {"universe": universe, "R": R, "pool_n": pool_n,
                         "max_execute": max_execute, "seed": seed},
              "summary": {"full_cost_curve": fc, "base_cost_curve": bc,
                          "full_extrapolated_total": total_lineage},
              "full": full, "base": base}
    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nwrote {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-R", type=int, default=8)
    ap.add_argument("--task", type=str, default="join_filter",
                    choices=["join_filter", "simple_lookup", "range_search"])
    ap.add_argument("--pool", type=int, default=12)
    ap.add_argument("--mx", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=str, default="experiments/_sql_evolution_result.json")
    a = ap.parse_args()
    main(R=a.R, universe=a.task, pool_n=a.pool, max_execute=a.mx, seed=a.seed, out_path=a.out)
