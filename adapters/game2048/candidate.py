"""adapters/game2048/candidate.py — parameterized policies + memory-independent generator.

A candidate is a Policy: 5 normalized heuristic weights (corner/mono/smooth/
space/merge) + a lookahead depth. The body string canonicalizes weights to 2
decimals so DeadEndDetector's already-tested check matches reliably
(0.80 == 0.80, never a stray "0.8" that bypasses Factor 1).

The generator is deliberately **memory-independent** — it never reads the
Memory ledger, so 'engine learning' and 'generator learning' cannot confound
the amnesic-vs-full ablation. It mixes three strata (experts / anti-patterns /
Dirichlet randoms) so every family yields both hits and misses; without that,
family-level scoring is degenerate and the ablation collapses to a trivial null.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

WEIGHT_KEYS = ("corner", "mono", "smooth", "space", "merge")


@dataclass(frozen=True)
class Policy:
    """One search candidate: a weighted heuristic + lookahead depth."""
    weights: tuple  # (corner, mono, smooth, space, merge), each rounded to 2dp
    depth: int
    body: str

    @property
    def weight_map(self) -> dict:
        return dict(zip(WEIGHT_KEYS, self.weights))


def _normalize(ws):
    s = sum(ws) or 1.0
    return tuple(round(w / s, 2) for w in ws)


def make_policy(corner: float, mono: float, smooth: float, space: float, merge: float, depth: int) -> Policy:
    ws = _normalize([corner, mono, smooth, space, merge])
    body = "corner={:.2f},mono={:.2f},smooth={:.2f},space={:.2f},merge={:.2f},depth={}".format(
        ws[0], ws[1], ws[2], ws[3], ws[4], depth
    )
    return Policy(weights=ws, depth=depth, body=body)


def generate_pool(round_idx: int, seed: int, n: int = 15) -> list:
    """Deterministic memory-independent candidate pool for one round.

    Six fixed family archetypes (3 high-yield experts, 3 low-yield
    anti-patterns) plus n-6 Dirichlet randoms. Each archetype is jittered per
    round so its body is unique across rounds — this prevents Factor 1's
    exact-match block from trivially dominating and forces the ablation to
    measure *family/motif guidance* (Factor 2/3), not mere dedup of identical
    bodies. The jitter is small enough to preserve each archetype's family
    classification (e.g. corner base 0.80 stays the dominant weight).

    Deterministic for (round_idx, seed). Never touches Memory.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))

    def jit(base: float, spread: float = 0.06) -> float:
        return max(0.0, base + rng.uniform(-spread, spread))

    pool = [
        make_policy(jit(0.80), jit(0.05), jit(0.05), jit(0.05), jit(0.05), 0),  # corner
        make_policy(jit(0.05), jit(0.05), jit(0.05), jit(0.80), jit(0.05), 0),  # space
        make_policy(jit(0.45), jit(0.10), jit(0.10), jit(0.25), jit(0.10), 0),  # corner+space hybrid
        make_policy(jit(0.10), jit(0.60), jit(0.10), jit(0.10), jit(0.10), 0),  # snake (anti)
        make_policy(jit(0.10), jit(0.10), jit(0.10), jit(0.10), jit(0.60), 0),  # merge (anti)
        make_policy(jit(0.20), jit(0.20), jit(0.20), jit(0.20), jit(0.20), 0),  # shallow (anti)
    ]
    # depth 0 (greedy eval) across the board: family signal is preserved at
    # depth 0 (corner/space reach 1024 in ~11/30 games; snake/merge ~0/30) and
    # dropping depth=1 expectimax cuts per-game cost ~10x (100ms -> 10ms).
    for _ in range(max(0, n - 6)):
        raw = [rng.gammavariate(2.0, 1.0) for _ in range(5)]
        pool.append(make_policy(*raw, 0))
    rng.shuffle(pool)
    return pool
