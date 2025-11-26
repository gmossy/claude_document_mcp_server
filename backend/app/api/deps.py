"""FastAPI dependencies for database and service access.

This module provides dependency injection functions for accessing
the database adapter and document service throughout the application.
"""

from collections.abc import Generator
from pathlib import Path

from backend.app.config import settings
from backend.core.db import DatabaseAdapter, PostgreSQLAdapter, SQLiteAdapter
from backend.core.services import DocumentService


def get_db_adapter() -> DatabaseAdapter:
    """Get database adapter based on configuration.

    Returns:
        DatabaseAdapter instance (SQLite or PostgreSQL)

    Raises:
        ValueError: If database URL format is not supported
    """
    if settings.database_url.startswith("sqlite:///"):
        db_path = Path(settings.database_url.replace("sqlite:///", ""))
        return SQLiteAdapter(db_path)
    elif settings.database_url.startswith("postgresql://"):
        return PostgreSQLAdapter(settings.database_url)
    else:
        raise ValueError(
            f"Unsupported database URL format: {settings.database_url}. "
            "Supported formats: sqlite:///path/to/db.db or "
            "postgresql://user:pass@host:port/dbname"
        )


# Initialize adapter and service
db_adapter = get_db_adapter()
storage_dir = Path(settings.storage_dir)
document_service = DocumentService(db_adapter, storage_dir)


def get_db() -> Generator[DatabaseAdapter, None, None]:
    """Get database adapter for dependency injection.

    Yields:
        DatabaseAdapter instance
    """
    yield db_adapter


def get_document_service() -> DocumentService:
    """Get document service for dependency injection.

    Returns:
        DocumentService instance
    """
    return document_service

