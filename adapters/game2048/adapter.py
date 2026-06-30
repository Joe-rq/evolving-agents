"""adapters/game2048/adapter.py — the 5 evolving-agents protocols over 2048 policies.

Mirrors the structure of the private reference adapter (RuleSpec list + evidence_kinds
projection + classify/motif_of mapping + make_execute) but with entirely new
domain content — zero quantitative IP bleed. A candidate is a Policy (see
candidate.py); execute() plays K games via env.play().

Factor 4 note (honest): in the quantitative host, Factor 4 manifested as a
universe switch (TOP3000->TOP1000, "switch ponds"). In 2048 a larger board is
*easier* (more space -> higher max tile), so "switch ponds to revive a dead
strategy" does NOT occur here — we do not claim it. Factor 4 in 2048 is the
Evolver's pivot *recommendation* (families struck + motifs failing repeatedly),
which is the same mechanism observed through a different lens.
"""
from __future__ import annotations

from core.protocols import DeadEndContext
from core.rules import RuleSpec
from adapters.game2048.candidate import Policy, WEIGHT_KEYS
from adapters.game2048.env import play


# Domain-defined projection rules (Factor 1/3 audit). Each fires when a motif
# accumulates >= min_evidence attempts tagged with the given evidence_kind.
GAME2048_RULE_SPECS: list = [
    RuleSpec("unanchored_mono", "corner_lost", 2, "penalize", -0.40,
             "mono-heavy with no corner anchor drifts and loses the max tile"),
    RuleSpec("unanchored_mono", "early_death", 3, "block", -1.00,
             "snake-class repeatedly stalls early"),
    RuleSpec("aggressive_merge", "early_death", 2, "penalize", -0.40,
             "merge-heavy policy collapses board structure"),
    RuleSpec("shallow_random", "weak", 3, "block", -1.00,
             "no-lookahead uniform policy unrecoverable", True),
]


def _weight_map(candidate) -> dict:
    if hasattr(candidate, "weight_map"):
        return candidate.weight_map
    return _parse_body(getattr(candidate, "body", str(candidate)))


def _parse_body(body: str) -> dict:
    """Best-effort parse of a body string into a weight map (depth unused here)."""
    w = {k: 0.2 for k in WEIGHT_KEYS}
    for part in str(body).split(","):
        if "=" in part:
            k, v = part.split("=", 1)
            k = k.strip()
            if k in w:
                try:
                    w[k] = float(v)
                except ValueError:
                    pass
    return w


class Game2048Adapter:
    """Implements the 5 evolving-agents protocols over 2048 Policy candidates."""

    def classify(self, candidate) -> str:
        """Factor 2 — map a policy to its strategy family."""
        w = _weight_map(candidate)
        depth = getattr(candidate, "depth", 0)
        top_key = max(w, key=w.get)
        if w[top_key] >= 0.5:
            return "snake" if top_key == "mono" else top_key
        if (max(w.values()) - min(w.values())) < 0.12 and depth == 0:
            return "random"
        return "balanced"

    def extract(self, candidate) -> list:
        """Factor 1/5 — comparable feature tokens for novelty + memory keying."""
        w = _weight_map(candidate)
        depth = getattr(candidate, "depth", 0)

        def bucket(v):
            return "hi" if v >= 0.40 else ("lo" if v < 0.15 else "mid")

        feats = [f"fam:{self.classify(candidate)}", f"depth:{depth}"]
        feats += [f"{k}:{bucket(w[k])}" for k in WEIGHT_KEYS]
        return feats

    def motif_of(self, candidate) -> str:
        """Factor 3 — predicted failure motif (a class that tends to fail together).

        Operates at scoring time (outcome unknown), so it reads the policy's
        risk structure, not the result."""
        w = _weight_map(candidate)
        depth = getattr(candidate, "depth", 0)
        if w["mono"] >= 0.40 and w["corner"] < 0.20:
            return "unanchored_mono"
        if w["merge"] >= 0.40 and w["smooth"] < 0.20:
            return "aggressive_merge"
        if max(w.values()) < 0.30 and depth == 0:
            return "shallow_random"
        return ""

    def dead_end_reason(self, candidate, context: DeadEndContext) -> str:
        """Factor 1 — block already-tested policies (exact body match)."""
        body = getattr(candidate, "body", str(candidate))
        if body in context.tested_bodies:
            return "already_tested"
        return ""

    def is_success(self, result) -> bool:
        return bool(result.get("success", False)) if isinstance(result, dict) else False

    def is_weak(self, result) -> bool:
        return bool(result.get("weak", False)) if isinstance(result, dict) else False


def _terminal_evidence(games, size):
    """Project terminal boards into evidence_kinds tags for rule projection."""
    kinds = set()
    for g in games:
        board = g["final_board"]
        empties = sum(1 for row in board for v in row if v == 0)
        if empties == 0:
            kinds.add("filled_board")
        mx = max(max(row) for row in board)
        if mx > 0 and board[0][0] != mx:
            kinds.add("corner_lost")
        if g["moves"] < 80:
            kinds.add("early_death")
        if 512 <= g["max_tile"] < 1024:
            kinds.add("weak")
    return kinds


def make_execute(size: int, K: int, seed_fn, success_tile: int = 1024, weak_tile: int = 512):
    """Build the deterministic execute() callback the engine calls.

    seed_fn(body) -> int must be deterministic and identical for both groups
    on the same (body, round), so amnesic vs full face the same K board traces.
    """
    def execute(candidate):
        w = _weight_map(candidate)
        depth = getattr(candidate, "depth", 0)
        base = seed_fn(getattr(candidate, "body", str(candidate)))
        games = [play(w, depth, size, base + i) for i in range(K)]
        max_tile = max(g["max_tile"] for g in games)
        return {
            "success": max_tile >= success_tile,
            "weak": weak_tile <= max_tile < success_tile,
            "evidence_kinds": _terminal_evidence(games, size),
            "max_tile": max_tile,
            "score": sum(g["score"] for g in games) / K,
        }
    return execute
