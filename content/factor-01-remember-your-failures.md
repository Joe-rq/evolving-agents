# Factor 1: Remember your failures

> Persist every failure to a store, not to conversation memory. Memory is the prerequisite for all evolution.

## Motivation

A pure-prompt agent starts from zero every run. It re-explores the same dead ends, re-misuses the same fields, re-submits the same crowded signals. "Remembering" in-context doesn't survive a session — once the context window rolls over or compaction fires, the lesson is gone. Evolution begins only when failure is written down, to a file, a table, a ledger that outlives any single run.

This is the bedrock factor: Factors 2–5 all read from memory and write to it. No persistence, no learning.

## Case (alpha-mining, sanitized)

`research_state` table persists per-family / per-field hit rates. `scl12_buzz` (Sharpe −0.73) and `sales_growth` (Sharpe −0.13) get recorded as dead and are never re-picked as a high-quality lead. `candidate_block_reason` hard-blocks any candidate body already tested, so evaluation quota is never re-burned on a known result.

## Core primitive

`Memory` (`core/memory.py`) — an append-only, universe-scoped ledger of `Attempt`s. Each attempt carries the outcome plus what the adapter protocols classified (family, features, motif, evidence_kinds).

```python
from core.memory import Memory, Attempt

mem = Memory()
mem.record(Attempt(body="ts_corr(close,volume,5)", universe="TOP3000",
                   success=False, family="technical",
                   motif="pure_ts_corr_volume", evidence_kinds={"weak"}))

# "have we already tried this here?" — never re-burn quota on a known body
mem.has_tested("ts_corr(close,volume,5)", "TOP3000")  # True
```

Universe scoping (see Factor 4) means scars from one environment don't pollute another — `has_tested` is per-pond.

## Anti-pattern

A pure-prompt agent re-steps into the same pit each run; its only "memory" is whatever fits in the context window this turn. RAG-style recall (dump history into the prompt and hope) is a weaker form of the same anti-pattern: it survives the session but, as we found empirically, adds zero on routine cases (see [Honest Boundary](honest-boundary.md)).

## Cross-domain

Anywhere a search can repeat a known-bad move: hyperparameter search re-trying configs that OOM'd, test-generation re-emitting structs that crash the parser, prompt-tuning re-sending variants a rubric already rejected. The move is identical — write the failure down, scope it to the relevant context, refuse to re-try it.

## Honest value layer

**Observed, not controlled.** Preventing known failures is deterministic *value* in principle — the cold group would re-commit failures the warm group recorded. But we did not run that control here (mechanisms went live 2026-06-24; too little post-evolution data). We claim the mechanism is implemented and observable, not that its lift was measured.
