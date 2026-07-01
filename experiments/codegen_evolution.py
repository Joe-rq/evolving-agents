"""experiments/codegen_evolution.py — observe code generation evolution."""
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
from adapters.codegen import (
    CodegenAdapter, CODEGEN_RULE_SPECS, make_execute,
    generate_pool, generate_pool_aware,
)


def _run_trajectory(group, universe, R, pool_n, max_execute, seed):
    adapter = CodegenAdapter()
    mem = Memory()
    exe = make_execute(universe)
    rounds = []
    for r in range(R):
        if group == "full":
            pool = generate_pool_aware(mem, r, seed, universe, pool_n)
        else:
            pool = generate_pool(r, seed, pool_n, universe)
        engine = Engine(adapter, mem, CODEGEN_RULE_SPECS)
        res = engine.run(pool, universe=universe, execute=exe, max_execute=max_execute)
        executed = []
        best_score = -1
        for sc, outcome in res["executed"]:
            score = outcome.get("score", -1) if outcome else -1
            best_score = max(best_score, score)
            executed.append({
                "body": getattr(sc.candidate, "body", str(sc.candidate)),
                "family": sc.family, "score": score,
                "passed": outcome.get("passed", 0) if outcome else 0,
                "total": outcome.get("total", 0) if outcome else 0,
                "success": bool(outcome.get("success")) if outcome else False,
                "parent_body": getattr(sc.candidate, "parent_body", ""),
                "graft": getattr(sc.candidate, "graft", ""),
            })
        lineage = [e for e in executed if e["parent_body"]]
        rounds.append({
            "round": r, "best_score": round(best_score, 3),
            "successes_n": sum(1 for e in executed if e["success"]),
            "extrapolated_n": len(lineage), "lineage": lineage, "executed": executed,
        })
    return {"group": group, "universe": universe, "rounds": rounds}


def main(R=8, universe="sum_squares", pool_n=12, max_execute=5, seed=1, out_path=None):
    from adapters.codegen import get_task
    task = get_task(universe)
    print(f"=== codegen evolution | task={universe} ({task.description}) R={R} ===")
    full = _run_trajectory("full", universe, R, pool_n, max_execute, seed)
    base = _run_trajectory("base", universe, R, pool_n, max_execute, seed)
    fs = [rd["best_score"] for rd in full["rounds"]]
    bs = [rd["best_score"] for rd in base["rounds"]]
    total_lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])
    print("\nround | FULL best_score (extrap) | BASE best_score")
    for fr, br in zip(full["rounds"], base["rounds"]):
        print(f"  {fr['round']:>2}  |   {fr['best_score']:.2f}   ({fr['extrapolated_n']} children) |   {br['best_score']:.2f}")
    print(f"\nFULL: {fs[0]:.2f} -> {fs[-1]:.2f} | graft children: {total_lineage}")
    print(f"BASE: {bs[0]:.2f} -> {bs[-1]:.2f}")
    all_succ = [e for rd in full["rounds"] for e in rd["executed"] if e["success"]]
    if all_succ:
        print(f"\nBest FULL (all tests passed): {all_succ[0]['body'][:60]}")
        if all_succ[0]["parent_body"]:
            print(f"  grew from: {all_succ[0]['parent_body'][:40]} via: {all_succ[0]['graft']}")
    result = {"summary": {"full_curve": fs, "base_curve": bs, "lineage_total": total_lineage},
              "full": full, "base": base}
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nwrote {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-R", type=int, default=8)
    ap.add_argument("--task", type=str, default="sum_squares",
                    choices=["sum_squares", "count_vowels", "max_diff"])
    ap.add_argument("--pool", type=int, default=12)
    ap.add_argument("--mx", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=str, default="experiments/_codegen_evolution_result.json")
    a = ap.parse_args()
    main(R=a.R, universe=a.task, pool_n=a.pool, max_execute=a.mx, seed=a.seed, out_path=a.out)
