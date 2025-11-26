"""SQLite database adapter implementation."""

import sqlite3
from pathlib import Path
from typing import Any, Optional

from backend.core.db.base import DatabaseAdapter


class SQLiteAdapter(DatabaseAdapter):
    """SQLite implementation of DatabaseAdapter."""

    def __init__(self, db_path: Path):
        """Initialize SQLite adapter.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        """Create and return a SQLite connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def close(self, conn: sqlite3.Connection) -> None:
        """Close SQLite connection."""
        conn.close()

    def execute(
        self,
        conn: sqlite3.Connection,
        query: str,
        params: Optional[tuple] = None
    ) -> sqlite3.Cursor:
        """Execute a query and return a cursor."""
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

    def fetchone(self, cursor: sqlite3.Cursor) -> Optional[dict[str, Any]]:
        """Fetch one row as dictionary."""
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetchall(self, cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
        """Fetch all rows as list of dictionaries."""
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def commit(self, conn: sqlite3.Connection) -> None:
        """Commit transaction."""
        conn.commit()

    def rollback(self, conn: sqlite3.Connection) -> None:
        """Rollback transaction."""
        conn.rollback()

    def get_parameter_placeholder(self) -> str:
        """SQLite uses '?' for parameters."""
        return "?"

    def get_text_type(self) -> str:
        """SQLite uses 'TEXT'."""
        return "TEXT"

    def get_integer_primary_key(self) -> str:
        """SQLite uses INTEGER PRIMARY KEY AUTOINCREMENT."""
        return "INTEGER PRIMARY KEY AUTOINCREMENT"

    def supports_fts(self) -> bool:
        """SQLite supports FTS5."""
        return True

    def init_schema(self, conn: sqlite3.Connection) -> None:
        """Initialize SQLite database schema."""
        cursor = conn.cursor()

        # Documents table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS documents (
                id {self.get_text_type()} PRIMARY KEY,
                title {self.get_text_type()} NOT NULL,
                content {self.get_text_type()} NOT NULL,
                tags {self.get_text_type()} NOT NULL DEFAULT '[]',
                status {self.get_text_type()} NOT NULL DEFAULT 'draft',
                metadata {self.get_text_type()} NOT NULL DEFAULT '{{}}',
                created_at {self.get_text_type()} NOT NULL,
                updated_at {self.get_text_type()} NOT NULL,
                size INTEGER NOT NULL,
                content_hash {self.get_text_type()} NOT NULL
            )
        """)

        # Versions table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS document_versions (
                id {self.get_integer_primary_key()},
                document_id {self.get_text_type()} NOT NULL,
                version_number INTEGER NOT NULL,
                title {self.get_text_type()} NOT NULL,
                content {self.get_text_type()} NOT NULL,
                tags {self.get_text_type()} NOT NULL,
                status {self.get_text_type()} NOT NULL,
                metadata {self.get_text_type()} NOT NULL,
                created_at {self.get_text_type()} NOT NULL,
                comment {self.get_text_type()} NOT NULL DEFAULT '',
                content_hash {self.get_text_type()} NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                UNIQUE(document_id, version_number)
            )
        """)

        # File-level versions
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS document_files (
                id {self.get_integer_primary_key()},
                document_id {self.get_text_type()} NOT NULL,
                version_number INTEGER NOT NULL,
                format {self.get_text_type()} NOT NULL,
                path {self.get_text_type()} NOT NULL,
                size INTEGER NOT NULL,
                created_at {self.get_text_type()} NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (document_id, version_number)
                    REFERENCES document_versions(document_id, version_number)
            )
        """)

        # Binary artifacts table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS document_binary (
                id {self.get_integer_primary_key()},
                document_id {self.get_text_type()} NOT NULL,
                version_number INTEGER NOT NULL,
                filename {self.get_text_type()} NOT NULL,
                mime_type {self.get_text_type()} NOT NULL,
                format {self.get_text_type()} NOT NULL,
                content_blob BLOB NOT NULL,
                size_bytes INTEGER NOT NULL,
                checksum {self.get_text_type()} NOT NULL,
                created_at {self.get_text_type()} NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (document_id, version_number)
                    REFERENCES document_versions(document_id, version_number),
                UNIQUE(document_id, version_number, filename)
            )
        """)

        # Embeddings table
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS document_embeddings (
                id {self.get_integer_primary_key()},
                document_id {self.get_text_type()} NOT NULL,
                version_number INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                text {self.get_text_type()} NOT NULL,
                metadata {self.get_text_type()} NOT NULL DEFAULT '{{}}',
                created_at {self.get_text_type()} NOT NULL,
                FOREIGN KEY (document_id) REFERENCES documents(id),
                FOREIGN KEY (document_id, version_number)
                    REFERENCES document_versions(document_id, version_number),
                UNIQUE(document_id, version_number, chunk_index)
            )
        """)

        # Full-text search index (SQLite FTS5)
        if self.supports_fts():
            self.create_fts_index(
                conn,
                "documents_fts",
                ["id", "title", "content", "tags"],
                "documents"
            )
            self.create_fts_triggers(conn, "documents_fts", "documents")

        conn.commit()

    def create_fts_index(
        self,
        conn: sqlite3.Connection,
        table_name: str,
        columns: list[str],
        source_table: str
    ) -> None:
        """Create SQLite FTS5 virtual table."""
        cursor = conn.cursor()
        columns_str = ", ".join(columns)
        cursor.execute(f"""
            CREATE VIRTUAL TABLE IF NOT EXISTS {table_name} USING fts5(
                {columns_str},
                content='{source_table}',
                content_rowid='rowid'
            )
        """)

    def create_fts_triggers(
        self,
        conn: sqlite3.Connection,
        fts_table: str,
        source_table: str
    ) -> None:
        """Create SQLite triggers to keep FTS in sync."""
        cursor = conn.cursor()

        # After insert trigger
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {source_table}_ai
            AFTER INSERT ON {source_table} BEGIN
                INSERT INTO {fts_table}(id, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END
        """)

        # After delete trigger
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {source_table}_ad
            AFTER DELETE ON {source_table} BEGIN
                INSERT INTO {fts_table}({fts_table}, id, title, content, tags)
                VALUES('delete', old.id, old.title, old.content, old.tags);
            END
        """)

        # After update trigger
        cursor.execute(f"""
            CREATE TRIGGER IF NOT EXISTS {source_table}_au
            AFTER UPDATE ON {source_table} BEGIN
                INSERT INTO {fts_table}({fts_table}, id, title, content, tags)
                VALUES('delete', old.id, old.title, old.content, old.tags);
                INSERT INTO {fts_table}(id, title, content, tags)
                VALUES (new.id, new.title, new.content, new.tags);
            END
        """)

