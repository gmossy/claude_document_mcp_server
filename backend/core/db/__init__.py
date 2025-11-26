"""Database abstraction layer for document management."""

from backend.core.db.base import DatabaseAdapter
from backend.core.db.sqlite_adapter import SQLiteAdapter
from backend.core.db.postgres_adapter import PostgreSQLAdapter

__all__ = [
    "DatabaseAdapter",
    "SQLiteAdapter",
    "PostgreSQLAdapter",
]

