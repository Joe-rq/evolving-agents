# evolving-agents

> Principles for building agents that **learn from their own failures**.
> *In the spirit of [12-factor agents](https://github.com/humanlayer/12-factor-agents).*

12-factor agents tells you how to build **reliable** agents.
This project tells you how to build agents that **evolve** — that get better at *searching* by remembering what failed, instead of starting from zero every run.

> ⚠️ **WIP** — hackathon build (2026-06). Core engine runnable on a mock domain; one real domain validated privately.

## The thesis

Most "agentic" search loops don't actually learn. They either:
- start fresh every run (same dead ends re-explored), or
- dump history into a prompt and hope (RAG-style recall — which we've empirically found adds zero on routine cases).

The agents that *do* keep getting better do something different: **they score the search strategy itself, learn failure *modes* not single failures, and pivot structure when stuck.** This project names those mechanisms, implements them as a domain-agnostic engine, and validates the architecture on one real domain.

## What's here — three legs

1. **The engine** (`core/`) — a domain-agnostic self-evolution loop: memory, rules, meta-learner, evolver, novelty, orchestrated by `engine.py`. Runs standalone with a mock adapter.
2. **A real domain** (private) — a quantitative factor-mining host implements the 5 adapter protocols against real data. This is where the mechanisms were observed, not constructed. Sanitized evidence → [case study](examples/case-study-pond-switch.md).
3. **Honest disclosure** — every claim is bounded. We say what the mechanisms did, and openly what we could *not* prove. → [Honest Claims Boundary](content/honest-boundary.md)

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
content/    # 5 factor docs + honest-boundary (CC BY-SA 4.0)
core/       # domain-agnostic engine (Apache 2.0):
            #   protocols · memory · rules · meta_learner · evolver · novelty · engine
adapters/   # reference mock adapter (toy domain); real adapters live in private host repos
examples/   # sanitized case studies
img/        # diagrams
```

## Positioning (and what this is *not*)

Self-evolving agents is a crowded space — [EvoMap/evolver](https://github.com/EvoMap/evolver), [AgentEvolver](https://github.com/modelscope/AgentEvolver), ExpeL, Reflexion, Voyager all touch it. This project does not claim a novel mechanism.

What it offers instead:
- **An engine, not a platform.** EvoMap is an A2A cross-node experience-sharing *platform* (we've used its memory layer). evolving-agents is a local, embeddable *engine* — a different abstraction layer, simpler and teachable in five named factors.
- **Auditable rules.** Each penalty a candidate receives traces to concrete past failures (`evidence_ids`), not a black-box "the agent learned."
- **Bounded honesty.** We do not market a learning curve we can't control. The honest boundary *is* the differentiator — most "self-evolving" demos cannot answer "is this evolution or in-context learning?"

## Status & honest boundary

Validated on **one domain** (quantitative factor mining, private). The mechanism is domain-agnostic by design; cross-domain validation is roadmap, not claim.

## License

- Code (`core/`, `adapters/`): Apache 2.0 — see [LICENSE](LICENSE)
- Content (`content/`): CC BY-SA 4.0 — see [content/LICENSE.md](content/LICENSE.md)
