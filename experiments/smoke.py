"""Fast reproducibility smoke entry point.

Runs a tiny 2048 amnesic-vs-full ablation and writes the usual JSON artifact.
This is intentionally small enough for a first clone check; use
`evolving-agents-ablation -M 30` for the pre-registered run.
"""
from __future__ import annotations

from experiments.ablation_runner import main as run_ablation


def main() -> None:
    run_ablation(M=1, R=4, K=2, size=4, out_path="experiments/_smoke_result.json")


if __name__ == "__main__":
    main()

