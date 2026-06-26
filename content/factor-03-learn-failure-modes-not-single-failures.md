# Factor 3: Learn failure modes, not single failures

> From one failure, down-weight the whole class — don't just block that one candidate.

## Motivation
Blocking a single dead candidate is shallow: its siblings and variants keep burning budget. The durable lesson of a self-correlation failure is usually a property of the whole motif (e.g. "close-denominator yield signals are crowded"), not of one expression. Learning the class from a single instance is where real sample-efficiency comes from.

## Case (alpha-mining, sanitized)
After a self-correlation FAIL on a mixed `operating_income/close + FCF/close` factor, the entire close-yield motif class is soft-penalized (`operating_cashflow_close_mix` -0.55, `cashflow_close_yield` -0.25, `operating_income_close_yield` -0.15), pushing orthogonal sentiment/growth probes ahead of crowded variants. Agent-authored from the result ledger — no human-written rule (commit `3a38a52`).

## Anti-pattern
Per-candidate blocklist — the same motif's untested variants keep consuming quota one by one until each is independently rejected.

## Core primitive
`FailureMotifExtractor` (adapter protocol: map candidate → failure motif) + class-level penalty applied by the `MetaLearner`.

## Value layer
🟢 **A (stable)** — preventing an entire *class* of known failures is deterministic, and strictly stronger than Factor 1's per-instance blocking.

---
*Seed — Day-3 expansion pending.*
