"""experiments/stats.py — minimal paired-difference statistics (stdlib only).

Used by the amnesic-vs-full ablation. Analysis unit is the replicate: each
replicate yields one paired difference (full - amnesic) on the primary metric,
and the M differences are tested with a paired Wilcoxon signed-rank + bootstrap
CI. No scipy — everything is stdlib so the result is reproducible everywhere.

Rounding policy: p-values below 1e-6 are reported as <1e-6 (the normal
approximation is not trustworthy that far in the tail anyway).
"""
from __future__ import annotations

import math
import random
from collections import Counter


def _norm_sf(z: float) -> float:
    """Survival function P(Z > z) for standard normal, via erfc."""
    return math.erfc(z / math.sqrt(2.0)) / 2.0


def wilcoxon_signed_rank(diffs, zero_tol: float = 1e-12):
    """Paired Wilcoxon signed-rank on differences (full - amnesic).

    Returns (W_plus, p_two_tailed). Normal approximation with tie correction
    + continuity correction; valid for n >= ~10. Pure stdlib.
    """
    d = [x for x in diffs if abs(x) > zero_tol]
    n = len(d)
    if n == 0:
        return 0.0, 1.0
    if n < 1:
        return 0.0, 1.0

    order = sorted(range(n), key=lambda i: abs(d[i]))
    ranks = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and abs(d[order[j + 1]]) == abs(d[order[i]]):
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0  # 1-indexed average over the tie group
        for k in range(i, j + 1):
            ranks[order[k]] = avg_rank
        i = j + 1

    w_plus = sum(r for r, dd in zip(ranks, d) if dd > 0)

    mean = n * (n + 1) / 4.0
    tie_counts = Counter(abs(x) for x in d)
    tie_term = sum(t ** 3 - t for t in tie_counts.values() if t > 1)
    var = n * (n + 1) * (2 * n + 1) / 24.0 - tie_term / 48.0
    if var <= 0:
        return w_plus, 1.0
    z = (abs(w_plus - mean) - 0.5) / math.sqrt(var)  # continuity correction
    p = min(1.0, 2.0 * _norm_sf(z))
    return w_plus, p


def bootstrap_ci(diffs, B: int = 2000, seed: int = 0, stat: str = "median"):
    """Bootstrap 95% CI of the median (or mean) of the paired differences.

    Returns (point_estimate, (lo, hi)). Pure stdlib.
    """
    n = len(diffs)
    if n == 0:
        return 0.0, (0.0, 0.0)
    rng = random.Random(seed)

    def sOf(sample):
        s = sorted(sample)
        return s[n // 2] if stat == "median" else sum(sample) / n

    boot = []
    for _ in range(B):
        boot.append(sOf([diffs[rng.randrange(n)] for _ in range(n)]))
    boot.sort()
    lo = boot[int(0.025 * B)]
    hi = boot[int(0.975 * B)]
    point = sOf(diffs)
    return point, (lo, hi)


def mde_estimate(diffs, alpha: float = 0.05, power: float = 0.8):
    """Minimum detectable paired effect given observed sd of differences.

    MDE = (z_{1-a/2} + z_power) * sd / sqrt(n).  Uses the fixed z pair for the
    pre-registered (alpha=0.05, power=0.8): z=1.96 and z=0.842.
    """
    n = len(diffs)
    if n < 2:
        return float("inf")
    mean = sum(diffs) / n
    var = sum((x - mean) ** 2 for x in diffs) / (n - 1)
    sd = math.sqrt(var)
    z_alpha = 1.959964
    z_power = 0.841621
    return (z_alpha + z_power) * sd / math.sqrt(n)


def summarize(diffs):
    """One-shot summary used by the runner. Returns a plain dict."""
    if not diffs:
        return {"n": 0}
    w, p = wilcoxon_signed_rank(diffs)
    point, (lo, hi) = bootstrap_ci(diffs, B=2000, seed=0, stat="median")
    return {
        "n": len(diffs),
        "mean_diff": sum(diffs) / len(diffs),
        "median_diff": point,
        "ci95": [round(lo, 4), round(hi, 4)],
        "wilcoxon_W": round(w, 2),
        "p_two_tailed": (round(p, 6) if p >= 1e-6 else "<1e-6"),
        "mde": round(mde_estimate(diffs), 4),
        "n_positive": sum(1 for x in diffs if x > 0),
    }


def _selftest():
    # strong positive effect -> p < 0.05
    pos = [0.5 + 0.3 * (i % 3) for i in range(30)]
    _, p_pos = wilcoxon_signed_rank(pos)
    # random noise around 0 -> p > 0.05
    rng = random.Random(7)
    noise = [rng.gauss(0, 1) for _ in range(30)]
    _, p_noise = wilcoxon_signed_rank(noise)
    s_pos = summarize(pos)
    s_noise = summarize(noise)
    print(f"[stats selftest] positive: p={p_pos:.4f}  median_diff={s_pos['median_diff']:.3f} ci={s_pos['ci95']}")
    print(f"[stats selftest] noise:    p={p_noise:.4f}  median_diff={s_noise['median_diff']:.3f} ci={s_noise['ci95']} mde={s_noise['mde']:.3f}")
    assert p_pos < 0.05, "positive effect should be significant"
    assert p_noise > 0.05, "noise should not be significant"
    print("[stats selftest] PASS (positive significant, noise not)")


if __name__ == "__main__":
    _selftest()
