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

| # | Factor |
|---|---|
| 1 | [Remember your failures](content/factor-01-remember-your-failures.md) |
| 2 | [Score the search, not the candidate](content/factor-02-score-the-search-not-the-candidate.md) |
| 3 | [Learn failure modes, not single failures](content/factor-03-learn-failure-modes-not-single-failures.md) |
| 4 | [Pivot structure, not tactics](content/factor-04-pivot-structure-not-tactics.md) |
| 5 | [Seek novelty, avoid crowding](content/factor-05-seek-novelty-avoid-crowding.md) |

**All five are implemented and produced observable evolving behavior — none has controlled effectiveness proof.** The cold-vs-warm control we designed could not run: mechanisms went live 2026-06-24, leaving only ~2-3 days of post-evolution data against ~10 days of baseline (50 records). We claim *mechanism + observed behavior*, not *proven lift*. Full disclosure → [Honest Claims Boundary](content/honest-boundary.md).

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
