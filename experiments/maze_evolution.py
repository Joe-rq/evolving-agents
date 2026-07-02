"""experiments/maze_evolution.py — observe GENERATOR evolution in the maze domain.

This is NOT an amnesic-vs-full ablation (that lives in ablation_runner.py and
is 2048-specific, pre-registered, memory-INdependent by design). This experiment
asks a different question the 2048 one could not:

    "If the generator READS memory and extrapolates from successes, do we
     observe a cross-round evolution trajectory — new strategies growing
     out of past winners, best-efficiency climbing over rounds?"

The treatment is the GENERATOR (memory-aware vs baseline), not the Memory
ledger. We run two parallel single-group trajectories:

  FULL  : generate_pool_aware(memory, ...) — extrapolates from successes.
  BASE  : generate_pool(             ...) — memory-independent (control).

Both use an ACCUMULATING memory (so blocking/rules still apply in both); the
ONLY difference is whether the generator itself learns. If FULL's best
efficiency climbs while BASE's plateaus, that is OBSERVABLE generator
evolution — the thing 2048 structurally could not show.

Honesty notes (this is what the case study will claim):
  - We claim an OBSERVABLE trajectory, not a statistically-proven effect.
  - It is a single (seeded) trajectory, not an M-replicate controlled trial.
  - Mechanism (block/pivot/rule) is reported separately from the trajectory.

Run:  python3 -m experiments.maze_evolution -R 8
Smoke: python3 -m experiments.maze_evolution -R 3
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
from adapters.maze import (
    MazeAdapter, MAZE_RULE_SPECS, make_execute,
    generate_pool, generate_pool_aware,
)


def _stable_hash(s: str) -> int:
    h = 0
    for ch in s:
        h = (h * 131 + ord(ch)) & 0x7FFFFFFF
    return h


def _seed_fn(body, round_idx, replicate):
    return _stable_hash(body) + round_idx * 1_000_003 + replicate * 97


def _run_trajectory(
    group: str,            # "full" or "base"
    size: int, R: int, K: int, pool_n: int, max_execute: int, seed: int,
    alpha: float = 1.0,
):
    """Run one evolution trajectory. Returns per-round record + lineage.

    group="full" uses the memory-aware generator; "base" uses the baseline.
    Both maintain their OWN accumulating memory (so Factor 1/3 blocking works
    in both) — the difference is ONLY generation. Metric is mean_cost (lower
    is better) under the resource-constraint scoring (step_ratio + alpha·compute).
    """
    adapter = MazeAdapter()
    mem = Memory()
    universe = f"{size}x{size}"
    rounds = []
    for r in range(R):
        if group == "full":
            pool = generate_pool_aware(mem, round_idx=r, seed=seed, universe=universe, n=pool_n)
        else:
            pool = generate_pool(round_idx=r, seed=seed, n=pool_n)

        exe = make_execute(size=size, K=K, alpha=alpha,
                           seed_fn=lambda b, _r=r, _rep=seed: _seed_fn(b, _r, _rep))
        engine = Engine(adapter, mem, MAZE_RULE_SPECS)
        res = engine.run(pool, universe=universe,
                         execute=lambda c, _e=exe: _e(c, r, seed),
                         max_execute=max_execute)

        executed = []
        best_cost = 99.0  # lower is better
        for sc, outcome in res["executed"]:
            cand = sc.candidate
            executed.append({
                "body": getattr(cand, "body", str(cand)),
                "family": sc.family,
                "success": bool(outcome.get("success")) if outcome else False,
                "weak": bool(outcome.get("weak")) if outcome else False,
                "mean_cost": outcome.get("mean_cost", 99.0) if outcome else 99.0,
                "parent_body": getattr(cand, "parent_body", ""),
                "inherited": list(getattr(cand, "inherited", ())),
                "evidence_kinds": sorted(outcome.get("evidence_kinds", set())) if outcome else [],
            })
            if outcome:
                best_cost = min(best_cost, outcome.get("mean_cost", 99.0))

        extrapolated = [e for e in executed if e["parent_body"]]
        rules = mem.project_rules(MAZE_RULE_SPECS, universe)
        fam_scores = engine.ml.score_families(mem, universe)

        rounds.append({
            "round": r,
            "pool_size": len(pool),
            "executed_n": len(executed),
            "blocked_n": sum(1 for s in res["scored"] if s.block_reason),
            "pivot": bool(res["pivot"]),
            "pivot_rec": res["pivot_recommendation"],
            "successes_n": sum(1 for e in executed if e["success"]),
            "weak_n": sum(1 for e in executed if e["weak"]),
            "best_cost": round(best_cost, 3),
            "rules_n": len(rules),
            "rules": [{"motif": rule.motif, "action": rule.action,
                       "adj": rule.score_adjustment, "evidence_n": rule.evidence_count}
                      for rule in rules],
            "family_scores": {k: round(v, 3) for k, v in fam_scores.items()},
            "extrapolated_n": len(extrapolated),
            "lineage": extrapolated,
            "executed": executed,
        })
    return {"group": group, "rounds": rounds}


def main(R: int = 8, size: int = 10, K: int = 3, pool_n: int = 12,
         max_execute: int = 4, seed: int = 1, alpha: float = 1.0, out_path=None) -> dict:
    print(f"=== maze evolution | size={size} R={R} K={K} alpha={alpha} (LOWER cost = better) ===")
    full = _run_trajectory("full", size, R, K, pool_n, max_execute, seed, alpha)
    base = _run_trajectory("base", size, R, K, pool_n, max_execute, seed, alpha)

    full_costs = [rd["best_cost"] for rd in full["rounds"]]
    base_costs = [rd["best_cost"] for rd in base["rounds"]]
    total_lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])

    print("\nround | FULL best_cost (extrap) | BASE best_cost    [lower=better]")
    for fr, br in zip(full["rounds"], base["rounds"]):
        print(f"  {fr['round']:>2}  |   {fr['best_cost']:5.2f}   ({fr['extrapolated_n']} children) |   {br['best_cost']:5.2f}")

    print(f"\nFULL: best_cost {full_costs[0]:.2f} -> {full_costs[-1]:.2f} | "
          f"total extrapolated children: {total_lineage}")
    print(f"BASE: best_cost {base_costs[0]:.2f} -> {base_costs[-1]:.2f} | "
          f"(memory-independent generator)")

    result = {
        "params": {"size": size, "R": R, "K": K, "pool_n": pool_n,
                   "max_execute": max_execute, "seed": seed, "alpha": alpha},
        "summary": {
            "full_cost_curve": full_costs, "base_cost_curve": base_costs,
            "full_cost_start": full_costs[0], "full_cost_end": full_costs[-1],
            "base_cost_start": base_costs[0], "base_cost_end": base_costs[-1],
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
    ap.add_argument("--size", type=int, default=10, help="maze size")
    ap.add_argument("-K", type=int, default=3, help="mazes per execute")
    ap.add_argument("--pool", type=int, default=12, help="pool size per round")
    ap.add_argument("--mx", type=int, default=4, help="max_execute per round")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--alpha", type=float, default=1.0, help="compute-cost weight in total cost")
    ap.add_argument("--out", type=str, default="experiments/_maze_evolution_result.json")
    a = ap.parse_args()
    main(R=a.R, size=a.size, K=a.K, pool_n=a.pool, max_execute=a.mx,
         seed=a.seed, alpha=a.alpha, out_path=a.out)
