"""adapters/codegen/env.py — code generation evaluation via exec (stdlib only).

A candidate is a Python function body. "Execute" = exec it against test cases.
This is the same design as symreg but with CODE instead of formulas:
  - deterministic: same code + same tests → same result
  - graded: pass all tests / pass some (weak) / crash (fail)
  - discrete: code is structural, grafts add/fix lines

Tasks are small programming problems (like LeetCode easy). The agent
discovers correct solutions by trial, remembering which patterns crash.
"""
from __future__ import annotations

import textwrap
from dataclasses import dataclass


@dataclass(frozen=True)
class CodeTask:
    """A coding problem: signature + test cases + description."""
    name: str
    description: str
    signature: str          # e.g. "def solve(lst):"
    tests: tuple            # ((input, expected), ...)
    hints: tuple            # template fragments the generator can use


TASKS = {
    "sum_squares": CodeTask(
        "sum_squares",
        "Return the sum of squares of a list",
        "def solve(lst):",
        (([1, 2, 3], 14), ([0], 0), ([1, 1, 1], 3), ([2, 3], 13)),
        ("return sum(x**2 for x in lst)", "return sum(x*x for x in lst)",
         "total = 0\nfor x in lst:\n    total += x*x\nreturn total"),
    ),
    "count_vowels": CodeTask(
        "count_vowels",
        "Count vowels in a string",
        "def solve(s):",
        (("hello", 2), ("aeiou", 5), ("xyz", 0), ("AaEe", 4)),
        ("return sum(1 for c in s if c.lower() in 'aeiou')",
         "count = 0\nfor c in s:\n    if c in 'aeiouAEIOU':\n        count += 1\nreturn count"),
    ),
    "max_diff": CodeTask(
        "max_diff",
        "Return max difference between adjacent elements",
        "def solve(lst):",
        (([1, 5, 2, 8], 6), ([1, 2, 3], 1), ([10, 1], 9), ([5], 0)),
        ("return max(abs(lst[i+1]-lst[i]) for i in range(len(lst)-1)) if len(lst)>1 else 0",
         "md = 0\nfor i in range(len(lst)-1):\n    md = max(md, abs(lst[i+1]-lst[i]))\nreturn md"),
    ),
}


def get_task(name: str) -> CodeTask:
    return TASKS[name]


def evaluate(code_body: str, task: CodeTask) -> dict:
    """Exec the code against test cases. Returns pass ratio + error tags.

    code_body is the function BODY (without def line). We wrap it.
    """
    full_code = f"{task.signature}\n{textwrap.indent(code_body, '    ')}"

    passed = 0
    total = len(task.tests)
    error_kind = None
    error_msg = ""

    try:
        ns = {}
        exec(full_code, ns)
        func = ns.get("solve")
        if func is None:
            return {"score": 0.0, "evidence_kinds": {"no_func"},
                    "passed": 0, "total": total, "error": "no solve function"}
    except SyntaxError as e:
        return {"score": 0.0, "evidence_kinds": {"syntax_error"},
                "passed": 0, "total": total, "error": str(e)}
    except Exception as e:
        return {"score": 0.0, "evidence_kinds": {type(e).__name__.lower()},
                "passed": 0, "total": total, "error": str(e)}

    for inp, expected in task.tests:
        try:
            result = func(inp)
            if result == expected:
                passed += 1
            else:
                error_kind = "wrong_answer"
        except TypeError as e:
            error_kind = "type_error"; error_msg = str(e)
        except Exception as e:
            error_kind = type(e).__name__.lower(); error_msg = str(e)

    ratio = passed / total
    kinds = set()
    if ratio == 1.0:
        pass  # perfect
    elif ratio >= 0.5:
        kinds.add("partial_pass")
    elif error_kind:
        kinds.add(error_kind)
    else:
        kinds.add("wrong_answer")

    return {
        "score": round(ratio, 4),
        "evidence_kinds": kinds,
        "passed": passed, "total": total,
        "error": error_msg,
    }


def _selftest():
    print("=== codegen env selftest ===")
    for tname in ("sum_squares", "count_vowels"):
        t = get_task(tname)
        print(f"\ntask: {tname} ({t.description})")
        tests = {
            "null_bug": "return lst + 1",
            "wrong_op": "return sum(x*2 for x in lst)" if tname == "sum_squares" else "return len(s)",
            "perfect": t.hints[0],
        }
        for label, code in tests.items():
            r = evaluate(code, t)
            print(f"  {label:12s} score={r['score']:.2f} passed={r['passed']}/{r['total']} kinds={sorted(r['evidence_kinds'])}")


if __name__ == "__main__":
    _selftest()
