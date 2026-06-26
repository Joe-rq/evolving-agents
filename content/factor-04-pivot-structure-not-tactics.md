# Factor 4: Pivot structure, not tactics

> When stuck repeatedly, change the environment or structural frame — not the parameters. And carry memory isolation across environments.

## Motivation
When a search stalls inside one frame, the decisive gain usually comes from correcting the *environment* itself, not from tuning strategy harder inside the existing frame (cf. Deli_AutoResearch: "pivot structure, not tactics"). Concretely: if a signal keeps failing in one market, the issue may be the market's nature — not the signal.

## Case (alpha-mining, sanitized)
Same factor expression body:
- TOP3000 (large-cap): self_corr **0.7844 → FAIL** (crowded) → rejected
- TOP1000 (small-cap): Sharpe **2.15**, self_corr **0.6768 → PASS** → ready_to_submit

The agent's insight: *"not the factor is dead — the pond is wrong for it."* **Agent proposed** the universe switch; human approved. Memory isolation: TOP3000 scars (e.g. dead sentiment/growth signals) do not pollute TOP1000 candidates.

Independently corroborated: a separate project found INDUSTRY (vs SUBINDUSTRY) neutralization to be the key structural switch — the same pattern in a different parameter.

## Anti-pattern
Keep tuning decay / window / neutralization inside the dead pond — sinking deeper into a local optimum instead of questioning the frame.

## Core primitive
`Evolver` (pivot policy: N strikes → switch structural frame, not tweak parameters) + universe-scoped `Memory` (isolate scars per environment).

## Value layer
🟡 **B (conjectured)** — strongest *narratively*, but carries an honest human-in-the-loop boundary: the agent **proposed** the pivot, the human **approved**. The quality lift is correlated, causation under validation.

---
*Seed — Day-3 expansion pending.*
