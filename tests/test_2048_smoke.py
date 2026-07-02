from __future__ import annotations

from experiments.ablation_runner import run_one_replicate


def test_2048_ablation_smoke_exercises_full_and_amnesic_paths() -> None:
    result = run_one_replicate(seed=1, R=4, K=1, size=4, max_execute=2, pool_n=6)

    assert result["seed"] == 1
    assert len(result["full_curve"]) == 4
    assert len(result["amn_curve"]) == 4
    assert "primary_diff" in result
    assert result["mechanism"]["full_blocks"] >= result["mechanism"]["amn_blocks"]
