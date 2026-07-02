"""adapters/maze/adapter.py — the 5 evolving-agents protocols over maze strategies.

Mirrors the structure of the 2048 adapter (RuleSpec list + evidence_kinds
projection + classify/motif_of mapping + make_execute) but over an entirely
new domain: discrete-compositional maze policies instead of weighted boards.

Success criterion (the key design choice): unlike 2048 where success = "reach
1024 tile" (binary), maze success is EFFICIITY-graded:
  success = reached the goal in <= K2×optimal steps        (efficient)
  weak    = reached but in K2×optimal < steps <= K3×optimal (inefficient but arrived)
  fail    = stuck, or took > K3×optimal                    (dead or thrashing)

This grading is what makes evolution VISIBLE: the optimizer has somewhere to
climb (fail→weak→success by improving efficiency), whereas 2048's binary gate
left no gradient once 'success' was reached.
"""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.maze.candidate import (
    Strategy, EXPLORERS, DEAD_ENDS, JUNCTIONS, MARKINGS,
    generate_pool, generate_pool_aware,
)
from adapters.maze.env import play, generate_maze, terminal_evidence


# Domain-defined projection rules (Factor 1/3 audit).
# Motifs (from motif_of) × evidence_kinds (from terminal_evidence) → Rule.
MAZE_RULE_SPECS: list = [
    RuleSpec("loop_prone", "looped", 3, "penalize", -0.35,
             "this config tends to oscillate and revisit cells"),
    RuleSpec("loop_prone", "high_revisit", 2, "block", -1.00,
             "random/poor explorer with backtrack repeatedly thrashes"),
    RuleSpec("deadlock_prone", "dead_end_stuck", 3, "penalize", -0.40,
             "this config gets stuck without reaching the goal"),
    RuleSpec("thrash_prone", "weak", 3, "penalize", -0.30,
             "reaches the goal but extremely inefficiently"),
]


def _strat_dict(candidate) -> dict:
    if hasattr(candidate, "as_dict"):
        return candidate.as_dict()
    # fall back to body parsing
    return _parse_body(getattr(candidate, "body", str(candidate)))


def _parse_body(body: str) -> dict:
    w = {k: "?" for k in ("explorer", "dead_end", "junction", "marking")}
    for part in str(body).split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            if k in w:
                w[k] = v.strip()
    return w


class MazeAdapter:
    """Implements the 5 evolving-agents protocols over maze Strategy candidates."""

    def classify(self, candidate) -> str:
        """Factor 2 — family = the explorer heuristic (dominant strategy axis)."""
        return getattr(candidate, "family", None) or _strat_dict(candidate).get("explorer", "unknown")

    def extract(self, candidate) -> list:
        """Factor 1/5 — feature tokens for novelty + memory keying."""
        d = _strat_dict(candidate)
        return [f"fam:{self.classify(candidate)}",
                f"de:{d.get('dead_end', '?')}",
                f"jn:{d.get('junction', '?')}",
                f"mk:{d.get('marking', '?')}"]

    def motif_of(self, candidate) -> str:
        """Factor 3 — predicted failure motif (class that tends to fail together).

        Reads the strategy's risk structure at scoring time (outcome unknown).
        Combinations known to misbehave get a motif so the engine can penalize
        the whole class after enough evidence, not just one instance.
        """
        d = _strat_dict(candidate)
        ex = d.get("explorer", "")
        de = d.get("dead_end", "")
        mk = d.get("marking", "")
        # random explorer + backtrack → oscillation trap
        if ex == "random" and de == "backtrack":
            return "loop_prone"
        # no marking + random/poor explorer → likely stuck thrashing
        if ex in ("random",) and mk == "none":
            return "thrash_prone"
        # greedy_dist + pivot_turn at dead ends → can deadlock (turns into wall)
        if ex == "greedy_dist" and de == "pivot_turn":
            return "deadlock_prone"
        return ""

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        """Factor 1 — block already-tested strategies (exact body match)."""
        body = getattr(candidate, "body", str(candidate))
        if body in context.tested_bodies:
            return "already_tested"
        return ""

    def is_success(self, result) -> bool:
        return bool(result.get("success", False)) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak", False)) if isinstance(result, dict) else False


def _outcome_from_result(result: dict, alpha: float = 1.0) -> dict:
    """Classify a play result by TOTAL COST (the resource-constraint metric).

    cost = step_ratio + alpha * compute_ratio
      step_ratio   = steps / optimal           (1.0 = optimal path)
      compute_ratio = total_compute / (optimal * n_cells)  (1.0 = flood-level)

    This is the key redesign. The old efficiency-only metric let flood dominate
    (it's always step-optimal). Adding the compute dimension means flood's
    O(n²)-per-step BFS makes it EXPENSIVE — greedy_dist (step~1x, compute~0)
    beats it on total cost. Success bands on cost create a real gradient:
      success: cost <= COST_SUCC (1.5)   — frugal AND accurate
      weak:    COST_SUCC < cost <= COST_WEAK (2.5) — arrived but costly
      fail:    cost > COST_WEAK or stuck
    """
    optimal = result.get("optimal", 0) or 1
    steps = result.get("steps", 0)
    reached = result.get("reached", False)
    total_compute = result.get("total_compute", 0)
    n_cells = result.get("n_cells", 1) or 1
    step_ratio = steps / optimal if reached else 99.0
    compute_ratio = total_compute / (optimal * n_cells) if reached else 99.0
    cost = step_ratio + alpha * compute_ratio
    COST_SUCC = 1.5
    COST_WEAK = 2.5
    if reached and cost <= COST_SUCC:
        return {"success": True, "weak": False, "cost": cost}
    if reached and cost <= COST_WEAK:
        return {"success": False, "weak": True, "cost": cost}
    return {"success": False, "weak": False, "cost": cost if reached else 99.0}


def make_execute(size: int = 8, K: int = 3, seed_fn=None,
                 max_steps: int = 0, alpha: float = 1.0):
    """Build the deterministic execute() callback the engine calls.

    Runs the strategy on K different mazes (deterministic seeds via seed_fn)
    and aggregates by TOTAL COST (step_ratio + alpha·compute_ratio). This is
    the resource-constraint metric: flood is accurate but compute-heavy, so a
    frugal-yet-accurate family (greedy_dist) wins on cost. Success/weak/fail
    bands on cost create the gradient that pure efficiency could not.

    seed_fn(body, round_idx, replicate) must be deterministic so any control
    group faces the same mazes.
    """
    if max_steps <= 0:
        max_steps = size * size * 25

    def execute(candidate, round_idx: int = 0, replicate: int = 0):
        d = _strat_dict(candidate)
        body = getattr(candidate, "body", str(candidate))
        base = seed_fn(body, round_idx, replicate) if seed_fn else 0
        results = []
        for i in range(K):
            m = generate_maze(seed=base + i, size=size)
            res = play(d, m, seed=base + i, max_steps=max_steps)
            results.append((m, res))
        succ = weak = 0
        kinds = set()
        costs_reached = []  # collect cost of every reached game (for averaging)
        for m, res in results:
            band = _outcome_from_result(res, alpha=alpha)
            if band["success"]:
                succ += 1
            elif band["weak"]:
                weak += 1
            kinds |= terminal_evidence(res, m)
            if res["reached"]:
                costs_reached.append(band["cost"])
        majority = (succ + weak) > K / 2.0
        # MEAN cost across reached games — not best. This rewards STABLE good
        # performance, not occasional lucky runs (which is what in-context
        # learning looks like, and what we want to distinguish from evolution).
        mean_cost = sum(costs_reached) / len(costs_reached) if costs_reached else 99.0
        # encode cost as a bucketed evidence_kind so the memory-aware generator
        # can recover "how frugal was each past attempt" and extrapolate toward
        # low-cost families — same pattern as symreg's r2:N tag.
        cost_bucket = f"cost:{int(mean_cost * 10)}"  # cost:10 = cost~1.0 (optimal)
        kinds.add(cost_bucket)
        return {
            "success": majority and succ >= max(1, weak),
            "weak": majority and succ < max(1, weak),
            "evidence_kinds": kinds,
            "reached_ratio": (succ + weak) / K,
            "mean_cost": round(mean_cost, 3),
            "best_cost": round(min(costs_reached) if costs_reached else 99.0, 3),
            "best_efficiency": 0.0,  # kept for backward-compat; cost is the real metric now
            "K": K,
        }

    return execute


def _selftest():
    """Quick: a known-good and a known-bad strategy, verify outcome bands."""
    from adapters.maze.candidate import make_strategy
    good = make_strategy("flood", "backtrack", "by_distance", "visited_averse")
    bad = make_strategy("random", "random", "left_hand", "none")
    exe = make_execute(size=8, K=5, seed_fn=lambda b, r, rep: hash(b) % 1000 + r)
    for name, s in [("flood+backtrack (good)", good), ("random (bad)", bad)]:
        out = exe(s)
        print(f"{name}: success={out['success']} weak={out['weak']} "
              f"reached_ratio={out['reached_ratio']} best_eff={out['best_efficiency']} "
              f"kinds={out['evidence_kinds']}")


if __name__ == "__main__":
    _selftest()
