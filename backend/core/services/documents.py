from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List

from backend.mcp_document_server.document_parsers import (
    create_docx_from_text,
    create_pdf_from_text,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sanitize_filename(name: str, default: str = "document") -> str:
    """Sanitize a filename by removing invalid characters."""
    safe_chars = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_"
        for c in (name or default)
    )
    base = "_".join(safe_chars.split())
    return base or default


@dataclass
class DocumentService:
    """
    Service layer for document management operations.

    Provides CRUD operations, file exports, binary storage,
    and semantic search capabilities.
    """

    db_path: Path
    storage_dir: Path

    def __post_init__(self) -> None:
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _generate_document_id(self) -> str:
        timestamp = _now_iso()
        hash_input = f"{timestamp}{id(timestamp)}"
        short_hash = hashlib.md5(hash_input.encode(), usedforsecurity=False).hexdigest()[:12]
        return f"doc_{short_hash}"

    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()

    # ------------------------------------------------------------------ #
    # CRUD helpers
    # ------------------------------------------------------------------ #

    def create_document(
        self,
        *,
        title: str,
        content: str,
        tags: list[str],
        status: str,
        metadata: Optional[dict[str, Any]] = None,
        version_comment: str = "Initial version",
    ) -> dict[str, Any]:
        """
        Create a new document with automatic versioning.

        Args:
            title: Document title
            content: Document content (text/markdown)
            tags: List of tags for categorization
            status: Document status (draft/published/archived)
            metadata: Optional metadata dictionary
            version_comment: Comment for initial version

        Returns:
            Dictionary with document_id, title, status, created_at, etc.
        """
        metadata = metadata or {}
        document_id = self._generate_document_id()
        timestamp = _now_iso()
        content_hash = self._content_hash(content)
        size = len(content.encode("utf-8"))

        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO documents (
                id, title, content, tags, status, metadata,
                created_at, updated_at, size, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                title,
                content,
                json.dumps(tags),
                status,
                json.dumps(metadata),
                timestamp,
                timestamp,
                size,
                content_hash,
            ),
        )

        cursor.execute(
            """
            INSERT INTO document_versions (
                document_id, version_number, title, content, tags,
                status, metadata, created_at, comment, content_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                1,
                title,
                content,
                json.dumps(tags),
                status,
                json.dumps(metadata),
                timestamp,
                version_comment,
                content_hash,
            ),
        )

        conn.commit()
        conn.close()

        return {
            "success": True,
            "document_id": document_id,
            "title": title,
            "status": status,
            "created_at": timestamp,
            "size": size,
            "tags": tags,
            "version": 1,
            "message": f"Document '{title}' created successfully with ID {document_id}",
        }

    def get_document(
        self,
        *,
        document_id: str,
        include_content: bool = True,
        include_versions: bool = False,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve a document by ID.

        Args:
            document_id: Unique document identifier
            include_content: Whether to include full content
            include_versions: Whether to include version history

        Returns:
            Document dictionary or None if not found
        """
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM documents WHERE id = ?", (document_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        doc = dict(row)
        doc["tags"] = json.loads(doc["tags"])
        doc["metadata"] = json.loads(doc["metadata"])

        if not include_content:
            doc.pop("content", None)

        if include_versions:
            cursor.execute(
                """
                SELECT version_number, title, created_at, comment, content_hash
                FROM document_versions
                WHERE document_id = ?
                ORDER BY version_number DESC
                """,
                (document_id,),
            )
            doc["versions"] = [dict(v) for v in cursor.fetchall()]

        conn.close()
        return doc

    # ------------------------------------------------------------------ #
    # File exports + tracking
    # ------------------------------------------------------------------ #

    def export_document_file(
        self,
        *,
        document_id: str,
        format: str,
        version_number: Optional[int] = None,
        file_name: Optional[str] = None,
        code_extension: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Export a document version to a file on disk.

        Supported formats: markdown, txt, docx, pdf, code

        Args:
            document_id: Document to export
            format: Export format
            version_number: Specific version (defaults to latest)
            file_name: Custom filename (defaults to document title)
            code_extension: Required for code format (e.g., .py, .cpp)

        Returns:
            Dictionary with path, size, version_number, etc.

        Raises:
            ValueError: If document/version not found or format invalid
        """
        conn = self._connect()
        cursor = conn.cursor()

        # Resolve version + content
        if version_number is not None:
            cursor.execute(
                """
                SELECT title, content
                FROM document_versions
                WHERE document_id = ? AND version_number = ?
                """,
                (document_id, version_number),
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise ValueError(f"Version {version_number} not found for document '{document_id}'.")
            title = row["title"]
            content = row["content"]
        else:
            cursor.execute(
                "SELECT title, content FROM documents WHERE id = ?",
                (document_id,),
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                raise ValueError(f"Document '{document_id}' not found.")
            title = row["title"]
            content = row["content"]
            cursor.execute(
                """
                SELECT MAX(version_number) AS v
                FROM document_versions
                WHERE document_id = ?
                """,
                (document_id,),
            )
            version_number = cursor.fetchone()["v"] or 1

        safe_title = _sanitize_filename(file_name or title or document_id)
        if format == "markdown":
            ext = ".md"
        elif format == "txt":
            ext = ".txt"
        elif format == "docx":
            ext = ".docx"
        elif format == "pdf":
            ext = ".pdf"
        elif format == "code":
            if not code_extension:
                conn.close()
                raise ValueError("code_extension is required when format='code'.")
            ext = (
                code_extension
                if code_extension.startswith(".")
                else f".{code_extension}"
            )
        else:
            conn.close()
            raise ValueError(f"Unsupported format: {format}")

        version_dir = Path(self.storage_dir) / document_id / f"v{version_number}"
        version_dir.mkdir(parents=True, exist_ok=True)
        file_path = version_dir / f"{safe_title}{ext}"

        if format in {"markdown", "txt", "code"}:
            file_path.write_text(content, encoding="utf-8")
        elif format == "docx":
            create_docx_from_text(content, file_path, title)
        elif format == "pdf":
            create_pdf_from_text(content, file_path, title)

        size = file_path.stat().st_size
        created_at = _now_iso()

        cursor.execute(
            """
            INSERT INTO document_files (document_id, version_number, format, path, size, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (document_id, version_number, format, str(file_path), size, created_at),
        )
        conn.commit()

        conn.close()
        return {
            "success": True,
            "document_id": document_id,
            "version_number": version_number,
            "format": format,
            "path": str(file_path),
            "size": size,
            "created_at": created_at,
            "message": f"Exported v{version_number} of '{title}' to {file_path}",
        }

    def _store_binary_file(
        self,
        *,
        document_id: str,
        version_number: int,
        filename: str,
        mime_type: str,
        file_format: str,
        content_bytes: bytes,
    ) -> int:
        """
        Store binary file content in document_binary table.

        Returns:
            Size of stored file in bytes
        """
        checksum = hashlib.sha256(content_bytes).hexdigest()
        size = len(content_bytes)
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO document_binary (
                document_id, version_number, filename, mime_type, format,
                content_blob, size_bytes, checksum, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                document_id,
                version_number,
                filename,
                mime_type,
                file_format,
                sqlite3.Binary(content_bytes),
                size,
                checksum,
                _now_iso(),
            ),
        )
        conn.commit()
        conn.close()
        return size

    def create_document_from_upload(
        self,
        *,
        title: str,
        extracted_text: str,
        tags: list[str],
        status: str,
        metadata: Optional[dict[str, Any]],
        filename: str,
        mime_type: str,
        file_format: str,
        content_bytes: bytes,
    ) -> dict[str, Any]:
        """
        Create a document from an uploaded file.

        Extracts text, creates document record, and stores binary file.

        Returns:
            Document creation result with binary file metadata
        """
        metadata = metadata or {}
        result = self.create_document(
            title=title,
            content=extracted_text,
            tags=tags,
            status=status,
            metadata=metadata,
        )
        document_id = result["document_id"]
        version_number = result.get("version", 1)
        size_bytes = self._store_binary_file(
            document_id=document_id,
            version_number=version_number,
            filename=filename,
            mime_type=mime_type,
            file_format=file_format,
            content_bytes=content_bytes,
        )
        result["binary"] = {
            "filename": filename,
            "mime_type": mime_type,
            "format": file_format,
            "size_bytes": size_bytes,
        }
        return result

    # ------------------------------------------------------------------ #
    # Semantic search (FTS-backed placeholder)
    # ------------------------------------------------------------------ #

    def semantic_search(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform full-text semantic search on documents.

        Uses SQLite FTS5 for text matching with snippet highlighting.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching documents with snippets
        """
        query = query.strip()
        if not query:
            return []

        terms = query.split()
        fts_query = " ".join(f'"{term}"*' for term in terms) or query

        conn = self._connect()
        cursor = conn.cursor()
            cursor.execute(
                """
                SELECT d.id AS document_id,
                       d.title,
                       d.status,
                       d.tags,
                       snippet(
                           documents_fts, 2, '<b>', '</b>', ' … ', 10
                       ) AS snippet
                FROM documents_fts
                JOIN documents d ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?
                LIMIT ?
                """,
            (fts_query, limit),
        )
        rows = cursor.fetchall()
        conn.close()

        results: List[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "status": row["status"],
                    "tags": json.loads(row["tags"]),
                    "snippet": row["snippet"],
                }
            )
        return results

