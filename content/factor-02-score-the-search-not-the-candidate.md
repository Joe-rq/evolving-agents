# Factor 2: Score the search, not the candidate

> Don't just evaluate how good each candidate is — evaluate *which direction is worth searching next*. Score the strategy, not the solution.

## Motivation
Standard optimization (incl. Bayesian Optimization) scores candidates and picks the best one. It never learns "technical factors have the lowest pass rate — search profitability first." The durable knowledge in a search loop is meta: which families, dimensions, and structures actually pay off. Capturing that is meta-learning over strategy space — a level above candidate scoring.

## Case (alpha-mining, sanitized)
`score_families` ranks economic families by `0.5·hit_rate + 0.2·recency + 0.3·freshness`, with a strike rule (N tries, zero candidates → score -1, excluded entirely). `technical` empirically has the lowest pass rate, so cold-start ordering puts it last automatically — without anyone hard-coding "avoid technical."

## Anti-pattern
Score-only optimization keeps re-entering low-yield regions because it has no memory of yield-by-direction; every run looks like the first.

## Core primitive
`MetaLearner` — scores search branches (families / dimensions) from the Memory ledger and steers generation toward high-EV directions.

## Value layer
🟡 **B (conjectured)** — improving search *quality* is real in practice, but its measured lift must be isolated from in-context learning via control B. Cannot yet claim causation, only correlation.

---
*Seed — Day-3 expansion pending.*
