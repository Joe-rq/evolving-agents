"""SQL adapter — query optimization via cost-driven evolution."""
from adapters.sql.adapter import SQLAdapter, SQL_RULE_SPECS, make_execute
from adapters.sql.candidate import Query, make_query, generate_pool, generate_pool_aware

__all__ = [
    "SQLAdapter", "SQL_RULE_SPECS", "make_execute",
    "Query", "make_query", "generate_pool", "generate_pool_aware",
]
