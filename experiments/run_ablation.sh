#!/usr/bin/env bash
# Amnesic-vs-full ablation (see pre_registration.md).
# Default: M=30 replicates, R=8 rounds, K=20 games/execute, 4x4 board.
# Smoke:   bash experiments/run_ablation.sh -M 1 -K 10
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m experiments.ablation_runner "$@"
