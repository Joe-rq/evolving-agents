# Factor 3: Learn failure modes, not single failures

> From one failure, down-weight the whole class — don't just block that one candidate.

## Motivation

Blocking a single dead candidate is shallow: its siblings and variants keep burning budget. The durable lesson of a self-correlation failure is usually a property of the whole motif (e.g. "close-denominator yield signals are crowded"), not of one expression. Learning the class from a single instance is where real sample-efficiency comes from — one failure teaches you about a neighborhood.

## Case (alpha-mining, sanitized)

After a self-correlation FAIL on a mixed `operating_income/close + FCF/close` factor, the entire close-yield motif class is penalized (`operating_cashflow_close_mix` −0.8, `cashflow_close_yield` −0.65, `operating_income_close_yield` −0.35), pushing orthogonal sentiment/growth probes ahead of crowded variants. The penalty is *projected from the ledger* by `strategy_memory.project_strategy_rules` — no hand-written rule, agent-authored from observed failures (commit `3a38a52`).

## Core primitive

Two pieces, in `core/rules.py`:

- `Rule` / `RuleSpec` — a declarative rule carries `motif`, `action` (block/penalize/cooldown), `score_adjustment`, and crucially `confidence` + `evidence_ids`. The confidence grows with evidence count; the evidence ids trace the rule back to *which specific failures* induced it.
- `project_rules(attempts, specs)` — turns the ledger into `Rule`s via the domain's `RuleSpec`s. The adapter owns *which* motifs and *how harsh* (domain IP); the engine owns the projection machinery.

```python
from core.rules import RuleSpec, project_rules

specs = [RuleSpec(motif="close_yield", evidence_kind="corr_failed",
                  min_evidence=1, action="block", adjustment=-0.8, reason="crowded")]
rules = mem.project_rules(specs, universe="TOP3000")
# Rule(motif="close_yield", action="block", confidence=0.55,
#     evidence_ids=("cy_expr_1", "cy_expr_2"))  ← auditable
```

The auditable `evidence_ids` are the honesty edge: when the engine blocks a candidate, it can answer *"because of these specific past failures,"* not "trust me."

## Anti-pattern

Per-candidate blocklist — the same motif's untested variants keep consuming quota one by one until each is independently rejected. One failure should teach you about a class, not just an instance.

## Cross-domain

Prompts that trigger refusals: one bad phrasing shouldn't just be avoided — its *category* (overly-long instruction, ambiguous negation) should be down-weighted. Crash reproducers: one failing input teaches you about the input *shape* (deeply nested, unicode-laden) that deserves a class-level guard.

## Honest value layer

**Observed, not controlled.** Class-level prevention is strictly stronger than per-instance (Factor 1), and is observable in the ledger projection. But "stronger" here is structural reasoning, not a measured delta.
