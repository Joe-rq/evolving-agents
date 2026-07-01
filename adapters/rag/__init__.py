"""RAG adapter — retrieval strategy optimization via config evolution."""
from adapters.rag.adapter import RAGAdapter, RAG_RULE_SPECS, make_execute
from adapters.rag.candidate import Strategy, make_strategy, generate_pool, generate_pool_aware

__all__ = [
    "RAGAdapter", "RAG_RULE_SPECS", "make_execute",
    "Strategy", "make_strategy", "generate_pool", "generate_pool_aware",
]
