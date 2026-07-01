"""experiments/symreg_evolution.py — observe GENERATOR evolution via AST grafting.

The signature experiment for "true evolution" in this repo. Unlike maze (low
ceiling) or 2048 (binary gate + memory-independent generator), symbolic
regression has:
  - a graded R² gate with a continuous gradient (0 → 0.5 → 0.9 → 1.0), AND
  - a memory-aware generator that GRAFTS new structure onto winning formulas.

So a cross-round trajectory can show: random formulas (R²≈0) → a poly family
partial hit (R²≈0.6, weak) → grafting an offset onto it (R²→1.0, success).
Each step is a structurally new, human-readable formula. That is the evolution
this domain was chosen to make visible.

Two parallel single-group trajectories, same design as maze_evolution:
  FULL : generate_pool_aware(memory, ...) — grafts onto winners.
  BASE : generate_pool(...)               — memory-independent (control).

If FULL's best R² climbs past where BASE plateaus, and FULL produces a lineage
of children visibly grown from prior winners, that is OBSERVABLE generator
evolution.

Honesty (what the case study will claim / NOT claim):
  - We claim an OBSERVABLE trajectory + lineage, not a statistically-proven effect.
  - It is a single (seeded) trajectory, not an M-replicate trial.
  - Mechanism (block/pivot/rule) reported separately from the trajectory.

Run:  python3 -m experiments.symreg_evolution -R 8
Smoke: python3 -m experiments.symreg_evolution -R 3
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
from adapters.symreg import (
    SymregAdapter, SYMREG_RULE_SPECS, make_execute,
    generate_pool, generate_pool_aware,
)


def _run_trajectory(group: str, universe: str, R: int, pool_n: int,
                    max_execute: int, seed: int):
    """Run one evolution trajectory. Returns per-round record + lineage.

    group="full" grafts onto winners (memory-aware); "base" is the control.
    Both maintain their OWN accumulating memory so blocking/rules apply to
    both — the ONLY difference is whether the generator itself learns.
    """
    adapter = SymregAdapter()
    mem = Memory()
    exe = make_execute(universe)
    rounds = []
    for r in range(R):
        if group == "full":
            pool = generate_pool_aware(mem, round_idx=r, seed=seed,
                                       universe=universe, n=pool_n)
        else:
            pool = generate_pool(round_idx=r, seed=seed, n=pool_n)

        engine = Engine(adapter, mem, SYMREG_RULE_SPECS)
        res = engine.run(pool, universe=universe, execute=exe,
                         max_execute=max_execute)

        executed = []
        best_r2 = -2.0
        for sc, outcome in res["executed"]:
            cand = sc.candidate
            r2 = outcome.get("r2", -2.0) if outcome else -2.0
            best_r2 = max(best_r2, r2)
            executed.append({
                "body": getattr(cand, "body", str(cand)),
                "family": sc.family,
                "r2": r2,
                "success": bool(outcome.get("success")) if outcome else False,
                "weak": bool(outcome.get("weak")) if outcome else False,
                "complexity": outcome.get("complexity", 0) if outcome else 0,
                "parent_body": getattr(cand, "parent_body", ""),
                "graft": getattr(cand, "graft", ""),
                "evidence_kinds": sorted(outcome.get("evidence_kinds", set())) if outcome else [],
            })

        lineage = [e for e in executed if e["parent_body"]]
        rules = mem.project_rules(SYMREG_RULE_SPECS, universe)
        fam_scores = engine.ml.score_families(mem, universe)

        rounds.append({
            "round": r,
            "pool_size": len(pool),
            "executed_n": len(executed),
            "blocked_n": sum(1 for s in res["scored"] if s.block_reason),
            "pivot": bool(res["pivot"]),
            "pivot_rec": res["pivot_recommendation"],
            "best_r2": round(best_r2, 4),
            "successes_n": sum(1 for e in executed if e["success"]),
            "weak_n": sum(1 for e in executed if e["weak"]),
            "rules_n": len(rules),
            "family_scores": {k: round(v, 3) for k, v in fam_scores.items()},
            "extrapolated_n": len(lineage),
            "lineage": lineage,
            "executed": executed,
        })
    return {"group": group, "universe": universe, "rounds": rounds}


def main(R: int = 8, universe: str = "poly2_offset", pool_n: int = 12,
         max_execute: int = 5, seed: int = 1, out_path=None) -> dict:
    from adapters.symreg import target_label
    print(f"=== symreg evolution | target={universe} ({target_label(universe)}) "
          f"R={R} ===")
    full = _run_trajectory("full", universe, R, pool_n, max_execute, seed)
    base = _run_trajectory("base", universe, R, pool_n, max_execute, seed)

    full_r2 = [rd["best_r2"] for rd in full["rounds"]]
    base_r2 = [rd["best_r2"] for rd in base["rounds"]]
    total_lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])

    print("\nround | FULL best_r2 (extrap/children) | BASE best_r2")
    for fr, br in zip(full["rounds"], base["rounds"]):
        print(f"  {fr['round']:>2}  |   {fr['best_r2']:+.3f}   "
              f"({fr['extrapolated_n']} children) |   {br['best_r2']:+.3f}")

    print(f"\nFULL: best_r2 {full_r2[0]:+.3f} -> {full_r2[-1]:+.3f} | "
          f"total extrapolated children: {total_lineage}")
    print(f"BASE: best_r2 {base_r2[0]:+.3f} -> {base_r2[-1]:+.3f} "
          f"(memory-independent generator)")

    # show the winning formula lineage (the headline of the case study)
    all_succ = [e for rd in full["rounds"] for e in rd["executed"] if e["success"]]
    if all_succ:
        best = max(all_succ, key=lambda e: e["r2"])
        print(f"\nBest FULL formula: {best['body']}  R²={best['r2']}")
        if best["parent_body"]:
            print(f"  grew from: {best['parent_body']}  via graft: {best['graft']}")

    result = {
        "params": {"universe": universe, "target": target_label(universe),
                   "R": R, "pool_n": pool_n, "max_execute": max_execute, "seed": seed},
        "summary": {
            "full_r2_curve": full_r2, "base_r2_curve": base_r2,
            "full_r2_start": full_r2[0], "full_r2_end": full_r2[-1],
            "base_r2_start": base_r2[0], "base_r2_end": base_r2[-1],
            "full_extrapolated_total": total_lineage,
        },
        "full": full,
        "base": base,
    }

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nwrote {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-R", type=int, default=8, help="rounds")
    ap.add_argument("--target", type=str, default="poly2_offset",
                    choices=["poly2_offset", "poly2_sin", "linear"])
    ap.add_argument("--pool", type=int, default=12, help="pool size per round")
    ap.add_argument("--mx", type=int, default=5, help="max_execute per round")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out", type=str, default="experiments/_symreg_evolution_result.json")
    a = ap.parse_args()
    main(R=a.R, universe=a.target, pool_n=a.pool, max_execute=a.mx,
         seed=a.seed, out_path=a.out)
