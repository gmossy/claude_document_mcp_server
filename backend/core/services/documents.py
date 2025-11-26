"""Document service layer for managing documents and their versions.

This module provides the DocumentService class which handles:
- CRUD operations for documents
- Document versioning
- Binary file storage (files stored as-is without parsing or conversion)
- File exports (markdown, txt, code formats only)
- Filename and metadata search capabilities

Note: This is a document library management system. Files are stored as binary
files without text extraction, parsing, or format conversion. The system focuses
on file organization, versioning, and metadata management.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from backend.core.db.base import DatabaseAdapter
# Conversion functions removed - this is a document library, not a converter


def _now_iso() -> str:
    """Get current UTC timestamp in ISO format.

    Returns:
        ISO format timestamp string (e.g., '2024-01-15T12:00:00+00:00')
    """
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
    Service layer for document library management operations.

    Provides CRUD operations, binary file storage, versioning,
    filename search, and metadata management.

    Key Features:
    - Binary file storage: Files stored as-is without parsing or conversion
    - Automatic versioning: New versions created on upload
    - Filename search: Search by filename, title, or metadata
    - Metadata management: Title, tags, status, and custom metadata
    - Export capabilities: Export to markdown, txt, or code formats (no conversion)

    This is a document library, not a document parser or converter.
    Files are stored in versioned directories with metadata tracking.
    """

    db_adapter: DatabaseAdapter
    storage_dir: Path

    def __post_init__(self) -> None:
        """Initialize storage directory after dataclass creation."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _connect(self):
        """Get a database connection using the adapter."""
        return self.db_adapter.connect()

    def connect(self):
        """Get a database connection. Public wrapper for _connect()."""
        return self._connect()

    def _generate_document_id(self) -> str:
        """Generate a unique document ID.

        Uses timestamp and object ID to create a unique identifier
        with format 'doc_<12-char-hex-hash>'.

        Returns:
            Unique document identifier string
        """
        timestamp = _now_iso()
        hash_input = f"{timestamp}{id(timestamp)}"
        short_hash = hashlib.md5(
            hash_input.encode(), usedforsecurity=False
        ).hexdigest()[:12]
        return f"doc_{short_hash}"

    def _content_hash(self, content: str) -> str:
        """Calculate SHA256 hash of content.

        Args:
            content: Text content to hash

        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(content.encode()).hexdigest()

    def content_hash(self, content: str) -> str:
        """Calculate content hash. Public wrapper for _content_hash()."""
        return self._content_hash(content)

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
        placeholder = self.db_adapter.get_parameter_placeholder()

        self.db_adapter.execute(
            conn,
            f"""
            INSERT INTO documents (
                id, title, content, tags, status, metadata,
                created_at, updated_at, size, content_hash
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}
            )
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

        self.db_adapter.execute(
            conn,
            f"""
            INSERT INTO document_versions (
                document_id, version_number, title, content, tags,
                status, metadata, created_at, comment, content_hash
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}
            )
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

        self.db_adapter.commit(conn)
        self.db_adapter.close(conn)

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
        placeholder = self.db_adapter.get_parameter_placeholder()

        cursor = self.db_adapter.execute(
            conn,
            f"SELECT * FROM documents WHERE id = {placeholder}",
            (document_id,)
        )
        doc = self.db_adapter.fetchone(cursor)
        if not doc:
            self.db_adapter.close(conn)
            return None

        doc["tags"] = json.loads(doc["tags"])
        doc["metadata"] = json.loads(doc["metadata"])

        if not include_content:
            doc.pop("content", None)

        if include_versions:
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT version_number, title, created_at, comment, content_hash
                FROM document_versions
                WHERE document_id = {placeholder}
                ORDER BY version_number DESC
                """,
                (document_id,),
            )
            doc["versions"] = self.db_adapter.fetchall(cursor)

        self.db_adapter.close(conn)
        return doc

    def update_document(
        self,
        *,
        document_id: str,
        title: Optional[str] = None,
        content: Optional[str] = None,
        tags: Optional[list[str]] = None,
        status: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
        version_comment: str = "Updated document",
    ) -> dict[str, Any]:
        """
        Update a document with automatic versioning.

        If content changes, creates a new version. Otherwise, updates the
        current document record.

        Args:
            document_id: Unique document identifier
            title: New title (optional)
            content: New content (optional, triggers new version if changed)
            tags: New tags list (optional)
            status: New status (optional)
            metadata: Metadata to merge with existing (optional)
            version_comment: Comment for new version if content changes

        Returns:
            Dictionary with updated document information

        Raises:
            ValueError: If document not found
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Get current document
        cursor = self.db_adapter.execute(
            conn,
            f"SELECT * FROM documents WHERE id = {placeholder}",
            (document_id,)
        )
        current = self.db_adapter.fetchone(cursor)
        if not current:
            self.db_adapter.close(conn)
            raise ValueError(f"Document '{document_id}' not found.")

        # Prepare update values
        new_title = title if title is not None else current["title"]
        new_content = content if content is not None else current["content"]
        new_tags = tags if tags is not None else json.loads(current["tags"])
        new_status = status if status is not None else current["status"]
        
        # Merge metadata
        current_metadata = json.loads(current["metadata"])
        if metadata is not None:
            current_metadata.update(metadata)
        new_metadata = current_metadata

        # Check if content changed (triggers new version)
        content_changed = content is not None and content != current["content"]
        timestamp = _now_iso()
        new_content_hash = self._content_hash(new_content)
        new_size = len(new_content.encode("utf-8"))

        if content_changed:
            # Get next version number
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT MAX(version_number) AS max_version
                FROM document_versions
                WHERE document_id = {placeholder}
                """,
                (document_id,)
            )
            version_row = self.db_adapter.fetchone(cursor)
            next_version = (version_row["max_version"] if version_row and version_row.get("max_version") else 0) + 1

            # Create new version
            self.db_adapter.execute(
                conn,
                f"""
                INSERT INTO document_versions (
                    document_id, version_number, title, content, tags,
                    status, metadata, created_at, comment, content_hash
                )
                VALUES (
                    {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}, {placeholder}, {placeholder},
                    {placeholder}, {placeholder}
                )
                """,
                (
                    document_id,
                    next_version,
                    new_title,
                    new_content,
                    json.dumps(new_tags),
                    new_status,
                    json.dumps(new_metadata),
                    timestamp,
                    version_comment,
                    new_content_hash,
                ),
            )

        # Update main document record
        self.db_adapter.execute(
            conn,
            f"""
            UPDATE documents SET
                title = {placeholder},
                content = {placeholder},
                tags = {placeholder},
                status = {placeholder},
                metadata = {placeholder},
                updated_at = {placeholder},
                size = {placeholder},
                content_hash = {placeholder}
            WHERE id = {placeholder}
            """,
            (
                new_title,
                new_content,
                json.dumps(new_tags),
                new_status,
                json.dumps(new_metadata),
                timestamp,
                new_size,
                new_content_hash,
                document_id,
            ),
        )

        self.db_adapter.commit(conn)
        self.db_adapter.close(conn)

        return {
            "success": True,
            "document_id": document_id,
            "title": new_title,
            "status": new_status,
            "updated_at": timestamp,
            "version_created": content_changed,
            "message": f"Document '{new_title}' updated successfully",
        }

    def get_document_version(
        self,
        *,
        document_id: str,
        version_number: int,
    ) -> Optional[dict[str, Any]]:
        """
        Get a specific version of a document.

        Args:
            document_id: Unique document identifier
            version_number: Version number to retrieve

        Returns:
            Version dictionary or None if not found
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        cursor = self.db_adapter.execute(
            conn,
            f"""
            SELECT * FROM document_versions
            WHERE document_id = {placeholder} AND version_number = {placeholder}
            """,
            (document_id, version_number)
        )
        version = self.db_adapter.fetchone(cursor)
        if not version:
            self.db_adapter.close(conn)
            return None

        version["tags"] = json.loads(version["tags"])
        version["metadata"] = json.loads(version["metadata"])

        self.db_adapter.close(conn)
        return version

    def compare_versions(
        self,
        *,
        document_id: str,
        version_a: int,
        version_b: int,
    ) -> dict[str, Any]:
        """
        Compare two versions of a document.

        Args:
            document_id: Unique document identifier
            version_a: First version number
            version_b: Second version number

        Returns:
            Dictionary with comparison results

        Raises:
            ValueError: If document or versions not found
        """
        version_a_data = self.get_document_version(
            document_id=document_id,
            version_number=version_a
        )
        if not version_a_data:
            raise ValueError(f"Version {version_a} not found for document '{document_id}'")

        version_b_data = self.get_document_version(
            document_id=document_id,
            version_number=version_b
        )
        if not version_b_data:
            raise ValueError(f"Version {version_b} not found for document '{document_id}'")

        content_a = version_a_data["content"]
        content_b = version_b_data["content"]

        # Simple diff calculation
        lines_a = content_a.splitlines()
        lines_b = content_b.splitlines()

        # Calculate basic statistics
        added_lines = len([l for l in lines_b if l not in lines_a])
        removed_lines = len([l for l in lines_a if l not in lines_b])
        changed = content_a != content_b

        return {
            "document_id": document_id,
            "version_a": version_a,
            "version_b": version_b,
            "changed": changed,
            "stats": {
                "lines_added": added_lines,
                "lines_removed": removed_lines,
                "content_length_a": len(content_a),
                "content_length_b": len(content_b),
            },
            "version_a_title": version_a_data["title"],
            "version_b_title": version_b_data["title"],
            "version_a_created": version_a_data["created_at"],
            "version_b_created": version_b_data["created_at"],
        }

    def delete_document(
        self,
        *,
        document_id: str,
        permanent: bool = False,
    ) -> dict[str, Any]:
        """
        Delete or archive a document.

        By default, archives the document (sets status to 'archived').
        Permanent deletion removes the document, all versions, and all stored files.

        Args:
            document_id: Unique document identifier
            permanent: If True, permanently deletes document and all files;
                       if False, archives (sets status to 'archived')

        Returns:
            Dictionary with success status, document_id, title, action, and message

        Example:
            >>> service.delete_document(document_id="doc_123", permanent=False)
            {"success": True, "document_id": "doc_123", "action": "archived", ...}
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Check if document exists
        cursor = self.db_adapter.execute(
            conn,
            f"SELECT title FROM documents WHERE id = {placeholder}",
            (document_id,),
        )
        doc = self.db_adapter.fetchone(cursor)
        if not doc:
            self.db_adapter.close(conn)
            return {
                "success": False,
                "error": f"Document with ID '{document_id}' not found.",
            }

        title = doc["title"]

        if permanent:
            # Permanently delete document, versions, and files
            # Delete binary files
            doc_dir = Path(self.storage_dir) / document_id
            if doc_dir.exists():
                shutil.rmtree(doc_dir, ignore_errors=True)

            # Delete from database
            self.db_adapter.execute(
                conn,
                f"DELETE FROM document_versions WHERE document_id = {placeholder}",
                (document_id,),
            )
            self.db_adapter.execute(
                conn,
                f"DELETE FROM document_files WHERE document_id = {placeholder}",
                (document_id,),
            )
            self.db_adapter.execute(
                conn,
                f"DELETE FROM documents WHERE id = {placeholder}",
                (document_id,),
            )
            action = "permanently deleted"
        else:
            # Archive the document
            timestamp = _now_iso()
            self.db_adapter.execute(
                conn,
                (
                    f"UPDATE documents SET status = 'archived', "
                    f"updated_at = {placeholder} WHERE id = {placeholder}"
                ),
                (timestamp, document_id),
            )
            action = "archived"

        self.db_adapter.commit(conn)
        self.db_adapter.close(conn)

        return {
            "success": True,
            "document_id": document_id,
            "title": title,
            "action": action,
            "message": f"Document '{title}' has been {action}.",
        }

    def list_documents(
        self,
        *,
        status: Optional[str] = None,
        tags: Optional[list[str]] = None,
        category: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> dict[str, Any]:
        """
        List documents with pagination and filtering.

        Args:
            status: Filter by document status (draft/published/archived)
            tags: Filter by tags (documents must have all specified tags)
            category: Filter by metadata.category field
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            order_by: Field to order by (created_at, updated_at, title)
            order_desc: Whether to order descending (default True)

        Returns:
            Dictionary with documents list and total count
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Build WHERE clause
        conditions = []
        params = []

        if status:
            conditions.append(f"status = {placeholder}")
            params.append(status)

        if tags:
            # Filter documents that contain all specified tags
            # Tags are stored as JSON array, so we check each tag
            for tag in tags:
                conditions.append(f"tags LIKE {placeholder}")
                params.append(f'%"{tag}"%')

        if category:
            # Filter by metadata.category field
            # Metadata is stored as JSON, so we check for the category field
            conditions.append(f"metadata LIKE {placeholder}")
            params.append(f'%"category"%"{category}"%')

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        # Validate order_by field
        valid_order_fields = {"created_at", "updated_at", "title", "status"}
        if order_by not in valid_order_fields:
            order_by = "created_at"
        order_direction = "DESC" if order_desc else "ASC"
        
        # Prefix order_by with table alias to avoid ambiguity in JOIN queries
        order_by_prefixed = f"d.{order_by}"

        # Get total count
        cursor = self.db_adapter.execute(
            conn,
            f"SELECT COUNT(*) as total FROM documents WHERE {where_clause}",
            tuple(params),
        )
        total_row = self.db_adapter.fetchone(cursor)
        total = total_row["total"] if total_row else 0

        # Get documents with binary format info (without content for performance)
        cursor = self.db_adapter.execute(
            conn,
            f"""
            SELECT d.id, d.title, d.status, d.tags, d.created_at, d.updated_at, d.size, d.metadata,
                   db.format, db.filename, db.mime_type
            FROM documents d
            LEFT JOIN document_binary db ON d.id = db.document_id
            WHERE {where_clause}
            ORDER BY {order_by_prefixed} {order_direction}
            LIMIT {placeholder} OFFSET {placeholder}
            """,
            tuple(params + [limit, offset]),
        )

        rows = self.db_adapter.fetchall(cursor)
        documents = []
        for row in rows:
            # Parse metadata if it exists
            metadata = {}
            if row.get("metadata"):
                try:
                    metadata = json.loads(row["metadata"])
                except (json.JSONDecodeError, TypeError):
                    metadata = {}
            
            # Build binary info if available
            binary_info = None
            if row.get("format") or row.get("filename"):
                binary_info = {
                    "format": row.get("format", "").lower() if row.get("format") else None,
                    "filename": row.get("filename"),
                    "mime_type": row.get("mime_type")
                }
            
            documents.append(
                {
                    "id": row["id"],
                    "title": row["title"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "size": row["size"],
                    "tags": json.loads(row["tags"]) if row.get("tags") else [],
                    "metadata": metadata,
                    "binary": binary_info,
                }
            )

        self.db_adapter.close(conn)
        return {
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    # ------------------------------------------------------------------ #
    # File exports + tracking
    # ------------------------------------------------------------------ #

    def export_document_file(
        self,
        *,
        document_id: str,
        file_format: str,
        version_number: Optional[int] = None,
        file_name: Optional[str] = None,
        code_extension: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Export a document version to a file on disk.

        Supported formats: markdown, txt, code
        Note: Word (.docx) and PDF (.pdf) conversion are not supported.
        This is a document library, not a document converter.

        Args:
            document_id: Document to export
            file_format: Export format ('markdown', 'txt', or 'code')
            version_number: Specific version (defaults to latest)
            file_name: Custom filename (defaults to document title)
            code_extension: Required for code format (e.g., '.py', '.cpp', '.js')

        Returns:
            Dictionary with path, size, version_number, title, etc.

        Raises:
            ValueError: If document/version not found or format invalid
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Resolve version + content
        if version_number is not None:
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT title, content
                FROM document_versions
                WHERE document_id = {placeholder} AND version_number = {placeholder}
                """,
                (document_id, version_number),
            )
            row = self.db_adapter.fetchone(cursor)
            if not row:
                self.db_adapter.close(conn)
                raise ValueError(
                    f"Version {version_number} not found for document '{document_id}'."
                )
            title = row["title"]
            content = row["content"]
        else:
            cursor = self.db_adapter.execute(
                conn,
                f"SELECT title, content FROM documents WHERE id = {placeholder}",
                (document_id,),
            )
            row = self.db_adapter.fetchone(cursor)
            if not row:
                self.db_adapter.close(conn)
                raise ValueError(f"Document '{document_id}' not found.")
            title = row["title"]
            content = row["content"]
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT MAX(version_number) AS v
                FROM document_versions
                WHERE document_id = {placeholder}
                """,
                (document_id,),
            )
            version_row = self.db_adapter.fetchone(cursor)
            version_number = version_row["v"] if version_row and version_row["v"] else 1

        safe_title = _sanitize_filename(file_name or title or document_id)
        if file_format == "markdown":
            ext = ".md"
        elif file_format == "txt":
            ext = ".txt"
        elif file_format == "code":
            if not code_extension:
                self.db_adapter.close(conn)
                raise ValueError("code_extension is required when file_format='code'.")
            ext = (
                code_extension
                if code_extension.startswith(".")
                else f".{code_extension}"
            )
        else:
            self.db_adapter.close(conn)
            raise ValueError(
                f"Unsupported format: {file_format}. "
                "Only 'markdown', 'txt', and 'code' formats are supported "
                "(no conversion to Word/PDF)."
            )

        version_dir = Path(self.storage_dir) / document_id / f"v{version_number}"
        version_dir.mkdir(parents=True, exist_ok=True)
        file_path = version_dir / f"{safe_title}{ext}"

        # Only write text formats - no conversion
        file_path.write_text(content, encoding="utf-8")

        size = file_path.stat().st_size
        created_at = _now_iso()

        self.db_adapter.execute(
            conn,
            f"""
            INSERT INTO document_files (
                document_id, version_number, format, path, size, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                document_id,
                version_number,
                file_format,
                str(file_path),
                size,
                created_at,
            ),
        )
        self.db_adapter.commit(conn)

        self.db_adapter.close(conn)
        return {
            "success": True,
            "document_id": document_id,
            "version_number": version_number,
            "format": file_format,
            "path": str(file_path),
            "size": size,
            "created_at": created_at,
            "message": f"Exported v{version_number} of '{title}' to {file_path}",
        }

    def create_document_file(
        self,
        *,
        document_id: str,
        file_format: str,
        version_number: Optional[int] = None,
        file_name: Optional[str] = None,
        excel_data: Optional[list[list[str]]] = None,
    ) -> dict[str, Any]:
        """
        Create a Word, PDF, or Excel document from a stored document.

        This method creates formatted documents (Word, PDF, Excel) from text content
        stored in the document library. This is separate from binary file storage -
        it generates new formatted documents from text content.

        Args:
            document_id: Document to convert
            file_format: Output format ('docx', 'pdf', or 'xlsx')
            version_number: Specific version to use (defaults to latest)
            file_name: Custom filename (defaults to document title)
            excel_data: For Excel format, provide list of rows (list of lists).
                       If None, converts document content to a single column.

        Returns:
            Dictionary with path, size, version_number, title, etc.

        Raises:
            ValueError: If document/version not found or format invalid
            ImportError: If required libraries not installed
        """
        try:
            from backend.mcp_document_server.document_parsers import (
                create_pdf_from_text,
                create_docx_from_text,
                create_excel_from_data,
                DocumentParseError,
                UnsupportedFormatError,
            )
        except ImportError as exc:
            raise ValueError(
                "Document creation functions not available. "
                "Install required packages: python-docx, reportlab, openpyxl"
            ) from exc

        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Resolve version + content
        if version_number is not None:
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT title, content
                FROM document_versions
                WHERE document_id = {placeholder} AND version_number = {placeholder}
                """,
                (document_id, version_number),
            )
            row = self.db_adapter.fetchone(cursor)
            if not row:
                self.db_adapter.close(conn)
                raise ValueError(
                    f"Version {version_number} not found for document '{document_id}'."
                )
            title = row["title"]
            content = row["content"]
        else:
            cursor = self.db_adapter.execute(
                conn,
                f"SELECT title, content FROM documents WHERE id = {placeholder}",
                (document_id,),
            )
            row = self.db_adapter.fetchone(cursor)
            if not row:
                self.db_adapter.close(conn)
                raise ValueError(f"Document '{document_id}' not found.")
            title = row["title"]
            content = row["content"]
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT MAX(version_number) AS v
                FROM document_versions
                WHERE document_id = {placeholder}
                """,
                (document_id,),
            )
            version_row = self.db_adapter.fetchone(cursor)
            version_number = version_row["v"] if version_row and version_row["v"] else 1

        self.db_adapter.close(conn)

        safe_title = _sanitize_filename(file_name or title or document_id)
        version_dir = Path(self.storage_dir) / document_id / f"v{version_number}"
        version_dir.mkdir(parents=True, exist_ok=True)

        if file_format == "docx":
            output_path = version_dir / f"{safe_title}.docx"
            try:
                create_docx_from_text(content, output_path, title)
            except (UnsupportedFormatError, DocumentParseError) as e:
                raise ValueError(f"Failed to create Word document: {str(e)}") from e
        elif file_format == "pdf":
            output_path = version_dir / f"{safe_title}.pdf"
            try:
                create_pdf_from_text(content, output_path, title)
            except (UnsupportedFormatError, DocumentParseError) as e:
                raise ValueError(f"Failed to create PDF: {str(e)}") from e
        elif file_format == "xlsx":
            output_path = version_dir / f"{safe_title}.xlsx"
            # Convert content to Excel data if not provided
            if excel_data is None:
                # Split content into rows (by newlines) and columns (by tabs or commas)
                lines = content.split("\n")
                excel_data = []
                for line in lines:
                    if line.strip():
                        # Try splitting by tab first, then comma
                        if "\t" in line:
                            excel_data.append(line.split("\t"))
                        elif "," in line:
                            excel_data.append(line.split(","))
                        else:
                            excel_data.append([line])
            try:
                create_excel_from_data(excel_data, output_path, "Sheet1", title)
            except (UnsupportedFormatError, DocumentParseError) as e:
                raise ValueError(
                    f"Failed to create Excel document: {str(e)}"
                ) from e
        else:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                "Supported formats: 'docx', 'pdf', 'xlsx'"
            )

        file_size = output_path.stat().st_size

        return {
            "success": True,
            "document_id": document_id,
            "version_number": version_number,
            "title": title,
            "file_path": str(output_path),
            "file_size": file_size,
            "format": file_format,
            "message": f"Created {file_format.upper()} document: {output_path.name}",
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

        Args:
            document_id: Document identifier
            version_number: Version number for this binary file
            filename: Original filename
            mime_type: MIME type of the file
            file_format: File format extension
            content_bytes: Binary content of the file

        Returns:
            Size of stored file in bytes
        """
        checksum = hashlib.sha256(content_bytes).hexdigest()
        size = len(content_bytes)
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # For binary data, use bytes directly (adapter handles SQLite.Binary if needed)
        # PostgreSQL will use bytea type
        self.db_adapter.execute(
            conn,
            f"""
            INSERT INTO document_binary (
                document_id, version_number, filename, mime_type, format,
                content_blob, size_bytes, checksum, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}
            )
            """,
            (
                document_id,
                version_number,
                filename,
                mime_type,
                file_format,
                content_bytes,
                size,
                checksum,
                _now_iso(),
            ),
        )
        self.db_adapter.commit(conn)
        self.db_adapter.close(conn)
        return size

    def get_binary_file(
        self,
        *,
        document_id: str,
        version_number: Optional[int] = None,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve binary file content for a document.

        Args:
            document_id: Document identifier
            version_number: Specific version to retrieve (defaults to latest)

        Returns:
            Dictionary with filename, mime_type, format, and content_bytes, or None if not found
        """
        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        if version_number:
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT filename, mime_type, format, content_blob, size_bytes
                FROM document_binary
                WHERE document_id = {placeholder} AND version_number = {placeholder}
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (document_id, version_number),
            )
        else:
            # Get latest version
            cursor = self.db_adapter.execute(
                conn,
                f"""
                SELECT filename, mime_type, format, content_blob, size_bytes
                FROM document_binary
                WHERE document_id = {placeholder}
                ORDER BY version_number DESC
                LIMIT 1
                """,
                (document_id,),
            )

        row = self.db_adapter.fetchone(cursor)
        self.db_adapter.close(conn)

        if not row:
            return None

        return {
            "filename": row["filename"],
            "mime_type": row["mime_type"],
            "format": row["format"],
            "content_bytes": row["content_blob"],
            "size_bytes": row["size_bytes"],
        }

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
        Create a document from an uploaded binary file.

        Stores the file as-is without parsing or conversion. The file is saved
        in a versioned directory structure. Supports all file formats including
        Word (.docx), Excel (.xlsx), PDF (.pdf), OpenUSD (.usd, .usda, .usdc),
        code files, markdown, and any other format.

        Args:
            title: Document title (often derived from filename)
            extracted_text: Placeholder text (filename is typically used)
            tags: List of tags for organization
            status: Document status (draft, published, archived)
            metadata: Optional metadata dictionary
            filename: Original filename
            mime_type: MIME type of the file
            file_format: File format/extension (e.g., 'docx', 'pdf', 'xlsx')
            content_bytes: Binary file content

        Returns:
            Dictionary with document_id, version, and metadata

        Note:
            Files are stored as binary without text extraction or parsing.
            This is a document library, not a document parser.

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

    def search_by_filename(
        self, filename_query: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        """
        Search for documents by filename, title, or metadata.

        Searches across:
        - Document titles (which often match filenames)
        - Stored filenames in document_binary table
        - Metadata fields

        This is the primary search method for finding files in the document library.

        Args:
            filename_query: Filename, partial filename, or search term
            limit: Maximum number of results to return (default: 50)

        Returns:
            List of matching documents with metadata (document_id, title, status,
            tags, created_at, updated_at, size)

        Example:
            >>> service.search_by_filename("report.pdf", limit=10)
            [{"document_id": "doc_123", "title": "report.pdf", ...}]
        """
        query = filename_query.strip()
        if not query:
            return []

        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Search in titles (which often match filenames) and metadata
        # Also check document_binary table for stored filenames
        search_pattern = f"%{query}%"
        cursor = self.db_adapter.execute(
            conn,
            f"""
            SELECT DISTINCT d.id AS document_id,
                   d.title,
                   d.status,
                   d.tags,
                   d.created_at,
                   d.updated_at,
                   d.size
            FROM documents d
            LEFT JOIN document_binary db ON d.id = db.document_id
            WHERE d.title LIKE {placeholder}
               OR db.filename LIKE {placeholder}
               OR d.metadata LIKE {placeholder}
            ORDER BY d.updated_at DESC
            LIMIT {placeholder}
            """,
            (search_pattern, search_pattern, search_pattern, limit),
        )
        rows = self.db_adapter.fetchall(cursor)
        self.db_adapter.close(conn)

        results: list[dict[str, Any]] = []
        for row in rows:
            results.append(
                {
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "status": row["status"],
                    "tags": json.loads(row["tags"]),
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "size": row["size"],
                }
            )
        return results

    def semantic_search(
        self, query: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        """
        Perform full-text semantic search on documents.

        Uses SQLite FTS5 for text matching with snippet highlighting.
        Also searches by filename if query looks like a filename.

        Args:
            query: Search query string
            limit: Maximum number of results

        Returns:
            List of matching documents with snippets
        """
        query = query.strip()
        if not query:
            return []

        # If query looks like a filename (has extension or contains dots/slashes),
        # also search by filename
        if "." in query or "/" in query or "\\" in query:
            filename_results = self.search_by_filename(query, limit)
            if filename_results:
                return filename_results[:limit]

        terms = query.split()
        fts_query = " ".join(f'"{term}"*' for term in terms) or query

        conn = self._connect()
        placeholder = self.db_adapter.get_parameter_placeholder()

        # Note: FTS syntax is database-specific
        # SQLite uses FTS5, PostgreSQL uses tsvector
        # This implementation assumes SQLite FTS5 for now
        # PostgreSQL adapter should override semantic_search or provide FTS method
        cursor = self.db_adapter.execute(
            conn,
            f"""
            SELECT d.id AS document_id,
                   d.title,
                   d.status,
                   d.tags,
                   snippet(
                       documents_fts, 2, '<b>', '</b>', ' … ', 10
                   ) AS snippet
            FROM documents_fts
            JOIN documents d ON d.rowid = documents_fts.rowid
            WHERE documents_fts MATCH {placeholder}
            LIMIT {placeholder}
            """,
            (fts_query, limit),
        )
        rows = self.db_adapter.fetchall(cursor)
        self.db_adapter.close(conn)

        results: list[dict[str, Any]] = []
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

