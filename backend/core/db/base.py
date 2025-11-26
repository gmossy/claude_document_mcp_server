"""Database abstraction layer for document management.

Provides a unified interface for database operations that can be
implemented by different database backends (SQLite, PostgreSQL, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class DatabaseAdapter(ABC):
    """Abstract base class for database adapters."""

    @abstractmethod
    def connect(self) -> Any:
        """Create and return a database connection.

        Returns:
            Database connection object (type depends on implementation)
        """
        pass

    @abstractmethod
    def close(self, conn: Any) -> None:
        """Close a database connection.

        Args:
            conn: Database connection to close
        """
        pass

    @abstractmethod
    def execute(
        self,
        conn: Any,
        query: str,
        params: Optional[tuple] = None
    ) -> Any:
        """Execute a query and return a cursor.

        Args:
            conn: Database connection
            query: SQL query string
            params: Optional query parameters

        Returns:
            Database cursor object
        """
        pass

    @abstractmethod
    def fetchone(self, cursor: Any) -> Optional[dict[str, Any]]:
        """Fetch one row from cursor as a dictionary.

        Args:
            cursor: Database cursor

        Returns:
            Dictionary with column names as keys, or None if no rows
        """
        pass

    @abstractmethod
    def fetchall(self, cursor: Any) -> list[dict[str, Any]]:
        """Fetch all rows from cursor as list of dictionaries.

        Args:
            cursor: Database cursor

        Returns:
            List of dictionaries, each representing a row
        """
        pass

    @abstractmethod
    def commit(self, conn: Any) -> None:
        """Commit a transaction.

        Args:
            conn: Database connection
        """
        pass

    @abstractmethod
    def rollback(self, conn: Any) -> None:
        """Rollback a transaction.

        Args:
            conn: Database connection
        """
        pass

    @abstractmethod
    def init_schema(self, conn: Any) -> None:
        """Initialize database schema (create tables, indexes, etc.).

        Args:
            conn: Database connection
        """
        pass

    @abstractmethod
    def get_parameter_placeholder(self) -> str:
        """Get the parameter placeholder for this database.

        Returns:
            Placeholder string (e.g., '?' for SQLite, '%s' for PostgreSQL)
        """
        pass

    @abstractmethod
    def get_text_type(self) -> str:
        """Get the TEXT data type for this database.

        Returns:
            Type string (e.g., 'TEXT' for SQLite, 'TEXT' for PostgreSQL)
        """
        pass

    @abstractmethod
    def get_integer_primary_key(self) -> str:
        """Get the integer primary key definition.

        Returns:
            SQL fragment for auto-incrementing integer primary key
        """
        pass

    @abstractmethod
    def supports_fts(self) -> bool:
        """Check if this database supports full-text search.

        Returns:
            True if FTS is supported, False otherwise
        """
        pass

    @abstractmethod
    def create_fts_index(
        self,
        conn: Any,
        table_name: str,
        columns: list[str],
        source_table: str
    ) -> None:
        """Create a full-text search index.

        Args:
            conn: Database connection
            table_name: Name for the FTS index/table
            columns: List of column names to index
            source_table: Source table name
        """
        pass

    @abstractmethod
    def create_fts_triggers(self, conn: Any, fts_table: str, source_table: str) -> None:
        """Create triggers to keep FTS index in sync.

        Args:
            conn: Database connection
            fts_table: FTS table/index name
            source_table: Source table name
        """
        pass

