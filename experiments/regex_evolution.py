"""experiments/regex_evolution.py — observe GENERATOR evolution via constraint grafting.

Same experimental design as symreg_evolution: two parallel single-group
trajectories (FULL = memory-aware grafting, BASE = memory-independent control).
Metric is F1 (higher = better) against a hidden target's example set.

The story regex tells that symreg can't: it's a PROGRAM-SYNTHESIS task —
induce a rule from labeled examples. The evolution is "from too-wide to
just-right": the generator grafts tightening constraints onto high-F1 patterns,
climbing F1 = 0.5 (too wide) → 0.7 (partial) → 0.9+ (precise).

Honesty: same as symreg — single (seeded) trajectory per target, not an
M-replicate controlled trial. Observable evolution, not statistically proven.

Run:  python3 -m experiments.regex_evolution -R 8
Smoke: python3 -m experiments.regex_evolution -R 3
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
from adapters.regex import (
    RegexAdapter, REGEX_RULE_SPECS, make_execute,
    generate_pool, generate_pool_aware,
)


def _run_trajectory(group: str, universe: str, R: int, pool_n: int,
                    max_execute: int, seed: int):
    adapter = RegexAdapter()
    mem = Memory()
    exe = make_execute(universe)
    rounds = []
    for r in range(R):
        if group == "full":
            pool = generate_pool_aware(mem, round_idx=r, seed=seed,
                                       universe=universe, n=pool_n)
        else:
            pool = generate_pool(round_idx=r, seed=seed, n=pool_n)

        engine = Engine(adapter, mem, REGEX_RULE_SPECS)
        res = engine.run(pool, universe=universe, execute=exe,
                         max_execute=max_execute)

        executed = []
        best_f1 = -1.0
        for sc, outcome in res["executed"]:
            cand = sc.candidate
            f1 = outcome.get("f1", -1.0) if outcome else -1.0
            best_f1 = max(best_f1, f1)
            executed.append({
                "body": getattr(cand, "body", str(cand)),
                "family": sc.family,
                "f1": f1,
                "success": bool(outcome.get("success")) if outcome else False,
                "weak": bool(outcome.get("weak")) if outcome else False,
                "precision": outcome.get("precision", 0) if outcome else 0,
                "recall": outcome.get("recall", 0) if outcome else 0,
                "parent_body": getattr(cand, "parent_body", ""),
                "graft": getattr(cand, "graft", ""),
            })

        lineage = [e for e in executed if e["parent_body"]]
        rules = mem.project_rules(REGEX_RULE_SPECS, universe)
        fam_scores = engine.ml.score_families(mem, universe)

        rounds.append({
            "round": r,
            "pool_size": len(pool),
            "executed_n": len(executed),
            "blocked_n": sum(1 for s in res["scored"] if s.block_reason),
            "pivot": bool(res["pivot"]),
            "best_f1": round(best_f1, 4),
            "successes_n": sum(1 for e in executed if e["success"]),
            "weak_n": sum(1 for e in executed if e["weak"]),
            "rules_n": len(rules),
            "family_scores": {k: round(v, 3) for k, v in fam_scores.items()},
            "extrapolated_n": len(lineage),
            "lineage": lineage,
            "executed": executed,
        })
    return {"group": group, "universe": universe, "rounds": rounds}


def main(R: int = 8, universe: str = "date_iso", pool_n: int = 12,
         max_execute: int = 5, seed: int = 1, out_path=None) -> dict:
    from adapters.regex import target_label
    print(f"=== regex evolution | target={universe} ({target_label(universe)}) R={R} ===")
    full = _run_trajectory("full", universe, R, pool_n, max_execute, seed)
    base = _run_trajectory("base", universe, R, pool_n, max_execute, seed)

    full_f1 = [rd["best_f1"] for rd in full["rounds"]]
    base_f1 = [rd["best_f1"] for rd in base["rounds"]]
    total_lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])

    print("\nround | FULL best_f1 (extrap) | BASE best_f1")
    for fr, br in zip(full["rounds"], base["rounds"]):
        print(f"  {fr['round']:>2}  |   {fr['best_f1']:.3f}   "
              f"({fr['extrapolated_n']} children) |   {br['best_f1']:.3f}")

    print(f"\nFULL: best_f1 {full_f1[0]:.3f} -> {full_f1[-1]:.3f} | "
          f"total extrapolated children: {total_lineage}")
    print(f"BASE: best_f1 {base_f1[0]:.3f} -> {base_f1[-1]:.3f}")

    all_succ = [e for rd in full["rounds"] for e in rd["executed"] if e["success"]]
    if all_succ:
        best = max(all_succ, key=lambda e: e["f1"])
        print(f"\nBest FULL pattern: {best['body']}  F1={best['f1']}")
        if best["parent_body"]:
            print(f"  grew from: {best['parent_body']}  via graft: {best['graft']}")

    result = {
        "params": {"universe": universe, "target": target_label(universe),
                   "R": R, "pool_n": pool_n, "max_execute": max_execute, "seed": seed},
        "summary": {
            "full_f1_curve": full_f1, "base_f1_curve": base_f1,
            "full_f1_start": full_f1[0], "full_f1_end": full_f1[-1],
            "base_f1_start": base_f1[0], "base_f1_end": base_f1[-1],
            "full_extrapolated_total": total_lineage,
        },
        "full": full, "base": base,
    }

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nwrote {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-R", type=int, default=8)
    ap.add_argument("--target", type=str, default="date_iso",
                    choices=["date_iso", "email", "phone_cn"])
    ap.add_argument("--pool", type=int, default=12)
    ap.add_argument("--mx", type=int, default=5)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=str, default="experiments/_regex_evolution_result.json")
    a = ap.parse_args()
    main(R=a.R, universe=a.target, pool_n=a.pool, max_execute=a.mx,
         seed=a.seed, out_path=a.out)
