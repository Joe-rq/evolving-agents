# Factor 5: Seek novelty, avoid crowding

> Prefer novelty over re-exploitation, and protect orthogonal exploration even when it scores low.

## Motivation

Pure exploitation converges to a local optimum — the cognitive-loop failure mode where successive iterations try similar directions with diminishing returns. A self-evolving search must actively avoid re-finding what it already has, and keep an exploration lane for structurally different candidates. Without this, Factors 1–3 (which are about *avoiding known bad*) would collapse the search into the first okay region it finds.

## Case (real domain, sanitized)

- **Novelty score** — a candidate's field-overlap with history; ~30% of its score, so a fully-explored direction decays naturally.
- **Crowding penalty** — candidates whose motif has already shipped an ACTIVE alpha get penalized; re-finding a known winner is low value.
- **Exploration lane** — lowers the execute-score floor for low-scoring but *orthogonal*-tagged candidates, so a structurally different probe can still surface and run.

## Core primitive

`core/novelty.py` — three functions, all pure scoring over already-extracted features/motifs:

```python
from core.novelty import novelty_score, crowding_penalty, qualifies_exploration_lane

nov = novelty_score(candidate_features, mem, universe="TOP3000")     # 1.0 = brand new
pen = crowding_penalty(candidate_motif, mem, universe="TOP3000")     # <0 if motif already shipped
run = qualifies_exploration_lane(score=0.18, main_threshold=0.20,
                                  exploration_threshold=0.15, is_orthogonal=True)  # True
```

The exploration lane is the controlled escape hatch against greedy exploitation: a candidate that fails the main floor may still run if it is structurally orthogonal and clears a lower bar.

## Anti-pattern

Greedy exploit — cognitive loop, diminishing returns, the search never escapes its cluster. Everything new is penalized as "lower-scoring than what we have," so nothing new ever runs.

## Cross-domain

Any explore/exploit tension: test-case generation (don't keep emitting the same bug class), config search (reserve budget for unseen regions), research agents (Deli_AutoResearch's "direction diversity" — a new direction must differ from every tried one). The mechanism is the same: score novelty, penalize crowding, protect the orthogonal.

## Honest value layer

**Observed, not controlled.** The explore/exploit balance is valuable in principle, but its quantitative contribution is entangled with the MetaLearner (Factor 2) and hard to attribute in isolation. We claim it is implemented and observable, not measured.
