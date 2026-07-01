"""adapters/maze/candidate.py — discrete-compositional strategies + generators.

A candidate is a Strategy: a fixed set of discrete slot choices (no continuous
weights). This is the deliberate contrast with 2048's 5-weight policies —
there, "extrapolation" is an invisible weight nudge; here, "extrapolation"
is a visible recomposition (keep the winning slot, re-roll the others).

Slots:
  explorer  — wall_follow / greedy_dist / flood / random
  dead_end  — backtrack / pivot_turn / random
  junction  — left_hand / right_hand / by_distance
  marking   — none / visited_averse

Two generators:
  generate_pool(round_idx, seed, n)        — memory-INdependent baseline (control).
  generate_pool_aware(memory, round_idx, seed, n, ...) — memory-AWARE evolution.
    Reads memory.successes(universe), finds which slot-values appear in
    winners, and recombines: keep the winning slot values, re-roll the rest.
    This is the "success-family extrapolation" the 2048 domain could not do.

The body string canonicalizes slot choices so the DeadEndDetector's
already-tested check matches reliably.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

# Slot vocabularies — discrete, finite. Each value is a real behavior in env.py.
EXPLORERS = ("wall_follow", "greedy_dist", "flood", "random")
DEAD_ENDS = ("backtrack", "pivot_turn", "random")
JUNCTIONS = ("left_hand", "right_hand", "by_distance")
MARKINGS = ("none", "visited_averse")

SLOTS = ("explorer", "dead_end", "junction", "marking")


@dataclass(frozen=True)
class Strategy:
    """One search candidate: a discrete-compositional maze policy."""
    explorer: str
    dead_end: str
    junction: str
    marking: str
    body: str
    # parent_body: which successful strategy this was extrapolated from, if any
    # (empty for baseline/randomly-generated). Used to build the lineage tree.
    parent_body: str = ""
    # which slots were inherited from the parent vs re-rolled (provenance)
    inherited: tuple = ()

    @property
    def family(self) -> str:
        """Factor 2 family = the explorer heuristic (the dominant strategy axis)."""
        return self.explorer

    def as_dict(self) -> dict:
        return {k: getattr(self, k) for k in SLOTS}

    def to_json(self) -> dict:
        return {
            "body": self.body,
            "explorer": self.explorer,
            "dead_end": self.dead_end,
            "junction": self.junction,
            "marking": self.marking,
            "family": self.family,
            "parent_body": self.parent_body,
            "inherited": list(self.inherited),
        }


def make_strategy(explorer: str, dead_end: str, junction: str, marking: str,
                  parent_body: str = "", inherited: tuple = ()) -> Strategy:
    body = f"explorer={explorer},dead_end={dead_end},junction={junction},marking={marking}"
    return Strategy(explorer, dead_end, junction, marking, body, parent_body, inherited)


# --- baseline generator (memory-independent; the control group uses this) ---

def _random_strategy(rng: random.Random, parent_body: str = "") -> Strategy:
    return make_strategy(
        explorer=rng.choice(EXPLORERS),
        dead_end=rng.choice(DEAD_ENDS),
        junction=rng.choice(JUNCTIONS),
        marking=rng.choice(MARKINGS),
        parent_body=parent_body,
    )


def generate_pool(round_idx: int, seed: int, n: int = 12) -> list:
    """Deterministic, memory-INdependent candidate pool for one round.

    Mixes every family archetype + pure randoms so each round yields both
    hits and misses. Deterministic for (round_idx, seed). NEVER reads Memory —
    this is what keeps 'generator learning' out of the control group, so any
    cross-round improvement in the control is attributable to scoring/blocking
    (Factor 2/3), not generation.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97))
    pool: list = []
    # seed one of each explorer family so every family is represented
    for ex in EXPLORERS:
        pool.append(make_strategy(
            explorer=ex,
            dead_end=rng.choice(DEAD_ENDS),
            junction=rng.choice(JUNCTIONS),
            marking=rng.choice(MARKINGS),
        ))
    # fill the rest with randoms
    for _ in range(max(0, n - len(EXPLORERS))):
        pool.append(_random_strategy(rng))
    rng.shuffle(pool)
    return pool


# --- memory-AWARE generator (the evolution mechanism; the treatment group) ---

def _slot_vote(winners: list, slot: str) -> dict:
    """Count how often each slot-value appears among winning strategies."""
    counts: dict = {}
    for w in winners:
        v = getattr(w, slot, None)
        if v is None:
            # w may be a raw Strategy or an Attempt carrying the strategy
            body = getattr(w, "body", "")
            v = _body_slot(body, slot)
        if v:
            counts[v] = counts.get(v, 0) + 1
    return counts


def _body_slot(body: str, slot: str) -> str:
    """Best-effort parse of one slot value from a body string."""
    key = slot + "="
    for part in str(body).split(","):
        part = part.strip()
        if part.startswith(key):
            return part[len(key):]
    return ""


def generate_pool_aware(
    memory,
    round_idx: int,
    seed: int,
    universe: str,
    n: int = 12,
    explore_ratio: float = 0.25,
) -> list:
    """Memory-AWARE evolution generator — learns FRUGAL success.

    Under the resource-constraint metric (cost = step_ratio + α·compute), not
    all successes are equal: greedy_dist (cost~1.0) is a cheap success, while
    wall_follow (cost~2.2) is an expensive success. This generator extrapolates
    from the CHEAPEST past successes — recovering each attempt's cost bucket
    from the `cost:N` evidence_kind tag the adapter stamps on.

    What it does that generate_pool cannot:
      1. Reads memory.attempts(universe), recovers each one's cost from the
         `cost:N` tag, and ranks by cost (ascending = cheaper is better).
      2. Votes per slot over the LOW-cost winners, then extrapolates children
         that inherit the frugal family's slot values.
      3. Keeps an explore_ratio of pure-random strategies (Factor 5 novelty).

    Round 0 (no positive clues) falls back to a baseline pool.
    """
    rng = random.Random((seed * 1_000_003) ^ (round_idx * 97) ^ 0x5EA9)  # 'MAZE'
    attempts = memory.attempts(universe) if memory is not None else []
    if not attempts:
        return generate_pool(round_idx, seed, n)

    # recover cost from the bucketed `cost:N` evidence_kind; keep winners (reached)
    # ranked by cost ascending — cheaper success is a better evolutionary clue.
    clues = []  # (cost_bucket_int, attempt)
    for a in attempts:
        cost_bucket = 999
        for k in (a.evidence_kinds or set()):
            if isinstance(k, str) and k.startswith("cost:"):
                try:
                    cost_bucket = int(k.split(":")[1])
                except ValueError:
                    pass
        if a.success or a.weak:  # any arrival is a clue (success=cheap, weak=pricey)
            clues.append((cost_bucket, a))

    if not clues:
        return generate_pool(round_idx, seed, n)

    # rank clues by cost ascending; take the cheapest distinct bodies as roots
    clues.sort(key=lambda t: t[0])
    seen = set()
    winners = []
    for _, a in clues:
        if a.body not in seen:
            seen.add(a.body); winners.append(a)
        if len(winners) >= 6:
            break

    pool: list = []
    n_extrapolate = max(1, int(round(n * (1.0 - explore_ratio))))
    n_explore = n - n_extrapolate

    # weight parent selection toward cheaper winners (the frugal family)
    weights = [1.0 / (i + 1) for i in range(len(winners))]  # cheapest = heaviest

    for _ in range(n_extrapolate):
        parent = rng.choices(winners, weights=weights, k=1)[0]
        parent_body = getattr(parent, "body", "")
        inherited_slots = []
        slots_chosen = {}
        for slot, vocab in (("explorer", EXPLORERS), ("dead_end", DEAD_ENDS),
                            ("junction", JUNCTIONS), ("marking", MARKINGS)):
            votes = _slot_vote(winners, slot)
            if votes and rng.random() < 0.7:
                best = max(votes, key=votes.get)
                slots_chosen[slot] = best
                inherited_slots.append(slot)
            else:
                slots_chosen[slot] = rng.choice(vocab)
        child = make_strategy(
            explorer=slots_chosen["explorer"],
            dead_end=slots_chosen["dead_end"],
            junction=slots_chosen["junction"],
            marking=slots_chosen["marking"],
            parent_body=parent_body,
            inherited=tuple(inherited_slots),
        )
        pool.append(child)

    # --- exploration: pure-random novelty (Factor 5) ---
    for _ in range(n_explore):
        pool.append(_random_strategy(rng))

    rng.shuffle(pool)
    return pool


def _selftest():
    """Sanity: baseline pool shape + aware generator lineage on a fake memory."""
    pool = generate_pool(round_idx=0, seed=1, n=12)
    print(f"[baseline] {len(pool)} strategies, families=",
          {s.family for s in pool})
    # simulate a memory with one success
    from core.memory import Memory, Attempt
    mem = Memory()
    winner = make_strategy("flood", "backtrack", "by_distance", "visited_averse")
    mem.record(Attempt(body=winner.body, universe="8x8", success=True,
                       family="flood", features=[], motif="",
                       evidence_kinds=set()))
    aware = generate_pool_aware(mem, round_idx=1, seed=1, universe="8x8", n=12)
    inherited = [s for s in aware if s.parent_body]
    print(f"[aware] {len(aware)} strategies, {len(inherited)} extrapolated from winner")
    # show one child's lineage
    for s in inherited[:3]:
        print(f"  child explorer={s.explorer} (inherited={s.inherited}) "
              f"parent={s.parent_body[:40]}...")


if __name__ == "__main__":
    _selftest()
