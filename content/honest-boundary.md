# Honest Claims Boundary

> What this project can and cannot claim about self-evolution — and why we disclose the limit openly.

This is the most important doc in the repo. Every demo, pitch, and factor doc must stay inside this boundary.

## What we claim

1. **The 5 mechanisms are implemented.** Memory, MetaLearner, failure-mode penalty, structural pivot, novelty guard — all exist as code and ran on a real workload (quantitative factor mining).

2. **Real evolving behavior was observed.** Most concretely: the same factor expression that **failed** in TOP3000 (large-cap, self_corr 0.7844 FAIL) was **resurrected** in TOP1000 (small-cap, Sharpe 2.15, self_corr 0.6768 PASS) after the agent proposed switching ponds. A real pivot-structure event with commit history — not a constructed demo.

3. **Some learning is agent-authored from the ledger**, not purely hand-written rules (e.g. the close-yield motif class penalty, commit `3a38a52`).

## What we do NOT claim

1. **No controlled proof of effectiveness.** We designed a cold-vs-warm control (amnesia version vs full-memory version, same task). **It could not run**: the evolution mechanisms went live 2026-06-24, leaving only ~2-3 days of post-evolution data against ~10 days of baseline (50 records total). Sample too small for any honest comparison.

2. **No quantified lift.** Without the control, we cannot say "evolution improved yield by X%." Any improvement curve is confounded with in-context learning and human-in-the-loop decisions.

3. **No cross-domain validation.** The mechanism ran on one domain (factor mining). Domain-agnostic is a *design intent*, not a tested claim.

## Why we disclose this openly

Several projects market "self-evolving agents" with three-day learning curves and spectacular counts, **without a control experiment and without disclosing the boundary**. Their "evolution" cannot be distinguished from in-context learning or cherry-picking.

We believe the honest path — *mechanism + observed behavior + disclosed limit* — is more durable than an uncontrolled claim. Effectiveness validation is on our roadmap; it is not today's claim.

## Implication for each factor

| Factor | Mechanism | Observed behavior | Effectiveness |
|---|---|---|---|
| 1 Remember failures | ✅ implemented (block tested bodies) | ✅ observed | not controlled |
| 2 Score the search | ✅ implemented (family scoring) | ✅ observed | not controlled |
| 3 Learn failure modes | ✅ implemented (motif penalty) | ✅ observed (`3a38a52`) | not controlled |
| 4 Pivot structure | ✅ implemented (universe switch) | ✅ observed (TOP3000→TOP1000) | not controlled |
| 5 Seek novelty | ✅ implemented (novelty + exploration lane) | ✅ observed | not controlled |

## The one-sentence pitch (inside boundary)

> "Five self-evolution mechanisms, all implemented, with one observed pivot-structure event where the agent proposed switching ponds to resurrect a dead factor. We disclose openly that controlled effectiveness proof is still roadmap — because the alternative is marketing."
