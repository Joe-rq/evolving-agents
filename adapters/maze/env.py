"""adapters/maze/env.py — minimal grid maze (stdlib only).

A dependency-free maze environment + a stepper parameterized by a *discrete
compositional* strategy (not continuous weights). The ablation/evolution
runner wraps `play()` as the deterministic execute() callback.

Why discrete: 2048's strategies are 5 continuous weights, so "extrapolation"
is a tiny weight nudge — invisible. Maze strategies are *combinations* of
discrete slot choices, so "extrapolation" is a visible recomposition
(keep the winning slot, re-roll the others). That is the point of this
domain: evolution you can SEE.

A maze is a grid of cells with walls between them. `generate_maze` builds one
deterministically (seeded recursive backtracker). `play` runs a strategy from
start to goal (or until stuck) and returns terminal stats + the path, so the
adapter can project failure-motif evidence.
"""
from __future__ import annotations

import random

# Direction vectors (dr, dc). N/E/S/W.
DIRS = ((-1, 0), (0, 1), (1, 0), (0, -1))


class Maze:
    """A grid maze. Cells are (r, c). Walls stored as a set of frozenset pairs.

    `grid(r, c)` returns the wall set around a cell as a dict of open flags.
    Generation is a seeded recursive backtracker → perfect maze (one path
    between any two cells, no isolated loops).
    """

    def __init__(self, size: int, seed: int) -> None:
        self.size = size
        self.rng = random.Random(seed)
        # walls between adjacent cells; absent = open passage
        self._walls: set[frozenset] = set()
        self._build()
        self.start = (0, 0)
        self.goal = (size - 1, size - 1)

    def _neighbors(self, r, c):
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                yield (nr, nc)

    def _build(self):
        """Recursive backtracker: knock down walls to form a perfect maze."""
        n = self.size
        # start fully walled
        for r in range(n):
            for c in range(n):
                if c + 1 < n:
                    self._walls.add(frozenset(((r, c), (r, c + 1))))
                if r + 1 < n:
                    self._walls.add(frozenset(((r, c), (r + 1, c))))
        visited = {(0, 0)}
        stack = [(0, 0)]
        while stack:
            r, c = stack[-1]
            unvisited = [nb for nb in self._neighbors(r, c) if nb not in visited]
            if not unvisited:
                stack.pop()
                continue
            nxt = self.rng.choice(unvisited)
            self._walls.discard(frozenset(((r, c), nxt)))
            visited.add(nxt)
            stack.append(nxt)

    def open_dirs(self, r, c) -> list[int]:
        """Indices into DIRS that are open (no wall) from (r,c)."""
        out = []
        for i, (dr, dc) in enumerate(DIRS):
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.size and 0 <= nc < self.size:
                if frozenset(((r, c), (nr, nc))) not in self._walls:
                    out.append(i)
        return out

    def cells(self):
        for r in range(self.size):
            for c in range(self.size):
                yield (r, c)


def generate_maze(seed: int, size: int = 8) -> Maze:
    """Deterministic maze for a given seed. Same seed → identical maze."""
    return Maze(size, seed)


# --- heuristic helpers the strategies use ---

def _manhattan(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _bfs_dist(maze: Maze, src, targets: set) -> dict:
    """BFS distance from src to every target cell (multi-source target)."""
    from collections import deque
    if src in targets:
        return {src: 0}
    dist = {src: 0}
    q = deque([src])
    while q:
        cur = q.popleft()
        for i in maze.open_dirs(*cur):
            dr, dc = DIRS[i]
            nb = (cur[0] + dr, cur[1] + dc)
            if nb not in dist:
                dist[nb] = dist[cur] + 1
                q.append(nb)
    return {t: dist[t] for t in targets if t in dist}


def _step(maze: Maze, pos: int, facing: int, strat, visited_count: dict, rng: random.Random):
    """Decide the next move from `pos` given a discrete strategy.

    Returns (new_pos, new_facing, compute_units) or (pos, facing, 0) if stuck.
    compute_units measures the computational cost of THIS step's decision:
      flood explorer does a BFS over the reachable graph each step → O(cells)
      all other heuristics (greedy_dist manhattan, wall_follow, random) → O(1)
    This is the resource dimension that breaks flood's dominance: flood is the
    most ACCURATE but also the most EXPENSIVE per step. Under a total-cost
    metric (steps + α·compute), flood no longer wins unconditionally.
    """
    r, c = pos
    opens = maze.open_dirs(r, c)  # list of open direction indices
    if not opens:
        return pos, facing, 0  # walled in (shouldn't happen in perfect maze at non-goal)
    n_cells = maze.size * maze.size

    # --- dead-end handling: only one way out (and it's where we came from) ---
    if len(opens) == 1:
        action = strat["dead_end"]
        if action == "backtrack":
            only = opens[0]
            return _move(r, c, only), only, 1
        elif action == "pivot_turn":
            only = opens[0]
            return _move(r, c, only), only, 1
        else:  # random
            i = rng.choice(opens)
            return _move(r, c, i), i, 1

    # --- multi-way: it's a junction. Apply the explorer heuristic. ---
    explorer = strat["explorer"]

    # filter out immediate revisits if marking strategy disallows them
    marking = strat["marking"]
    candidates = list(opens)
    if marking == "visited_averse":
        # prefer directions whose target cell has been visited least
        def visit_key(i):
            dr, dc = DIRS[i]
            nb = (r + dr, c + dc)
            return visited_count.get(nb, 0)
        candidates.sort(key=visit_key)
        # keep only the least-visited tier (allow ties)
        if candidates:
            best = visit_key(candidates[0])
            least = [i for i in candidates if visit_key(i) == best]
            candidates = least

    if explorer == "greedy_dist":
        # pick the open direction minimizing manhattan dist to goal — O(1) per step
        goal = maze.goal
        best_i, best_d = None, None
        for i in candidates:
            dr, dc = DIRS[i]
            nb = (r + dr, c + dc)
            d = _manhattan(nb, goal)
            if best_d is None or d < best_d:
                best_d, best_i = d, i
        i = best_i if best_i is not None else rng.choice(opens)
        return _move(r, c, i), i, 1
    elif explorer == "flood":
        # pick the open direction that BFS-measures closest to goal — O(cells) per step.
        # This is the resource cost: flood is the most accurate heuristic but
        # recomputes a full BFS every step. Under total-cost scoring this breaks
        # its dominance — greedy_dist is nearly as accurate at O(1) per step.
        goal = maze.goal
        best_i, best_d = None, None
        for i in candidates:
            dr, dc = DIRS[i]
            nb = (r + dr, c + dc)
            d = _bfs_dist(maze, nb, {goal}).get(goal, 10 ** 9)
            if best_d is None or d < best_d:
                best_d, best_i = d, i
        i = best_i if best_i is not None else rng.choice(opens)
        return _move(r, c, i), i, n_cells
    elif explorer == "wall_follow":
        hand = strat["junction"]  # left_hand or right_hand
        i = _wall_follow_pick(facing, opens, hand, rng)
        return _move(r, c, i), i, 1
    else:  # random
        i = rng.choice(candidates) if candidates else rng.choice(opens)
        return _move(r, c, i), i, 1


def _move(r, c, dir_idx):
    dr, dc = DIRS[dir_idx]
    return (r + dr, c + dc)


def _wall_follow_pick(facing: int, opens: list[int], hand: str, rng: random.Random) -> int:
    """Choose a direction keeping a 'hand' on a wall.

    left_hand: prefer turning left from current facing, then straight, then right.
    right_hand: mirror. Falls back to any open direction. The reverse of the
    current facing is excluded (we came from there) unless nothing else is open.
    """
    reverse = (facing + 2) % 4
    abs_order = [(facing + delta) % 4 for delta in ([1, 0, 3] if hand == "left_hand" else [3, 0, 1])]
    for d in abs_order:
        if d == reverse:
            continue
        if d in opens:
            return d
    # last resort: any open dir (even reverse)
    return rng.choice(opens)


def play(strat, maze: Maze, seed: int, max_steps: int = 4_000) -> dict:
    """Run one strategy attempt on a maze. Deterministic for fixed seed.

    The seed controls ONLY tie-break randomness inside the strategy. The maze
    is fixed by its own seed. Returns terminal stats + path + optimal length
    + total compute units (the resource dimension).
    """
    rng = random.Random(seed)
    pos = maze.start
    facing = 1  # start facing East
    visited_count: dict = {}
    path = [pos]
    visited_count[pos] = 1
    steps = 0
    total_compute = 0  # cumulative computational cost across all steps
    while steps < max_steps:
        if pos == maze.goal:
            break
        prev = pos
        pos, facing, compute = _step(maze, pos, facing, strat, visited_count, rng)
        steps += 1
        total_compute += compute
        visited_count[pos] = visited_count.get(pos, 0) + 1
        path.append(pos)
        if pos == prev and pos != maze.goal:
            break

    reached = (pos == maze.goal)
    optimal = _bfs_dist(maze, maze.start, {maze.goal}).get(maze.goal, 0)
    n_cells = maze.size * maze.size
    # normalize compute: flood-optimal would be optimal_steps × n_cells
    return {
        "reached": reached,
        "steps": steps,
        "optimal": optimal,
        "efficiency": (optimal / steps) if (reached and steps > 0) else 0.0,
        "total_compute": total_compute,
        "compute_per_step": (total_compute / steps) if steps > 0 else 0,
        "n_cells": n_cells,
        "path_len": len(path),
        "final_pos": pos,
        "path": path,
        "visited_counts": visited_count,
    }


def terminal_evidence(result: dict, maze: Maze) -> set:
    """Project a play result into failure-motif evidence tags.

    Analogous to 2048's _terminal_evidence. Tags used by MAZE_RULE_SPECS:
      looped        — visited some cell >= 4 times (oscillating)
      dead_end_stuck — ended not at goal AND last few moves revisited cells
      high_revisit  — max visit count >= 6 (severe thrashing)
      weak          — reached goal but took >= 3x the maze's optimal length
    """
    kinds = set()
    if result["reached"]:
        # weak success: very inefficient path
        # estimate optimal via BFS
        opt = _bfs_dist(maze, maze.start, {maze.goal}).get(maze.goal, 1) or 1
        if result["steps"] >= 3 * opt:
            kinds.add("weak")
        return kinds  # success → only a possible 'weak' tag, no failure tags

    vc = result["visited_counts"]
    max_visits = max(vc.values()) if vc else 0
    if max_visits >= 4:
        kinds.add("looped")
    if max_visits >= 6:
        kinds.add("high_revisit")
    if not result["reached"]:
        kinds.add("dead_end_stuck")
    return kinds


def _selftest(n=30, size=8, seed0=0):
    """Sanity: random strategies on fixed mazes, distribution of outcomes."""
    strats = []
    explorers = ["greedy_dist", "flood", "wall_follow", "random"]
    dead_ends = ["backtrack", "pivot_turn", "random"]
    junctions = ["left_hand", "right_hand", "by_distance"]
    markings = ["none", "visited_averse"]
    rng = random.Random(999)
    reached = 0
    for i in range(n):
        s = {
            "explorer": rng.choice(explorers),
            "dead_end": rng.choice(dead_ends),
            "junction": rng.choice(junctions),
            "marking": rng.choice(markings),
        }
        m = generate_maze(seed=seed0 + i, size=size)
        res = play(s, m, seed=seed0 + i, max_steps=2000)
        if res["reached"]:
            reached += 1
        strats.append((s, res))
    print(f"[env selftest] {n} random strats | size={size}")
    print(f"  reached: {reached}/{n}")
    steps_reached = [r["steps"] for _, r in strats if r["reached"]]
    if steps_reached:
        print(f"  steps (reached): min={min(steps_reached)} "
              f"mean={sum(steps_reached)//len(steps_reached)} max={max(steps_reached)}")


if __name__ == "__main__":
    _selftest()
