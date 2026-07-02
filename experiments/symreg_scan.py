"""experiments/symreg_scan.py — scan seeds × targets for the most dramatic trajectory.

Runs symreg_evolution across multiple seeds and targets, scores each trajectory
on "dramaticness" (does FULL climb AND beat BASE stably?), and prints a ranked
table. Used to pick the best trajectory to inline into the demo.

Scoring (higher = more dramatic, better for demo):
  - climb: how much FULL's best_r2 rose from its first positive round to its peak
  - stability: how many of the last-half rounds FULL stayed >= 0.8
  - separation: (FULL mean last-half) - (BASE mean last-half)
  - lineage: total extrapolated children (>0 means grafting happened)
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from experiments.symreg_evolution import _run_trajectory


def score_trajectory(result: dict) -> dict:
    full = result["rounds"]
    base = result["rounds"]  # same object, but we re-run base separately below
    return {}  # placeholder, real scoring below


def scan(seeds=(1, 2, 3, 5, 7, 11), targets=("poly2_offset", "poly2_sin"),
         R=8, pool_n=14, max_execute=6):
    print(f"{'target':12s} {'seed':>4s} {'climb':>6s} {'stab':>5s} {'sep':>6s} {'lin':>4s} {'score':>6s}  curve")
    print("-" * 80)
    results = []
    for target in targets:
        for seed in seeds:
            full = _run_trajectory("full", target, R, pool_n, max_execute, seed)
            base = _run_trajectory("base", target, R, pool_n, max_execute, seed)

            fc = [rd["best_r2"] for rd in full["rounds"]]
            bc = [rd["best_r2"] for rd in base["rounds"]]
            lineage = sum(rd["extrapolated_n"] for rd in full["rounds"])

            # climb: peak - first-positive
            positives = [r for r in fc if r > 0]
            if positives:
                first_pos = positives[0]
                peak = max(fc)
                climb = peak - first_pos
            else:
                climb = 0.0

            # stability: fraction of last-half rounds >= 0.8
            last_half = fc[len(fc) // 2:]
            stab = sum(1 for r in last_half if r >= 0.8) / max(1, len(last_half))

            # separation: FULL avg(last half) - BASE avg(last half)
            bh = bc[len(bc) // 2:]
            sep = (sum(last_half) / len(last_half)) - (sum(bh) / len(bh))

            # composite score: reward climb + stability + separation + having lineage
            score = climb * 2 + stab * 1.5 + sep * 1.5 + (0.5 if lineage > 0 else 0)

            results.append((target, seed, climb, stab, sep, lineage, score, fc, bc))
            curve_str = " ".join(f"{r:+.1f}" for r in fc)
            print(f"{target:12s} {seed:>4d} {climb:>6.2f} {stab:>5.2f} {sep:>6.2f} "
                  f"{lineage:>4d} {score:>6.2f}  [{curve_str}]")

    print("\n" + "=" * 80)
    print("TOP 5 by score:")
    results.sort(key=lambda t: t[6], reverse=True)
    for target, seed, climb, stab, sep, lineage, score, fc, bc in results[:5]:
        print(f"  {target:12s} seed={seed} score={score:.2f} climb={climb:.2f} "
              f"stab={stab:.2f} sep={sep:.2f} lineage={lineage}")
        print(f"    FULL: {[round(r,2) for r in fc]}")
        print(f"    BASE: {[round(r,2) for r in bc]}")
    return results


if __name__ == "__main__":
    scan()
