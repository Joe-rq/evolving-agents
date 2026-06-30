"""experiments/ablation_runner.py — amnesic vs full paired ablation over 2048.

Drives M replicates x R rounds. Per replicate:
  - shared candidate pool each round (memory-independent generator)
  - deterministic execute seed per (body, round, replicate)  [stable hash!]
  - FULL group   : one Memory accumulating across rounds
  - AMNESIC group: fresh Memory() every round   <- the only treatment variable
The engine itself is untouched. Collects the primary metric (per-round mean
log2(max_tile) over executed candidates) + mechanism-level evidence (blocks,
family strikes, projected rules, pivot recommendations).

Run:  python3 -m experiments.ablation_runner -M 30
Smoke: python3 -m experiments.ablation_runner -M 1 -K 10
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from core.engine import Engine
from core.memory import Memory
from adapters.game2048 import Game2048Adapter, GAME2048_RULE_SPECS, make_execute, generate_pool
from experiments.stats import summarize

TAIL_H = 4  # pre-registered: primary uses the last H rounds
WARMUP = 2  # pre-registered: first W rounds execute the FULL pool (explore) so every
             # family accumulates failure evidence; later rounds use max_execute (exploit).


def _stable_hash(s: str) -> int:
    """Deterministic string hash (Python's hash() is salted per process)."""
    h = 0
    for ch in s:
        h = (h * 131 + ord(ch)) & 0x7FFFFFFF
    return h


def _mean_log2_tile(executed):
    """Mean log2(max_tile) over executed candidates' outcomes this round."""
    vals = []
    for _sc, outcome in executed:
        if outcome and isinstance(outcome, dict) and outcome.get("max_tile", 0) > 0:
            vals.append(math.log2(outcome["max_tile"]))
    return sum(vals) / len(vals) if vals else 0.0


def run_one_replicate(seed: int, size: int = 4, R: int = 8, K: int = 20,
                      max_execute: int = 3, pool_n: int = 15) -> dict:
    adapter = Game2048Adapter()
    full_mem = Memory()
    full_curve, amn_curve = [], []
    mech = {"full_blocks": 0, "amn_blocks": 0,
            "full_pivots": 0, "amn_pivots": 0,
            "full_rules_final": 0, "full_struck": []}

    universe = f"{size}x{size}"
    for r in range(R):
        pool = generate_pool(round_idx=r, seed=seed, n=pool_n)

        def seed_fn(body, _r=r, _s=seed):
            return _stable_hash(body) + _r * 1_000_003 + _s * 97

        execute = make_execute(size=size, K=K, seed_fn=seed_fn)
        mx = pool_n if r < WARMUP else max_execute  # warmup explores fully; test exploits

        # --- FULL: accumulating memory ---
        full_engine = Engine(adapter, full_mem, GAME2048_RULE_SPECS)
        full_res = full_engine.run(pool, universe=universe, execute=execute, max_execute=mx)
        full_curve.append(_mean_log2_tile(full_res["executed"]))
        mech["full_blocks"] += sum(1 for s in full_res["scored"] if s.block_reason)
        mech["full_pivots"] += 1 if full_res["pivot"] else 0
        fam_full = full_engine.ml.score_families(full_mem, universe)
        mech["full_struck"] = sorted(f for f, s in fam_full.items() if s < 0)
        mech["full_rules_final"] = len(full_mem.project_rules(GAME2048_RULE_SPECS, universe))

        # --- AMNESIC: fresh memory each round (the treatment variable) ---
        amn_mem = Memory()
        amn_engine = Engine(adapter, amn_mem, GAME2048_RULE_SPECS)
        amn_res = amn_engine.run(pool, universe=universe, execute=execute, max_execute=mx)
        amn_curve.append(_mean_log2_tile(amn_res["executed"]))
        mech["amn_blocks"] += sum(1 for s in amn_res["scored"] if s.block_reason)
        mech["amn_pivots"] += 1 if amn_res["pivot"] else 0

    tail_full = sum(full_curve[-TAIL_H:]) / TAIL_H
    tail_amn = sum(amn_curve[-TAIL_H:]) / TAIL_H
    return {
        "seed": seed,
        "primary_diff": round(tail_full - tail_amn, 4),
        "tail_full": round(tail_full, 3),
        "tail_amn": round(tail_amn, 3),
        "full_curve": [round(x, 3) for x in full_curve],
        "amn_curve": [round(x, 3) for x in amn_curve],
        "mechanism": mech,
    }


def _p_lt(p, thr):
    if isinstance(p, str):  # "<1e-6"
        return True
    return p is not None and p < thr


def main(M: int = 30, R: int = 8, K: int = 20, size: int = 4, out_path=None) -> dict:
    diffs, reps = [], []
    for s in range(M):
        rep = run_one_replicate(seed=s + 1, size=size, R=R, K=K)
        reps.append(rep)
        diffs.append(rep["primary_diff"])
        if s == 0 or (s + 1) % 5 == 0:
            print(f"  rep {s+1:>2}/{M}: diff={rep['primary_diff']:+.3f}  "
                  f"full_tail={rep['tail_full']:.2f} amn_tail={rep['tail_amn']:.2f}  "
                  f"full_blocks={rep['mechanism']['full_blocks']} amn_blocks={rep['mechanism']['amn_blocks']}")

    summary = summarize(diffs)
    agg = {
        "full_blocks_total": sum(r["mechanism"]["full_blocks"] for r in reps),
        "amn_blocks_total": sum(r["mechanism"]["amn_blocks"] for r in reps),
        "full_pivots_total": sum(r["mechanism"]["full_pivots"] for r in reps),
        "amn_pivots_total": sum(r["mechanism"]["amn_pivots"] for r in reps),
        "full_rules_final_mean": round(sum(r["mechanism"]["full_rules_final"] for r in reps) / len(reps), 2),
        "full_struck_union": sorted({f for r in reps for f in r["mechanism"]["full_struck"]}),
    }
    median = summary.get("median_diff", 0.0)
    p = summary.get("p_two_tailed")
    verdict = "positive" if (median > 0 and _p_lt(p, 0.05)) else "null"

    result = {
        "params": {"M": M, "R": R, "K": K, "size": size, "H": TAIL_H},
        "primary_metric": "mean_log2_max_tile_tail4_full_minus_amnesic",
        "summary": summary,
        "verdict": verdict,
        "mechanism": agg,
        "replicates": reps,
    }
    print("\n=== RESULT ===")
    print(f"primary: n={summary.get('n')} mean={summary.get('mean_diff'):+.4f} "
          f"median={median:+.4f} ci95={summary.get('ci95')} p={p} "
          f"n_pos={summary.get('n_positive')}/{summary.get('n')}")
    print(f"verdict (pre-registered alpha=0.05): {verdict.upper()}")
    print(f"mechanism: full_blocks={agg['full_blocks_total']} amn_blocks={agg['amn_blocks_total']} | "
          f"full_pivots={agg['full_pivots_total']} amn_pivots={agg['amn_pivots_total']} | "
          f"rules_mean={agg['full_rules_final_mean']} struck={agg['full_struck_union']}")

    if out_path:
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=2)
        print(f"wrote {out_path}")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-M", type=int, default=30, help="replicates")
    ap.add_argument("-R", type=int, default=8, help="rounds per replicate")
    ap.add_argument("-K", type=int, default=20, help="games per execute")
    ap.add_argument("--size", type=int, default=4, help="board size")
    ap.add_argument("--out", type=str, default="experiments/_ablation_result.json")
    a = ap.parse_args()
    main(M=a.M, R=a.R, K=a.K, size=a.size, out_path=a.out)
