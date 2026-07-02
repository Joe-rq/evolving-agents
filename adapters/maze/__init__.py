"""maze adapter — a public domain for the evolving-agents engine.

Unlike 2048 (continuous weights, binary success), maze strategies are
discrete-compositional (slot combinations) and success is efficiency-graded.
This is what makes *generation* learnable: extrapolation = visible
recomposition around winning slots, not an invisible weight nudge.

See adapter.py (5 protocols + RuleSpecs), env.py (maze + stepper),
candidate.py (baseline + memory-aware generators).
"""
from adapters.maze.adapter import MazeAdapter, MAZE_RULE_SPECS, make_execute
from adapters.maze.candidate import (
    Strategy, make_strategy, generate_pool, generate_pool_aware,
    EXPLORERS, DEAD_ENDS, JUNCTIONS, MARKINGS,
)

__all__ = [
    "MazeAdapter",
    "MAZE_RULE_SPECS",
    "make_execute",
    "Strategy",
    "make_strategy",
    "generate_pool",
    "generate_pool_aware",
    "EXPLORERS",
    "DEAD_ENDS",
    "JUNCTIONS",
    "MARKINGS",
]
