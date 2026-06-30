"""2048 adapter — a public, reproducible domain for the evolving-agents engine.

The quantitative host is private; 2048 is the open, batch-runnable sandbox used
for the amnesic-vs-full ablation. See adapter.py (5 protocols + RuleSpecs),
env.py (minimal 2048 + expectimax), candidate.py (memory-independent generator).
"""
from adapters.game2048.adapter import Game2048Adapter, GAME2048_RULE_SPECS, make_execute
from adapters.game2048.candidate import Policy, make_policy, generate_pool

__all__ = [
    "Game2048Adapter",
    "GAME2048_RULE_SPECS",
    "make_execute",
    "Policy",
    "make_policy",
    "generate_pool",
]
