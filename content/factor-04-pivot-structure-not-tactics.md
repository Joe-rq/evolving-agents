# Factor 4: Pivot structure, not tactics

> When stuck repeatedly, change the environment or structural frame — not the parameters. And carry memory isolation across environments.

## Motivation

When a search stalls inside one frame, the decisive gain usually comes from correcting the *environment* itself, not from tuning strategy harder inside the existing frame (cf. Deli_AutoResearch: *"pivot structure, not tactics"*). Concretely: if a signal keeps failing in one market, the issue may be the market's nature — not the signal. Tuning decay/window/neutralization inside a dead pond is the failure mode this factor exists to break.

This is the factor with the strongest narrative in the project — and, honestly, the one most entangled with human-in-the-loop judgment.

## Case (alpha-mining, sanitized)

One factor expression body:

```
0.5*group_rank(ts_rank(operating_income/close,126),industry)
+ 0.5*group_rank(ts_rank(free_cash_flow_reported_value/close,126),industry)
```

| pond | status | Sharpe | self_corr | outcome |
|---|---|---|---|---|
| TOP3000 (large-cap) | rejected | 2.15 | 0.7844 | SELF_CORR_FAIL (crowded) |
| TOP1000 (small-cap) | **submitted** | 2.15 | 0.6768 | checks clear |

**The factor never changed. Sharpe never changed (2.15 in both). The only thing that moved was self_corr — the crowding metric.** Tuning parameters inside TOP3000 could never have fixed a crowding problem. The agent's insight was *"not the factor is dead — the pond is wrong for it,"* and it proposed switching ponds. Full timeline and the honest "not switch-and-it-lives" detail → [case study](../examples/case-study-pond-switch.md).

## Core primitive

`Evolver` (`core/evolver.py`) — detects frame exhaustion (N strategy classes struck, or a failure motif hit ≥ threshold times in the current universe) and emits a *recommendation*. It does **not** choose what to pivot to; that stays with the adapter / human.

```python
from core.evolver import Evolver

ev = Evolver(family_strike_count=2, motif_strike_count=3)
if ev.should_pivot(mem, "TOP3000", family_scores):
    print(ev.pivot_recommendation(mem, "TOP3000", family_scores))
    # "2 strategy classes struck in 'TOP3000' (cashflow, sentiment) —
    #  switch structural frame, not parameters."
```

The split is deliberate: **agent proposes / human approves**. The agent observed the stall and named the structural cause; the human green-lit the universe switch. Disclosed openly — this is not autonomous.

Independently corroborated: a separate project found INDUSTRY (vs SUBINDUSTRY) neutralization to be the key structural switch — the same "pivot structure" pattern in a different parameter.

## Anti-pattern

Keep tuning decay / window / neutralization inside the dead pond — sinking deeper into a local optimum instead of questioning the frame. Parameter-tweaking feels productive (you're "doing something") but is exactly the trap.

## Cross-domain

Hyperparameter search stuck on a model family: the fix may be switching *dataset representation*, not tuning the model. Prompt-tuning stuck: switch *task decomposition*, not wording. The signal is always "repeated stalls in one frame" → question the frame.

## Honest value layer

**Observed, not controlled — and human-in-the-loop.** This factor is strongest *narratively* (the pond-switch is real, with verified numbers) but carries an honest boundary: the agent **proposed** the pivot, the human **approved**. The quality lift is correlated with the mechanism, not causally isolated. We disclose this rather than dress it up as autonomous self-evolution.
