# Factor 5: Seek novelty, avoid crowding

> Prefer novelty over re-exploitation, and protect orthogonal exploration even when it scores low.

## Motivation
Pure exploitation converges to a local optimum — the cognitive-loop failure mode where successive iterations try similar directions with diminishing returns. A self-evolving search must actively avoid re-finding what it already has, and keep an exploration lane for structurally different candidates.

## Case (alpha-mining, sanitized)
- `novelty_score`: field-overlap vs history; ~30% of candidate score, so a fully-explored direction decays.
- portfolio proxy: candidates highly correlated with already-ACTIVE alphas get a crowding penalty.
- exploration lane: lowers the execute-score floor for low-scoring but orthogonal-tagged candidates, so a structurally different probe can still surface.

## Anti-pattern
Greedy exploit — cognitive loop, diminishing returns, the search never escapes its cluster.

## Core primitive
`NoveltyGuard` — novelty scoring + crowding penalty + exploration lane.

## Value layer
🟡 **B (conjectured)** — exploration/exploitation balance is valuable, but its quantitative contribution is entangled with the MetaLearner; under validation.

---
*Seed — Day-3 expansion pending.*
