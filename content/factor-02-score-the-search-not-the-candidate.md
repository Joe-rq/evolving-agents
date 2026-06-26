# Factor 2: Score the search, not the candidate

> Don't just evaluate how good each candidate is — evaluate *which direction is worth searching next*. Score the strategy, not the solution.

## Motivation

Standard optimization (Bayesian Optimization included) scores candidates and picks the best one. It never learns *"technical factors have the lowest pass rate here — search profitability first."* The durable knowledge in a search loop is meta: which families, dimensions, and structures actually pay off. Capturing that is meta-learning over strategy space — a level above candidate scoring.

This is the factor that makes the difference between an agent that runs and an agent that *improves at running*. Candidate scoring tells you what to try; search-strategy scoring tells you where to look.

## Case (real domain, sanitized)

`score_families` ranks economic families by `0.5·hit_rate + 0.2·recency + 0.3·freshness`, with a strike rule (≥ N tries, zero candidates → score −1, excluded entirely). `technical` empirically has the lowest pass rate, so cold-start ordering puts it last automatically — without anyone hard-coding "avoid technical." The agent learns the ordering from its own ledger.

## Core primitive

`MetaLearner.score_families` (`core/meta_learner.py`) — scores search branches from the `Memory` ledger and steers generation toward high-EV directions.

```python
from core.meta_learner import MetaLearner

ml = MetaLearner(strike_threshold=5)
scores = ml.score_families(mem, universe="TOP3000", known_families=["technical", "profitability", ...])
# {'profitability': 0.61, 'analyst': 0.55, ..., 'technical': -1.0}  ← struck, stop searching
```

The struck branch (−1.0) is excluded by the engine before any candidate in it is even generated — search budget is spent on high-EV directions.

## Anti-pattern

Score-only optimization keeps re-entering low-yield regions because it has no memory of yield-by-direction; every run looks like the first. A candidate-scoring-only loop is "smart per item, dumb overall."

## Cross-domain

Test-case generation: score which *property categories* (boundary / equivalence / error-path) have found bugs, not just which individual test is good. Hyperparameter search: score which *model families* (GBM / DNN / linear) pay off on this dataset class. The meta-level is always "which branch is worth more samples."

## Honest value layer

**Observed, not controlled.** Improving search *quality* is real in practice, but its measured lift must be isolated from in-context learning via a control we could not run. We claim correlation (the family ordering tracked empirical pass rates), not causation.
