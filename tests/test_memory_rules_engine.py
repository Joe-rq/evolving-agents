from __future__ import annotations

from adapters.mock.adapter import MockAdapter, MockCandidate
from core.engine import Engine
from core.memory import Attempt, Memory
from core.rules import RuleSpec, project_rules, rule_adjustment, rule_block_reason


def test_memory_is_universe_scoped_and_append_only() -> None:
    memory = Memory()
    memory.record(Attempt("a", "u1", success=False, family="f1", motif="m1"))
    memory.record(Attempt("a", "u2", success=True, family="f1", motif="m1"))

    assert len(memory) == 2
    assert len(memory.attempts("u1")) == 1
    assert memory.has_tested("a", "u1")
    assert memory.has_tested("a", "u2")
    assert memory.failures("u1")[0].body == "a"
    assert memory.successes("u2")[0].body == "a"


def test_rule_projection_is_auditable_and_blocks_by_motif() -> None:
    attempts = [
        Attempt("bad-1", "u", False, motif="risky", evidence_kinds={"weak"}),
        Attempt("bad-2", "u", False, motif="risky", evidence_kinds={"weak"}),
    ]
    specs = [RuleSpec("risky", "weak", 2, "block", -1.0, "repeat weak failures")]

    rules = project_rules(attempts, specs, scope="u")

    assert len(rules) == 1
    assert rules[0].evidence_count == 2
    assert rules[0].evidence_ids == ("bad-1", "bad-2")
    assert rule_block_reason("risky", rules) == "rule_block:u:risky:block"


def test_rule_adjustment_caps_non_block_penalties() -> None:
    attempts = [
        Attempt("bad-1", "u", False, motif="slow", evidence_kinds={"timeout"}),
        Attempt("bad-2", "u", False, motif="slow", evidence_kinds={"timeout"}),
    ]
    specs = [
        RuleSpec("slow", "timeout", 1, "penalize", -0.8),
        RuleSpec("slow", "timeout", 2, "penalize", -0.8),
    ]

    rules = project_rules(attempts, specs, scope="u")

    assert rule_adjustment("slow", rules) == -1.0


def test_engine_scores_executes_records_and_blocks_known_dead_ends() -> None:
    memory = Memory()
    engine = Engine(MockAdapter(), memory, [])
    candidates = [
        MockCandidate("winner", family="good", features=["x"], motif=""),
        MockCandidate("loser", family="bad", features=["y"], motif="weak"),
    ]

    def execute(candidate: MockCandidate) -> dict:
        return {
            "success": candidate.body == "winner",
            "weak": candidate.body == "loser",
            "evidence_kinds": {"weak"} if candidate.body == "loser" else set(),
        }

    first = engine.run(candidates, universe="demo", execute=execute, max_execute=2)
    second = engine.run(candidates, universe="demo", execute=execute, max_execute=2)

    assert len(first["executed"]) == 2
    assert len(memory.attempts("demo")) == 2
    assert all(sc.block_reason == "already_tested" for sc in second["scored"])
    assert second["executed"] == []

