"""codegen adapter — code generation domain for evolving-agents."""
from adapters.codegen.adapter import CodegenAdapter, CODEGEN_RULE_SPECS, make_execute
from adapters.codegen.candidate import (
    CodeExpr, make_code, generate_pool, generate_pool_aware, family_of,
)
from adapters.codegen.env import evaluate, get_task, CodeTask, TASKS

__all__ = [
    "CodegenAdapter", "CODEGEN_RULE_SPECS", "make_execute",
    "CodeExpr", "make_code", "generate_pool", "generate_pool_aware", "family_of",
    "evaluate", "get_task", "CodeTask", "TASKS",
]
