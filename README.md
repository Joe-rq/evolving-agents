# evolving-agents

> Principles for building agents that **learn from their own failures**.
> *In the spirit of [12-factor agents](https://github.com/humanlayer/12-factor-agents).*

12-factor agents tells you how to build **reliable** agents.
This project tells you how to build agents that **evolve** — that get better at *searching* by remembering what failed, instead of starting from zero every run.

> ⚠️ **WIP** — hackathon scaffold (2026-06-26). Core engine + full factor docs in progress.

## The thesis

Most "agentic" search loops don't actually learn. They either:
- start fresh every run (same dead ends re-explored), or
- dump history into a prompt and hope (RAG-style recall — which we've empirically found adds zero on routine cases).

The agents that *do* keep getting better do something different: **they score the search strategy itself, learn failure *modes* not single failures, and pivot structure when stuck.** This project names those mechanisms.

## The 5 Factors

| # | Factor | Value layer |
|---|---|---|
| 1 | [Remember your failures](content/factor-01-remember-your-failures.md) | 🟢 A stable |
| 2 | [Score the search, not the candidate](content/factor-02-score-the-search-not-the-candidate.md) | 🟡 B conjectured |
| 3 | [Learn failure modes, not single failures](content/factor-03-learn-failure-modes-not-single-failures.md) | 🟢 A stable |
| 4 | [Pivot structure, not tactics](content/factor-04-pivot-structure-not-tactics.md) | 🟡 B conjectured |
| 5 | [Seek novelty, avoid crowding](content/factor-05-seek-novelty-avoid-crowding.md) | 🟡 B conjectured |

**Honest layering** — not all factors are equally proven:
- 🟢 **A (stable)** — Factor 1, 3: prevent known failures. Verified by cold-vs-warm control.
- 🟡 **B (conjectured)** — Factor 2, 4, 5: improve search quality. Correlated in practice, causation under validation.

## Repo layout

```
content/    # 5 factor docs (CC BY-SA 4.0)
core/       # domain-agnostic engine: memory / meta-learner / evolver / novelty (Apache 2.0)
adapters/   # domain adapters implementing the 5 protocols (e.g. quant)
examples/   # cold-vs-warm control experiments
img/        # diagrams
```

## Status & honest boundary

Validated on **one domain** (quantitative factor mining, private). The mechanism is domain-agnostic by design; cross-domain validation is roadmap, not claim.

## License

- Code (`core/`, `adapters/`): Apache 2.0 — see [LICENSE](LICENSE)
- Content (`content/`): CC BY-SA 4.0 — see [content/LICENSE.md](content/LICENSE.md)
