"""adapters/game2048/env.py — minimal 2048 environment (stdlib only).

A tiny, dependency-free 2048 board + an expectimax player parameterized by a
policy (5 heuristic weights + lookahead depth). The ablation runner wraps
`play()` as the deterministic execute() callback: same (weights, depth, size,
seed) -> identical trajectory, so the amnesic and full groups face the exact
same boards and the only varying factor is the Memory ledger.

No external libs — keeps the ablation reproducible and the demo portable.
"""
from __future__ import annotations

import random

LEFT, RIGHT, UP, DOWN = 0, 1, 2, 3
DIRECTIONS = (LEFT, RIGHT, UP, DOWN)


def _log2(x: int) -> int:
    """Exact log2 for powers of two (all 2048 tiles are powers of two)."""
    return x.bit_length() - 1


def _slide_row_left(row):
    """Slide+merge one row to the left. Returns (new_row, score_gained)."""
    nz = [x for x in row if x != 0]
    out, score, i = [], 0, 0
    while i < len(nz):
        if i + 1 < len(nz) and nz[i] == nz[i + 1]:
            out.append(nz[i] * 2); score += nz[i] * 2; i += 2
        else:
            out.append(nz[i]); i += 1
    out += [0] * (len(row) - len(out))
    return out, score


def _slide_left_board(board):
    rows, total = [], 0
    for row in board:
        nr, s = _slide_row_left(row)
        rows.append(nr); total += s
    return rows, total


def _rev_rows(b):
    return [r[::-1] for r in b]


def _trans(b):
    return [list(col) for col in zip(*b)]


def apply_move(board, direction):
    """Return (new_board, score_gained, changed). Never mutates `board`.

    All four directions are reduced to a left-slide via reversible transforms:
      LEFT  = identity
      RIGHT = reverse each row (self-inverse)
      UP    = transpose (self-inverse)
      DOWN  = transpose -> reverse each row -> slide -> reverse -> transpose
    """
    if direction == LEFT:
        nb, s = _slide_left_board([r[:] for r in board])
    elif direction == RIGHT:
        nb, s = _slide_left_board(_rev_rows(board)); nb = _rev_rows(nb)
    elif direction == UP:
        nb, s = _slide_left_board(_trans(board)); nb = _trans(nb)
    elif direction == DOWN:
        nb, s = _slide_left_board(_rev_rows(_trans(board))); nb = _trans(_rev_rows(nb))
    else:
        raise ValueError(direction)
    return nb, s, nb != board


class Game2048:
    def __init__(self, size: int = 4, seed=None) -> None:
        self.size = size
        self.rng = random.Random(seed)
        self.board = [[0] * size for _ in range(size)]
        self.score = 0
        self._spawn(); self._spawn()

    def _empty(self):
        return [(r, c) for r in range(self.size) for c in range(self.size) if self.board[r][c] == 0]

    def _spawn(self) -> bool:
        cells = self._empty()
        if not cells:
            return False
        r, c = self.rng.choice(cells)
        self.board[r][c] = 4 if self.rng.random() < 0.1 else 2
        return True

    def move(self, direction: int) -> bool:
        nb, s, changed = apply_move(self.board, direction)
        if changed:
            self.board = nb; self.score += s; self._spawn()
        return changed

    def legal_moves(self) -> list[int]:
        return [d for d in DIRECTIONS if apply_move(self.board, d)[2]]

    def is_game_over(self) -> bool:
        return not self.legal_moves()

    def max_tile(self) -> int:
        return max(max(row) for row in self.board)


# --- heuristic features (each normalized to [0,1] so weights compose cleanly) ---

def heuristic_features(board, size):
    """Five normalized sub-scores. A policy weights these to evaluate a board.

    corner          — is the max tile anchored at (0,0)? (the classic 2048 aim)
    monotonicity    — fraction of adjacent pairs that are non-increasing
    smoothness      — 1 - normalized mean log2 gap between nonzero neighbors
    space           — fraction of empty cells
    merge           — fraction of adjacent equal nonzero pairs (mergeable now)
    """
    max_tile = 0
    empties = 0
    for r in range(size):
        for c in range(size):
            v = board[r][c]
            if v > max_tile:
                max_tile = v
            if v == 0:
                empties += 1
    corner = 1.0 if (max_tile > 0 and board[0][0] == max_tile) else 0.0
    space = empties / (size * size)

    mono_n = mono_ok = merge_n = merge_ok = 0
    diffs = []
    for r in range(size):
        for c in range(size - 1):
            a, b = board[r][c], board[r][c + 1]
            mono_n += 1; merge_n += 1
            if a >= b: mono_ok += 1
            if a != 0 and a == b: merge_ok += 1
            if a and b: diffs.append(abs(_log2(a) - _log2(b)))
    for c in range(size):
        for r in range(size - 1):
            a, b = board[r][c], board[r + 1][c]
            mono_n += 1; merge_n += 1
            if a >= b: mono_ok += 1
            if a != 0 and a == b: merge_ok += 1
            if a and b: diffs.append(abs(_log2(a) - _log2(b)))
    monotonicity = mono_ok / mono_n if mono_n else 0.0
    merge_potential = merge_ok / merge_n if merge_n else 0.0
    mean_diff = sum(diffs) / len(diffs) if diffs else 0.0
    smoothness = max(0.0, 1.0 - mean_diff / (size + 1))
    return {
        "corner": corner,
        "monotonicity": monotonicity,
        "smoothness": smoothness,
        "space": space,
        "merge": merge_potential,
    }


def evaluate(board, size, weights):
    """Weighted sum of the five heuristic features."""
    f = heuristic_features(board, size)
    return (
        weights["corner"] * f["corner"]
        + weights["mono"] * f["monotonicity"]
        + weights["smooth"] * f["smoothness"]
        + weights["space"] * f["space"]
        + weights["merge"] * f["merge"]
    )


def _chance_value(board, size, weights, depth):
    """Expected evaluation over all empty cells spawning a 2 (deterministic)."""
    empties = [(r, c) for r in range(size) for c in range(size) if board[r][c] == 0]
    if not empties:
        return evaluate(board, size, weights)
    total = 0.0
    for (r, c) in empties:
        b2 = [row[:] for row in board]
        b2[r][c] = 2
        if depth <= 0:
            total += evaluate(b2, size, weights)
        else:
            best = None
            for d in DIRECTIONS:
                nb, _, ch = apply_move(b2, d)
                if not ch:
                    continue
                v = _chance_value(nb, size, weights, depth - 1)
                if best is None or v > best:
                    best = v
            total += best if best is not None else evaluate(b2, size, weights)
    return total / len(empties)


def choose_move(board, size, weights, depth):
    """Best direction, or None if no legal move. Deterministic given inputs.

    depth=0 is greedy (evaluate immediate post-move board); depth=1 averages
    over spawn positions then re-optimizes — a 1-ply expectimax.
    """
    best_dir, best_val = None, None
    for d in DIRECTIONS:
        nb, _, changed = apply_move(board, d)
        if not changed:
            continue
        val = evaluate(nb, size, weights) if depth <= 0 else _chance_value(nb, size, weights, depth - 1)
        if best_val is None or val > best_val:
            best_val, best_dir = val, d
    return best_dir


def play(weights, depth, size, seed, max_moves=2000):
    """Run one full game with the given policy. Deterministic for fixed seed.

    Returns terminal stats + the final board (for failure-motif evidence).
    """
    game = Game2048(size=size, seed=seed)
    moves = 0
    while moves < max_moves:
        d = choose_move(game.board, size, weights, depth)
        if d is None:
            break
        game.move(d)
        moves += 1
    return {
        "max_tile": game.max_tile(),
        "score": game.score,
        "moves": moves,
        "final_board": [row[:] for row in game.board],
    }


def _selftest(n=100, size=4, seed0=0):
    rng = random.Random(12345)
    vals = []
    for i in range(n):
        w = [rng.random() for _ in range(5)]
        s = sum(w) if sum(w) else 1.0
        weights = {"corner": w[0] / s, "mono": w[1] / s, "smooth": w[2] / s,
                   "space": w[3] / s, "merge": w[4] / s}
        vals.append(play(weights, depth=0, size=size, seed=seed0 + i)["max_tile"])
    mean = sum(vals) / len(vals)
    print(f"[env selftest] {n} games | size={size} depth=0 random-weights")
    print(f"  max_tile mean={mean:.1f} min={min(vals)} max={max(vals)}")
    print(f"  >=256: {sum(1 for v in vals if v >= 256)}/{n}  >=512: {sum(1 for v in vals if v >= 512)}/{n}")


if __name__ == "__main__":
    _selftest()
