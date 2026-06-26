# Case Study: Pivot Structure — TOP3000 → TOP1000

> A real pivot-structure event: the agent proposed switching ponds to rescue a factor that was dying of *crowding*, not of *quality*.

This is the demo's single hardest piece of evidence. Every number is verified against the local scoreboard (50-record dataset, private host repo, 2026-06).

## The factor (one expression body)

```
0.5*group_rank(ts_rank(operating_income/close,126),industry)
+ 0.5*group_rank(ts_rank(free_cash_flow_reported_value/close,126),industry)
```

## The two ponds

| pond | status | Sharpe | self_corr | outcome |
|---|---|---|---|---|
| TOP3000 (large-cap) | rejected | **2.15** | **0.7844** | SELF_CORR_FAIL |
| TOP1000 (small-cap) | **submitted**  | **2.15** | **0.6768** | checks clear |

**The factor never changed. Sharpe never changed (2.15 in both). The only thing that moved was self_corr — the crowding metric — from 0.7844 (too crowded → fail) to 0.6768 (clear → pass).**

That is the cleanest possible illustration of Factor 4: the problem was *the environment*, not *the factor*. Tuning decay/window/neutralization harder inside TOP3000 could never have fixed a crowding problem — the agent refused to try, and proposed switching ponds instead.

## Honest detail: TOP1000 wasn't "switch and it lives"

The agent did **not** guess right on the first try. In TOP1000 it ran several variants of the same body:

| variant | self_corr | outcome |
|---|---|---|
| A | 0.916 | SELF_CORR_FAIL |
| B | 0.825 | SELF_CORR_FAIL |
| C | **0.6768** | pass → submitted |

Switching ponds *lowered the crowding baseline enough to make "pass" possible* — but only one specific variant cleared it. The agent still had to search within the new pond. We disclose this openly: it is not a fairy tale of "switch → resurrect."

## Who decided what (human-in-the-loop, disclosed)

- **Agent** accumulated the failure memory (yield / sentiment / growth all fail in TOP3000) and emitted the evolution action: *"don't just change windows — switch data source / economic family."*
- **Agent** proposed the universe switch as the structural pivot.
- **Human** approved the switch (commit `b38ce00`, 2026-06-24).
- **Agent** then auto-applied structural relaxation for the new pond (commit `23ac8a1`: TOP1000 relaxes the leverage/ROA hard-blocks that TOP3000 enforced).

This is **agent-proposes / human-approves**, not autonomous. Disclosed openly.

## Timeline (commit chain, 2026-06)

| commit | what | actor |
|---|---|---|
| `e1937ed` | universe-scoped memory (TOP3000 scars don't pollute TOP1000) | agent system |
| `3a38a52` | close-yield motif soft-penalty after self-corr fail | agent-authored |
| `b38ce00` | switch default universe TOP3000 → TOP1000 | **agent proposed, human approved** |
| `23ac8a1` | TOP1000 structural relaxation + exploration lane | agent system |
| 06-24 | factor clears in TOP1000 (self_corr 0.6768) → submitted | — |

## What this proves / doesn't prove

- ✅ **Proves**: a real pivot-structure event happened; the "switch environment, not tune parameters" insight was correct here; the factor's quality (Sharpe 2.15) was environment-independent.
- ❌ **Doesn't prove**: that the evolution mechanism *caused* the win (no cold-vs-warm control — see [Honest Boundary](../content/honest-boundary.md)); that it generalizes beyond this one event.

## Demo hook (the pitch line)

> "Same factor. Same Sharpe — 2.15. In TOP3000 it died: self_corr 0.78, too crowded. The agent didn't tell me to tune it harder. It told me to switch ponds. In TOP1000, self_corr dropped to 0.68, and it shipped. **The factor was never the problem. The pond was.**"
