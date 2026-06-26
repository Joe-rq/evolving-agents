# Factor 1: Remember your failures

> Persist every failure to a store, not to conversation memory. Memory is the prerequisite for all evolution.

## Motivation
A pure-prompt agent starts from zero every run. It re-explores the same dead ends, re-misuses the same fields, re-submits the same crowded signals. "Remembering" in-context doesn't survive a session. Evolution begins only when failure is written down — to a file, a table, a ledger.

## Case (alpha-mining, sanitized)
`research_state` table persists per-family / per-field hit rates: `scl12_buzz` (Sharpe -0.73), `sales_growth` (Sharpe -0.13) recorded as dead and never re-picked as a high-quality lead. `candidate_block_reason` hard-blocks any candidate body already tested, so evaluation quota is never re-burned on a known result.

## Anti-pattern
Pure-prompt agent re-steps into the same pit each run; the only "memory" is whatever fits in the context window this turn.

## Core primitive
`Memory` — append-only ledger of attempts + outcomes, scoped per environment (see Factor 4 on why scoping matters).

## Value layer
🟢 **A (stable)** — preventing known failures is deterministic value. Control experiment: the cold group re-commits failures the warm group has already recorded.

---
*Seed — Day-3 expansion: full motivation, code reference, cross-domain example.*
