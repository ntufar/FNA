"""
Database package for FNA Platform.

This package contains database connection management, session handling,
vector operations, and database utilities.
"""

from .connection import (
    init_database,
    close_database,
    get_db,
    get_db_session,
    get_db_session_context,
    atomic_transaction,
    check_database_health,
)

from .vector_setup import (
    setup_vector_environment,
    perform_similarity_search,
    get_vector_stats,
    VectorSetupManager,
)

__all__ = [
    "init_database",
    "close_database", 
    "get_db",
    "get_db_session",
    "get_db_session_context",
    "atomic_transaction",
    "check_database_health",
    "setup_vector_environment",
    "perform_similarity_search",
    "get_vector_stats",
    "VectorSetupManager",
]
