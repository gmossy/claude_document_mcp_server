#!/usr/bin/env python3
"""
Document Management MCP Server

A comprehensive MCP server for document management with features including:
- Document CRUD operations with versioning
- Full-text search with highlighting
- Tagging and categorization
- Content analysis and summarization
- Export to multiple formats
- Batch operations
"""

import json
import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from enum import Enum
from contextlib import asynccontextmanager

from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel, Field, field_validator, ConfigDict

# ============================================================================
# Constants
# ============================================================================

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
DATABASE_PATH = SCRIPT_DIR / "documents.db"
DOCUMENTS_DIR = SCRIPT_DIR / "document_storage"
MAX_CONTENT_SIZE = 10 * 1024 * 1024  # 10MB
MAX_TAGS = 50
MAX_TITLE_LENGTH = 500
MAX_SEARCH_RESULTS = 100
DEFAULT_PAGE_SIZE = 20

# ============================================================================
# Enums
# ============================================================================


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class DocumentStatus(str, Enum):
    """Document lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class SortOrder(str, Enum):
    """Sort order for listings."""
    ASC = "asc"
    DESC = "desc"


class SortField(str, Enum):
    """Fields to sort by."""
    TITLE = "title"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    SIZE = "size"


# ============================================================================
# Pydantic Input Models
# ============================================================================


class CreateDocumentInput(BaseModel):
    """Input for creating a new document."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    title: str = Field(
        ...,
        description="Document title (e.g., 'Q3 Financial Report', 'Meeting Notes 2024-01-15')",
        min_length=1,
        max_length=MAX_TITLE_LENGTH
    )
    content: str = Field(
        ...,
        description="Document content in plain text or markdown format",
        min_length=1,
        max_length=MAX_CONTENT_SIZE
    )
    tags: Optional[list[str]] = Field(
        default_factory=list,
        description="List of tags for categorization (e.g., ['finance', 'quarterly', 'report'])",
        max_length=MAX_TAGS
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.DRAFT,
        description="Initial status: 'draft', 'published', or 'archived'"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description="Additional metadata as key-value pairs (e.g., {'author': 'John', 'department': 'Engineering'})"
    )
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if v:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return []


class GetDocumentInput(BaseModel):
    """Input for retrieving a document."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier (e.g., 'doc_abc123')",
        min_length=1,
        max_length=100
    )
    include_content: bool = Field(
        default=True,
        description="Whether to include the full document content"
    )
    include_versions: bool = Field(
        default=False,
        description="Whether to include version history"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' for human-readable or 'json' for structured data"
    )


class UpdateDocumentInput(BaseModel):
    """Input for updating a document."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    title: Optional[str] = Field(
        default=None,
        description="New title (leave empty to keep current)",
        max_length=MAX_TITLE_LENGTH
    )
    content: Optional[str] = Field(
        default=None,
        description="New content (creates a new version)",
        max_length=MAX_CONTENT_SIZE
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="New tags (replaces existing tags)",
        max_length=MAX_TAGS
    )
    status: Optional[DocumentStatus] = Field(
        default=None,
        description="New status"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default=None,
        description="New metadata (merges with existing)"
    )
    version_comment: str = Field(
        default="",
        description="Comment describing this version change",
        max_length=500
    )
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v


class DeleteDocumentInput(BaseModel):
    """Input for deleting a document."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    permanent: bool = Field(
        default=False,
        description="If True, permanently deletes; if False, archives the document"
    )


class SearchDocumentsInput(BaseModel):
    """Input for searching documents."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    query: Optional[str] = Field(
        default=None,
        description="Full-text search query (searches title and content)",
        max_length=500
    )
    tags: Optional[list[str]] = Field(
        default=None,
        description="Filter by tags (documents must have ALL specified tags)",
        max_length=MAX_TAGS
    )
    status: Optional[DocumentStatus] = Field(
        default=None,
        description="Filter by status"
    )
    created_after: Optional[str] = Field(
        default=None,
        description="Filter documents created after this date (ISO format: '2024-01-15T00:00:00Z')"
    )
    created_before: Optional[str] = Field(
        default=None,
        description="Filter documents created before this date"
    )
    sort_by: SortField = Field(
        default=SortField.UPDATED_AT,
        description="Field to sort results by"
    )
    sort_order: SortOrder = Field(
        default=SortOrder.DESC,
        description="Sort order: 'asc' or 'desc'"
    )
    limit: int = Field(
        default=DEFAULT_PAGE_SIZE,
        description="Maximum number of results to return",
        ge=1,
        le=MAX_SEARCH_RESULTS
    )
    offset: int = Field(
        default=0,
        description="Number of results to skip for pagination",
        ge=0
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )
    
    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v


class ListTagsInput(BaseModel):
    """Input for listing all tags."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    sort_by_count: bool = Field(
        default=True,
        description="If True, sort by usage count; if False, sort alphabetically"
    )
    min_count: int = Field(
        default=1,
        description="Minimum usage count to include tag",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class GetDocumentVersionInput(BaseModel):
    """Input for retrieving a specific document version."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    version_number: int = Field(
        ...,
        description="Version number to retrieve (1 is the first version)",
        ge=1
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class CompareVersionsInput(BaseModel):
    """Input for comparing two document versions."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    version_a: int = Field(
        ...,
        description="First version number to compare",
        ge=1
    )
    version_b: int = Field(
        ...,
        description="Second version number to compare",
        ge=1
    )


class AnalyzeDocumentInput(BaseModel):
    """Input for analyzing document content."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    include_stats: bool = Field(
        default=True,
        description="Include word count, character count, reading time"
    )
    include_keywords: bool = Field(
        default=True,
        description="Extract top keywords from content"
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


class ExportDocumentInput(BaseModel):
    """Input for exporting a document."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100
    )
    format: str = Field(
        default="markdown",
        description="Export format: 'markdown', 'html', 'json', or 'txt'",
        pattern=r"^(markdown|html|json|txt)$"
    )
    include_metadata: bool = Field(
        default=True,
        description="Include document metadata in export"
    )


class BulkTagInput(BaseModel):
    """Input for bulk tagging operations."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    document_ids: list[str] = Field(
        ...,
        description="List of document IDs to tag",
        min_length=1,
        max_length=100
    )
    add_tags: Optional[list[str]] = Field(
        default=None,
        description="Tags to add to all specified documents",
        max_length=MAX_TAGS
    )
    remove_tags: Optional[list[str]] = Field(
        default=None,
        description="Tags to remove from all specified documents",
        max_length=MAX_TAGS
    )
    
    @field_validator("add_tags", "remove_tags")
    @classmethod
    def validate_tags(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            return [tag.lower().strip() for tag in v if tag.strip()]
        return v


class GetStatisticsInput(BaseModel):
    """Input for getting document statistics."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")
    
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format"
    )


# ============================================================================
# Database Management
# ============================================================================


def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'draft',
            metadata TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            size INTEGER NOT NULL,
            content_hash TEXT NOT NULL
        )
    """)
    
    # Versions table for version history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS document_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id TEXT NOT NULL,
            version_number INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT NOT NULL,
            status TEXT NOT NULL,
            metadata TEXT NOT NULL,
            created_at TEXT NOT NULL,
            comment TEXT NOT NULL DEFAULT '',
            content_hash TEXT NOT NULL,
            FOREIGN KEY (document_id) REFERENCES documents(id),
            UNIQUE(document_id, version_number)
        )
    """)
    
    # Full-text search index
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
            id,
            title,
            content,
            tags,
            content='documents',
            content_rowid='rowid'
        )
    """)
    
    # Triggers to keep FTS in sync
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
            INSERT INTO documents_fts(id, title, content, tags) 
            VALUES (new.id, new.title, new.content, new.tags);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, id, title, content, tags) 
            VALUES('delete', old.id, old.title, old.content, old.tags);
        END
    """)
    
    cursor.execute("""
        CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
            INSERT INTO documents_fts(documents_fts, id, title, content, tags) 
            VALUES('delete', old.id, old.title, old.content, old.tags);
            INSERT INTO documents_fts(id, title, content, tags) 
            VALUES (new.id, new.title, new.content, new.tags);
        END
    """)
    
    conn.commit()
    conn.close()


def get_db_connection():
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================================
# Helper Functions
# ============================================================================


def generate_document_id() -> str:
    """Generate a unique document ID."""
    timestamp = datetime.now(timezone.utc).isoformat()
    hash_input = f"{timestamp}{id(timestamp)}"
    short_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
    return f"doc_{short_hash}"


def calculate_content_hash(content: str) -> str:
    """Calculate SHA-256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()


def get_current_timestamp() -> str:
    """Get current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def format_timestamp(iso_timestamp: str) -> str:
    """Format ISO timestamp to human-readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
    except (ValueError, AttributeError):
        return iso_timestamp


def calculate_reading_time(content: str) -> int:
    """Calculate estimated reading time in minutes (200 words/min)."""
    word_count = len(content.split())
    return max(1, round(word_count / 200))


def extract_keywords(content: str, top_n: int = 10) -> list[str]:
    """Extract top keywords from content."""
    # Simple keyword extraction based on word frequency
    words = content.lower().split()
    # Filter out common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'shall', 'can', 'need', 'dare', 'ought',
        'used', 'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them',
        'their', 'what', 'which', 'who', 'whom', 'whose', 'where', 'when', 'why',
        'how', 'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
        'some', 'such', 'no', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'also'
    }
    
    # Count word frequencies
    word_freq: dict[str, int] = {}
    for word in words:
        # Clean word
        clean_word = ''.join(c for c in word if c.isalnum())
        if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
    
    # Sort by frequency and return top N
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, _ in sorted_words[:top_n]]


def format_document_markdown(doc: dict, include_content: bool = True, include_versions: bool = False) -> str:
    """Format a document as Markdown."""
    lines = [
        f"# {doc['title']}",
        "",
        f"**ID**: `{doc['id']}`",
        f"**Status**: {doc['status']}",
        f"**Created**: {format_timestamp(doc['created_at'])}",
        f"**Last Updated**: {format_timestamp(doc['updated_at'])}",
        f"**Size**: {doc['size']:,} bytes",
    ]
    
    tags = json.loads(doc['tags']) if isinstance(doc['tags'], str) else doc['tags']
    if tags:
        lines.append(f"**Tags**: {', '.join(tags)}")
    
    metadata = json.loads(doc['metadata']) if isinstance(doc['metadata'], str) else doc['metadata']
    if metadata:
        lines.append("")
        lines.append("## Metadata")
        for key, value in metadata.items():
            lines.append(f"- **{key}**: {value}")
    
    if include_content:
        lines.append("")
        lines.append("## Content")
        lines.append("")
        lines.append(doc['content'])
    
    if include_versions and 'versions' in doc:
        lines.append("")
        lines.append("## Version History")
        for ver in doc['versions']:
            lines.append(f"- **v{ver['version_number']}** ({format_timestamp(ver['created_at'])})")
            if ver['comment']:
                lines.append(f"  - {ver['comment']}")
    
    return "\n".join(lines)


def format_search_results_markdown(results: list[dict], total: int, offset: int) -> str:
    """Format search results as Markdown."""
    lines = [
        f"# Search Results",
        "",
        f"Found **{total}** documents (showing {offset + 1}-{offset + len(results)})",
        ""
    ]
    
    for i, doc in enumerate(results, 1):
        tags = json.loads(doc['tags']) if isinstance(doc['tags'], str) else doc['tags']
        tag_str = f" • Tags: {', '.join(tags)}" if tags else ""
        lines.append(f"### {i}. {doc['title']}")
        lines.append(f"ID: `{doc['id']}` • Status: {doc['status']} • Updated: {format_timestamp(doc['updated_at'])}{tag_str}")
        
        # Show content preview (first 200 chars)
        preview = doc['content'][:200].replace('\n', ' ')
        if len(doc['content']) > 200:
            preview += "..."
        lines.append(f"> {preview}")
        lines.append("")
    
    return "\n".join(lines)


# ============================================================================
# Lifespan Management
# ============================================================================


@asynccontextmanager
async def app_lifespan(app):
    """Manage application lifecycle."""
    # Initialize database and storage
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    init_database()
    
    yield {}


# ============================================================================
# MCP Server Initialization
# ============================================================================

mcp = FastMCP("document_mcp", lifespan=app_lifespan)


# ============================================================================
# Tool Implementations
# ============================================================================


@mcp.tool(
    name="document_create",
    annotations={
        "title": "Create Document",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def document_create(params: CreateDocumentInput) -> str:
    """Create a new document with title, content, tags, and metadata.
    
    Creates a document in the document management system with automatic versioning.
    The first version is automatically created upon document creation.
    
    Args:
        params (CreateDocumentInput): Input parameters containing:
            - title (str): Document title
            - content (str): Document content in text or markdown
            - tags (Optional[List[str]]): Tags for categorization
            - status (DocumentStatus): Initial status (draft/published/archived)
            - metadata (Optional[Dict]): Additional key-value metadata
    
    Returns:
        str: JSON response containing:
            {
                "success": bool,
                "document_id": str,
                "title": str,
                "status": str,
                "created_at": str,
                "size": int,
                "tags": List[str],
                "version": int,
                "message": str
            }
    """
    try:
        doc_id = generate_document_id()
        timestamp = get_current_timestamp()
        content_hash = calculate_content_hash(params.content)
        size = len(params.content.encode('utf-8'))
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insert document
        cursor.execute("""
            INSERT INTO documents (id, title, content, tags, status, metadata, created_at, updated_at, size, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            params.title,
            params.content,
            json.dumps(params.tags),
            params.status.value,
            json.dumps(params.metadata),
            timestamp,
            timestamp,
            size,
            content_hash
        ))
        
        # Create initial version
        cursor.execute("""
            INSERT INTO document_versions (document_id, version_number, title, content, tags, status, metadata, created_at, comment, content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            1,
            params.title,
            params.content,
            json.dumps(params.tags),
            params.status.value,
            json.dumps(params.metadata),
            timestamp,
            "Initial version",
            content_hash
        ))
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "success": True,
            "document_id": doc_id,
            "title": params.title,
            "status": params.status.value,
            "created_at": timestamp,
            "size": size,
            "tags": params.tags,
            "version": 1,
            "message": f"Document '{params.title}' created successfully with ID {doc_id}"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to create document: {str(e)}",
            "suggestion": "Please check your input parameters and try again."
        }, indent=2)


@mcp.tool(
    name="document_get",
    annotations={
        "title": "Get Document",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_get(params: GetDocumentInput) -> str:
    """Retrieve a document by its ID with optional version history.
    
    Fetches complete document information including content, metadata, tags,
    and optionally the full version history.
    
    Args:
        params (GetDocumentInput): Input parameters containing:
            - document_id (str): Unique document identifier
            - include_content (bool): Include full content in response
            - include_versions (bool): Include version history
            - response_format (ResponseFormat): Output format (markdown/json)
    
    Returns:
        str: Document data in requested format. JSON format includes:
            {
                "id": str,
                "title": str,
                "content": str (if include_content),
                "tags": List[str],
                "status": str,
                "metadata": Dict,
                "created_at": str,
                "updated_at": str,
                "size": int,
                "versions": List[Dict] (if include_versions)
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (params.document_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Document with ID '{params.document_id}' not found.",
                "suggestion": "Please verify the document ID and try again. Use document_search to find documents."
            }, indent=2)
        
        doc = dict(row)
        
        if params.include_versions:
            cursor.execute("""
                SELECT version_number, title, created_at, comment, content_hash
                FROM document_versions
                WHERE document_id = ?
                ORDER BY version_number DESC
            """, (params.document_id,))
            versions = [dict(v) for v in cursor.fetchall()]
            doc['versions'] = versions
        
        conn.close()
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return format_document_markdown(doc, params.include_content, params.include_versions)
        else:
            if not params.include_content:
                doc.pop('content', None)
            doc['tags'] = json.loads(doc['tags'])
            doc['metadata'] = json.loads(doc['metadata'])
            return json.dumps(doc, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to retrieve document: {str(e)}",
            "suggestion": "Please try again or contact support if the issue persists."
        }, indent=2)


@mcp.tool(
    name="document_update",
    annotations={
        "title": "Update Document",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def document_update(params: UpdateDocumentInput) -> str:
    """Update an existing document with new content, tags, or metadata.
    
    Updates create a new version automatically if content changes.
    Only provided fields are updated; others remain unchanged.
    
    Args:
        params (UpdateDocumentInput): Input parameters containing:
            - document_id (str): Document to update
            - title (Optional[str]): New title
            - content (Optional[str]): New content (creates new version)
            - tags (Optional[List[str]]): New tags (replaces existing)
            - status (Optional[DocumentStatus]): New status
            - metadata (Optional[Dict]): Additional metadata (merges)
            - version_comment (str): Comment for this version
    
    Returns:
        str: JSON response containing:
            {
                "success": bool,
                "document_id": str,
                "new_version": int (if content changed),
                "changes": List[str],
                "message": str
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get current document
        cursor.execute("SELECT * FROM documents WHERE id = ?", (params.document_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Document with ID '{params.document_id}' not found.",
                "suggestion": "Please verify the document ID exists before updating."
            }, indent=2)
        
        current = dict(row)
        changes = []
        timestamp = get_current_timestamp()
        
        # Prepare updates
        new_title = params.title if params.title is not None else current['title']
        new_content = params.content if params.content is not None else current['content']
        new_tags = json.dumps(params.tags) if params.tags is not None else current['tags']
        new_status = params.status.value if params.status is not None else current['status']
        
        # Merge metadata
        current_metadata = json.loads(current['metadata'])
        if params.metadata is not None:
            current_metadata.update(params.metadata)
        new_metadata = json.dumps(current_metadata)
        
        # Track changes
        if params.title is not None and params.title != current['title']:
            changes.append(f"title: '{current['title']}' → '{params.title}'")
        if params.content is not None:
            changes.append("content updated")
        if params.tags is not None:
            old_tags = json.loads(current['tags'])
            if set(params.tags) != set(old_tags):
                changes.append(f"tags: {old_tags} → {params.tags}")
        if params.status is not None and params.status.value != current['status']:
            changes.append(f"status: '{current['status']}' → '{params.status.value}'")
        if params.metadata is not None:
            changes.append("metadata updated")
        
        if not changes:
            conn.close()
            return json.dumps({
                "success": True,
                "document_id": params.document_id,
                "message": "No changes detected."
            }, indent=2)
        
        # Calculate new values
        new_size = len(new_content.encode('utf-8'))
        new_hash = calculate_content_hash(new_content)
        
        # Create new version if content changed
        new_version = None
        if params.content is not None:
            cursor.execute("""
                SELECT MAX(version_number) FROM document_versions WHERE document_id = ?
            """, (params.document_id,))
            max_version = cursor.fetchone()[0] or 0
            new_version = max_version + 1
            
            cursor.execute("""
                INSERT INTO document_versions (document_id, version_number, title, content, tags, status, metadata, created_at, comment, content_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                params.document_id,
                new_version,
                new_title,
                new_content,
                new_tags,
                new_status,
                new_metadata,
                timestamp,
                params.version_comment,
                new_hash
            ))
        
        # Update main document
        cursor.execute("""
            UPDATE documents
            SET title = ?, content = ?, tags = ?, status = ?, metadata = ?, updated_at = ?, size = ?, content_hash = ?
            WHERE id = ?
        """, (new_title, new_content, new_tags, new_status, new_metadata, timestamp, new_size, new_hash, params.document_id))
        
        conn.commit()
        conn.close()
        
        result = {
            "success": True,
            "document_id": params.document_id,
            "changes": changes,
            "updated_at": timestamp,
            "message": f"Document updated successfully. Changes: {', '.join(changes)}"
        }
        
        if new_version:
            result["new_version"] = new_version
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to update document: {str(e)}",
            "suggestion": "Please check your input and try again."
        }, indent=2)


@mcp.tool(
    name="document_delete",
    annotations={
        "title": "Delete Document",
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def document_delete(params: DeleteDocumentInput) -> str:
    """Delete or archive a document.
    
    By default, archives the document (sets status to 'archived').
    Use permanent=True to permanently delete the document and all versions.
    
    Args:
        params (DeleteDocumentInput): Input parameters containing:
            - document_id (str): Document to delete
            - permanent (bool): If True, permanently deletes; if False, archives
    
    Returns:
        str: JSON response containing:
            {
                "success": bool,
                "document_id": str,
                "action": str ("archived" or "deleted"),
                "message": str
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if document exists
        cursor.execute("SELECT title FROM documents WHERE id = ?", (params.document_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            return json.dumps({
                "success": False,
                "error": f"Document with ID '{params.document_id}' not found.",
                "suggestion": "Please verify the document ID."
            }, indent=2)
        
        title = row['title']
        
        if params.permanent:
            # Permanently delete document and versions
            cursor.execute("DELETE FROM document_versions WHERE document_id = ?", (params.document_id,))
            cursor.execute("DELETE FROM documents WHERE id = ?", (params.document_id,))
            action = "permanently deleted"
        else:
            # Archive the document
            timestamp = get_current_timestamp()
            cursor.execute("""
                UPDATE documents SET status = 'archived', updated_at = ? WHERE id = ?
            """, (timestamp, params.document_id))
            action = "archived"
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "success": True,
            "document_id": params.document_id,
            "title": title,
            "action": action,
            "message": f"Document '{title}' has been {action}."
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to delete document: {str(e)}",
            "suggestion": "Please try again or contact support."
        }, indent=2)


@mcp.tool(
    name="document_search",
    annotations={
        "title": "Search Documents",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_search(params: SearchDocumentsInput) -> str:
    """Search documents with full-text search, filtering, and pagination.
    
    Supports full-text search across title and content, tag filtering,
    status filtering, date range filtering, and various sorting options.
    
    Args:
        params (SearchDocumentsInput): Input parameters containing:
            - query (Optional[str]): Full-text search query
            - tags (Optional[List[str]]): Filter by tags (AND logic)
            - status (Optional[DocumentStatus]): Filter by status
            - created_after (Optional[str]): Date filter (ISO format)
            - created_before (Optional[str]): Date filter (ISO format)
            - sort_by (SortField): Field to sort by
            - sort_order (SortOrder): Sort direction
            - limit (int): Results per page
            - offset (int): Pagination offset
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Search results with pagination info. JSON format includes:
            {
                "total": int,
                "count": int,
                "offset": int,
                "limit": int,
                "has_more": bool,
                "next_offset": int,
                "documents": List[Dict]
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        conditions = []
        query_params = []
        
        # Full-text search
        doc_ids_from_fts = None
        if params.query:
            fts_query = ' '.join(f'"{word}"*' for word in params.query.split())
            cursor.execute("""
                SELECT id FROM documents_fts WHERE documents_fts MATCH ?
            """, (fts_query,))
            doc_ids_from_fts = [row['id'] for row in cursor.fetchall()]
            if not doc_ids_from_fts:
                # No FTS matches
                result = {
                    "total": 0,
                    "count": 0,
                    "offset": params.offset,
                    "limit": params.limit,
                    "has_more": False,
                    "documents": []
                }
                if params.response_format == ResponseFormat.MARKDOWN:
                    return format_search_results_markdown([], 0, params.offset)
                return json.dumps(result, indent=2)
        
        # Tag filtering
        if params.tags:
            for tag in params.tags:
                conditions.append("tags LIKE ?")
                query_params.append(f'%"{tag}"%')
        
        # Status filtering
        if params.status:
            conditions.append("status = ?")
            query_params.append(params.status.value)
        
        # Date range filtering
        if params.created_after:
            conditions.append("created_at > ?")
            query_params.append(params.created_after)
        
        if params.created_before:
            conditions.append("created_at < ?")
            query_params.append(params.created_before)
        
        # Build WHERE clause
        where_clause = ""
        if doc_ids_from_fts is not None:
            placeholders = ','.join('?' * len(doc_ids_from_fts))
            if conditions:
                where_clause = f"WHERE id IN ({placeholders}) AND " + " AND ".join(conditions)
            else:
                where_clause = f"WHERE id IN ({placeholders})"
            query_params = list(doc_ids_from_fts) + query_params
        elif conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # Get total count
        count_query = f"SELECT COUNT(*) as total FROM documents {where_clause}"
        cursor.execute(count_query, query_params)
        total = cursor.fetchone()['total']
        
        # Build ORDER BY
        sort_mapping = {
            SortField.TITLE: "title",
            SortField.CREATED_AT: "created_at",
            SortField.UPDATED_AT: "updated_at",
            SortField.SIZE: "size"
        }
        order_by = f"{sort_mapping[params.sort_by]} {params.sort_order.value.upper()}"
        
        # Get documents
        select_query = f"""
            SELECT id, title, content, tags, status, metadata, created_at, updated_at, size
            FROM documents
            {where_clause}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
        """
        cursor.execute(select_query, query_params + [params.limit, params.offset])
        documents = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        has_more = total > params.offset + len(documents)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            return format_search_results_markdown(documents, total, params.offset)
        else:
            # Parse JSON fields for JSON output
            for doc in documents:
                doc['tags'] = json.loads(doc['tags'])
                doc['metadata'] = json.loads(doc['metadata'])
                # Truncate content for search results
                if len(doc['content']) > 500:
                    doc['content_preview'] = doc['content'][:500] + "..."
                else:
                    doc['content_preview'] = doc['content']
                del doc['content']
            
            return json.dumps({
                "total": total,
                "count": len(documents),
                "offset": params.offset,
                "limit": params.limit,
                "has_more": has_more,
                "next_offset": params.offset + len(documents) if has_more else None,
                "documents": documents
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Search failed: {str(e)}",
            "suggestion": "Please refine your search query and try again."
        }, indent=2)


@mcp.tool(
    name="document_list_tags",
    annotations={
        "title": "List All Tags",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_list_tags(params: ListTagsInput) -> str:
    """List all tags used across documents with usage counts.
    
    Returns a comprehensive list of all tags in the system with their
    usage frequency, helpful for discovering document categories.
    
    Args:
        params (ListTagsInput): Input parameters containing:
            - sort_by_count (bool): Sort by usage count or alphabetically
            - min_count (int): Minimum usage count to include
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Tag list with counts. JSON format includes:
            {
                "total_tags": int,
                "tags": List[{"name": str, "count": int}]
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT tags FROM documents")
        rows = cursor.fetchall()
        conn.close()
        
        # Count tag frequencies
        tag_counts: dict[str, int] = {}
        for row in rows:
            tags = json.loads(row['tags'])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Filter by min_count
        filtered_tags = [(tag, count) for tag, count in tag_counts.items() if count >= params.min_count]
        
        # Sort
        if params.sort_by_count:
            filtered_tags.sort(key=lambda x: (-x[1], x[0]))
        else:
            filtered_tags.sort(key=lambda x: x[0])
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                "# Document Tags",
                "",
                f"Total unique tags: **{len(filtered_tags)}**",
                ""
            ]
            for tag, count in filtered_tags:
                lines.append(f"- **{tag}**: {count} document{'s' if count != 1 else ''}")
            return "\n".join(lines)
        else:
            return json.dumps({
                "total_tags": len(filtered_tags),
                "tags": [{"name": tag, "count": count} for tag, count in filtered_tags]
            }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to list tags: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_get_version",
    annotations={
        "title": "Get Document Version",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_get_version(params: GetDocumentVersionInput) -> str:
    """Retrieve a specific historical version of a document.
    
    Fetches the complete state of a document at a specific version,
    including content, tags, and metadata as they were at that time.
    
    Args:
        params (GetDocumentVersionInput): Input parameters containing:
            - document_id (str): Document identifier
            - version_number (int): Version to retrieve
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Version data in requested format. JSON includes:
            {
                "document_id": str,
                "version_number": int,
                "title": str,
                "content": str,
                "tags": List[str],
                "status": str,
                "metadata": Dict,
                "created_at": str,
                "comment": str
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM document_versions
            WHERE document_id = ? AND version_number = ?
        """, (params.document_id, params.version_number))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return json.dumps({
                "success": False,
                "error": f"Version {params.version_number} not found for document '{params.document_id}'.",
                "suggestion": "Use document_get with include_versions=True to see available versions."
            }, indent=2)
        
        version = dict(row)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Document Version {version['version_number']}",
                "",
                f"**Document ID**: `{version['document_id']}`",
                f"**Title**: {version['title']}",
                f"**Created**: {format_timestamp(version['created_at'])}",
                f"**Comment**: {version['comment'] or 'No comment'}",
                "",
                "## Content",
                "",
                version['content']
            ]
            return "\n".join(lines)
        else:
            version['tags'] = json.loads(version['tags'])
            version['metadata'] = json.loads(version['metadata'])
            return json.dumps(version, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to retrieve version: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_compare_versions",
    annotations={
        "title": "Compare Document Versions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_compare_versions(params: CompareVersionsInput) -> str:
    """Compare two versions of a document to see differences.
    
    Provides a side-by-side comparison of two document versions,
    highlighting changes in title, content length, tags, and metadata.
    
    Args:
        params (CompareVersionsInput): Input parameters containing:
            - document_id (str): Document identifier
            - version_a (int): First version to compare
            - version_b (int): Second version to compare
    
    Returns:
        str: Comparison results showing differences between versions
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get both versions
        cursor.execute("""
            SELECT * FROM document_versions
            WHERE document_id = ? AND version_number IN (?, ?)
        """, (params.document_id, params.version_a, params.version_b))
        
        rows = cursor.fetchall()
        conn.close()
        
        if len(rows) != 2:
            return json.dumps({
                "success": False,
                "error": f"Could not find both versions {params.version_a} and {params.version_b}.",
                "suggestion": "Verify both version numbers exist for this document."
            }, indent=2)
        
        versions = {row['version_number']: dict(row) for row in rows}
        va = versions[params.version_a]
        vb = versions[params.version_b]
        
        # Compare
        differences = []
        
        if va['title'] != vb['title']:
            differences.append({
                "field": "title",
                f"v{params.version_a}": va['title'],
                f"v{params.version_b}": vb['title']
            })
        
        content_len_a = len(va['content'])
        content_len_b = len(vb['content'])
        if content_len_a != content_len_b:
            differences.append({
                "field": "content_length",
                f"v{params.version_a}": f"{content_len_a} chars",
                f"v{params.version_b}": f"{content_len_b} chars",
                "change": f"{content_len_b - content_len_a:+d} chars"
            })
        
        tags_a = set(json.loads(va['tags']))
        tags_b = set(json.loads(vb['tags']))
        if tags_a != tags_b:
            differences.append({
                "field": "tags",
                "added": list(tags_b - tags_a),
                "removed": list(tags_a - tags_b)
            })
        
        if va['status'] != vb['status']:
            differences.append({
                "field": "status",
                f"v{params.version_a}": va['status'],
                f"v{params.version_b}": vb['status']
            })
        
        lines = [
            f"# Version Comparison: v{params.version_a} vs v{params.version_b}",
            "",
            f"**Document**: `{params.document_id}`",
            f"**Version {params.version_a}**: {format_timestamp(va['created_at'])}",
            f"**Version {params.version_b}**: {format_timestamp(vb['created_at'])}",
            "",
            "## Differences",
            ""
        ]
        
        if not differences:
            lines.append("No significant differences found between these versions.")
        else:
            for diff in differences:
                if diff['field'] == 'title':
                    lines.append(f"### Title Changed")
                    lines.append(f"- v{params.version_a}: {diff[f'v{params.version_a}']}")
                    lines.append(f"- v{params.version_b}: {diff[f'v{params.version_b}']}")
                elif diff['field'] == 'content_length':
                    lines.append(f"### Content Length Changed")
                    lines.append(f"- v{params.version_a}: {diff[f'v{params.version_a}']}")
                    lines.append(f"- v{params.version_b}: {diff[f'v{params.version_b}']}")
                    lines.append(f"- Change: {diff['change']}")
                elif diff['field'] == 'tags':
                    lines.append(f"### Tags Changed")
                    if diff['added']:
                        lines.append(f"- Added: {', '.join(diff['added'])}")
                    if diff['removed']:
                        lines.append(f"- Removed: {', '.join(diff['removed'])}")
                elif diff['field'] == 'status':
                    lines.append(f"### Status Changed")
                    lines.append(f"- v{params.version_a}: {diff[f'v{params.version_a}']}")
                    lines.append(f"- v{params.version_b}: {diff[f'v{params.version_b}']}")
                lines.append("")
        
        return "\n".join(lines)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to compare versions: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_analyze",
    annotations={
        "title": "Analyze Document Content",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_analyze(params: AnalyzeDocumentInput) -> str:
    """Analyze document content for statistics and keywords.
    
    Provides comprehensive analysis including word count, character count,
    estimated reading time, and automatically extracted keywords.
    
    Args:
        params (AnalyzeDocumentInput): Input parameters containing:
            - document_id (str): Document to analyze
            - include_stats (bool): Include statistical analysis
            - include_keywords (bool): Extract top keywords
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: Analysis results. JSON format includes:
            {
                "document_id": str,
                "title": str,
                "stats": {
                    "word_count": int,
                    "character_count": int,
                    "line_count": int,
                    "paragraph_count": int,
                    "reading_time_minutes": int
                },
                "keywords": List[str]
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, title, content FROM documents WHERE id = ?", (params.document_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return json.dumps({
                "success": False,
                "error": f"Document '{params.document_id}' not found."
            }, indent=2)
        
        doc = dict(row)
        content = doc['content']
        
        analysis = {
            "document_id": doc['id'],
            "title": doc['title']
        }
        
        if params.include_stats:
            words = content.split()
            lines = content.split('\n')
            paragraphs = [p for p in content.split('\n\n') if p.strip()]
            
            analysis['stats'] = {
                "word_count": len(words),
                "character_count": len(content),
                "character_count_no_spaces": len(content.replace(' ', '').replace('\n', '')),
                "line_count": len(lines),
                "paragraph_count": len(paragraphs),
                "average_word_length": round(sum(len(w) for w in words) / max(len(words), 1), 2),
                "reading_time_minutes": calculate_reading_time(content)
            }
        
        if params.include_keywords:
            analysis['keywords'] = extract_keywords(content, top_n=15)
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                f"# Document Analysis",
                "",
                f"**Document**: {doc['title']}",
                f"**ID**: `{doc['id']}`",
                ""
            ]
            
            if params.include_stats:
                stats = analysis['stats']
                lines.extend([
                    "## Statistics",
                    "",
                    f"- **Word Count**: {stats['word_count']:,}",
                    f"- **Character Count**: {stats['character_count']:,}",
                    f"- **Characters (no spaces)**: {stats['character_count_no_spaces']:,}",
                    f"- **Line Count**: {stats['line_count']:,}",
                    f"- **Paragraph Count**: {stats['paragraph_count']:,}",
                    f"- **Average Word Length**: {stats['average_word_length']} characters",
                    f"- **Estimated Reading Time**: {stats['reading_time_minutes']} minute{'s' if stats['reading_time_minutes'] != 1 else ''}",
                    ""
                ])
            
            if params.include_keywords:
                lines.extend([
                    "## Top Keywords",
                    "",
                    ", ".join(analysis['keywords']),
                    ""
                ])
            
            return "\n".join(lines)
        else:
            return json.dumps(analysis, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to analyze document: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_export",
    annotations={
        "title": "Export Document",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_export(params: ExportDocumentInput) -> str:
    """Export a document to various formats (Markdown, HTML, JSON, TXT).
    
    Converts document content to the specified format with optional
    metadata inclusion. Useful for sharing or archiving documents.
    
    Args:
        params (ExportDocumentInput): Input parameters containing:
            - document_id (str): Document to export
            - format (str): Export format (markdown/html/json/txt)
            - include_metadata (bool): Include metadata in export
    
    Returns:
        str: Exported document content in requested format
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM documents WHERE id = ?", (params.document_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return json.dumps({
                "success": False,
                "error": f"Document '{params.document_id}' not found."
            }, indent=2)
        
        doc = dict(row)
        doc['tags'] = json.loads(doc['tags'])
        doc['metadata'] = json.loads(doc['metadata'])
        
        if params.format == "markdown":
            lines = [f"# {doc['title']}", ""]
            if params.include_metadata:
                lines.extend([
                    "---",
                    f"id: {doc['id']}",
                    f"status: {doc['status']}",
                    f"tags: {', '.join(doc['tags'])}",
                    f"created: {doc['created_at']}",
                    f"updated: {doc['updated_at']}",
                    "---",
                    ""
                ])
            lines.append(doc['content'])
            return "\n".join(lines)
            
        elif params.format == "html":
            html_lines = [
                "<!DOCTYPE html>",
                "<html>",
                "<head>",
                f"<title>{doc['title']}</title>",
                "<meta charset='utf-8'>",
                "</head>",
                "<body>"
            ]
            
            if params.include_metadata:
                html_lines.extend([
                    "<header>",
                    f"<p><strong>ID:</strong> {doc['id']}</p>",
                    f"<p><strong>Status:</strong> {doc['status']}</p>",
                    f"<p><strong>Tags:</strong> {', '.join(doc['tags'])}</p>",
                    f"<p><strong>Created:</strong> {format_timestamp(doc['created_at'])}</p>",
                    f"<p><strong>Updated:</strong> {format_timestamp(doc['updated_at'])}</p>",
                    "</header>",
                    "<hr>"
                ])
            
            html_lines.extend([
                f"<h1>{doc['title']}</h1>",
                "<article>",
                doc['content'].replace('\n', '<br>\n'),
                "</article>",
                "</body>",
                "</html>"
            ])
            return "\n".join(html_lines)
            
        elif params.format == "json":
            export_data = {
                "title": doc['title'],
                "content": doc['content']
            }
            if params.include_metadata:
                export_data.update({
                    "id": doc['id'],
                    "status": doc['status'],
                    "tags": doc['tags'],
                    "metadata": doc['metadata'],
                    "created_at": doc['created_at'],
                    "updated_at": doc['updated_at'],
                    "size": doc['size']
                })
            return json.dumps(export_data, indent=2)
            
        elif params.format == "txt":
            lines = [doc['title'], "=" * len(doc['title']), ""]
            if params.include_metadata:
                lines.extend([
                    f"ID: {doc['id']}",
                    f"Status: {doc['status']}",
                    f"Tags: {', '.join(doc['tags'])}",
                    f"Created: {doc['created_at']}",
                    f"Updated: {doc['updated_at']}",
                    "",
                    "-" * 50,
                    ""
                ])
            lines.append(doc['content'])
            return "\n".join(lines)
        
        return json.dumps({
            "success": False,
            "error": f"Unsupported format: {params.format}"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to export document: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_bulk_tag",
    annotations={
        "title": "Bulk Tag Documents",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False
    }
)
async def document_bulk_tag(params: BulkTagInput) -> str:
    """Add or remove tags from multiple documents at once.
    
    Efficiently applies tag changes to a batch of documents,
    useful for reorganizing or categorizing document collections.
    
    Args:
        params (BulkTagInput): Input parameters containing:
            - document_ids (List[str]): Documents to modify
            - add_tags (Optional[List[str]]): Tags to add
            - remove_tags (Optional[List[str]]): Tags to remove
    
    Returns:
        str: JSON response with results for each document:
            {
                "success": bool,
                "total_documents": int,
                "updated": int,
                "failed": int,
                "results": List[Dict]
            }
    """
    try:
        if not params.add_tags and not params.remove_tags:
            return json.dumps({
                "success": False,
                "error": "No tags specified to add or remove.",
                "suggestion": "Provide add_tags and/or remove_tags parameter."
            }, indent=2)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        results = []
        updated_count = 0
        failed_count = 0
        timestamp = get_current_timestamp()
        
        for doc_id in params.document_ids:
            cursor.execute("SELECT tags FROM documents WHERE id = ?", (doc_id,))
            row = cursor.fetchone()
            
            if not row:
                results.append({
                    "document_id": doc_id,
                    "success": False,
                    "error": "Document not found"
                })
                failed_count += 1
                continue
            
            current_tags = set(json.loads(row['tags']))
            
            # Apply changes
            if params.add_tags:
                current_tags.update(params.add_tags)
            if params.remove_tags:
                current_tags -= set(params.remove_tags)
            
            new_tags = json.dumps(sorted(list(current_tags)))
            
            cursor.execute("""
                UPDATE documents SET tags = ?, updated_at = ? WHERE id = ?
            """, (new_tags, timestamp, doc_id))
            
            results.append({
                "document_id": doc_id,
                "success": True,
                "new_tags": sorted(list(current_tags))
            })
            updated_count += 1
        
        conn.commit()
        conn.close()
        
        return json.dumps({
            "success": True,
            "total_documents": len(params.document_ids),
            "updated": updated_count,
            "failed": failed_count,
            "results": results
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Bulk tag operation failed: {str(e)}"
        }, indent=2)


@mcp.tool(
    name="document_statistics",
    annotations={
        "title": "Get Document Statistics",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def document_statistics(params: GetStatisticsInput) -> str:
    """Get overall statistics about the document collection.
    
    Provides a comprehensive overview of the document management system,
    including total documents, storage usage, status distribution, and more.
    
    Args:
        params (GetStatisticsInput): Input parameters containing:
            - response_format (ResponseFormat): Output format
    
    Returns:
        str: System statistics. JSON format includes:
            {
                "total_documents": int,
                "total_size_bytes": int,
                "status_distribution": Dict[str, int],
                "total_tags": int,
                "total_versions": int,
                "documents_with_most_versions": List[Dict]
            }
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total documents
        cursor.execute("SELECT COUNT(*) as count FROM documents")
        total_docs = cursor.fetchone()['count']
        
        # Total size
        cursor.execute("SELECT SUM(size) as total_size FROM documents")
        total_size = cursor.fetchone()['total_size'] or 0
        
        # Status distribution
        cursor.execute("""
            SELECT status, COUNT(*) as count FROM documents GROUP BY status
        """)
        status_dist = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total versions
        cursor.execute("SELECT COUNT(*) as count FROM document_versions")
        total_versions = cursor.fetchone()['count']
        
        # Average versions per document
        avg_versions = round(total_versions / max(total_docs, 1), 2)
        
        # Documents with most versions
        cursor.execute("""
            SELECT d.id, d.title, COUNT(v.id) as version_count
            FROM documents d
            JOIN document_versions v ON d.id = v.document_id
            GROUP BY d.id
            ORDER BY version_count DESC
            LIMIT 5
        """)
        most_versions = [dict(row) for row in cursor.fetchall()]
        
        # Tag count
        cursor.execute("SELECT tags FROM documents")
        all_tags = set()
        for row in cursor.fetchall():
            tags = json.loads(row['tags'])
            all_tags.update(tags)
        
        # Recent activity
        cursor.execute("""
            SELECT id, title, updated_at FROM documents
            ORDER BY updated_at DESC LIMIT 5
        """)
        recent_activity = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        stats = {
            "total_documents": total_docs,
            "total_size_bytes": total_size,
            "total_size_human": f"{total_size / 1024 / 1024:.2f} MB",
            "status_distribution": status_dist,
            "total_unique_tags": len(all_tags),
            "total_versions": total_versions,
            "average_versions_per_document": avg_versions,
            "documents_with_most_versions": most_versions,
            "recent_activity": recent_activity
        }
        
        if params.response_format == ResponseFormat.MARKDOWN:
            lines = [
                "# Document Management Statistics",
                "",
                "## Overview",
                "",
                f"- **Total Documents**: {stats['total_documents']:,}",
                f"- **Total Storage**: {stats['total_size_human']} ({stats['total_size_bytes']:,} bytes)",
                f"- **Total Versions**: {stats['total_versions']:,}",
                f"- **Average Versions per Document**: {stats['average_versions_per_document']}",
                f"- **Unique Tags**: {stats['total_unique_tags']:,}",
                "",
                "## Status Distribution",
                ""
            ]
            
            for status, count in stats['status_distribution'].items():
                lines.append(f"- **{status.capitalize()}**: {count}")
            
            lines.extend([
                "",
                "## Most Versioned Documents",
                ""
            ])
            
            for doc in stats['documents_with_most_versions']:
                lines.append(f"- **{doc['title']}** (`{doc['id']}`): {doc['version_count']} versions")
            
            lines.extend([
                "",
                "## Recent Activity",
                ""
            ])
            
            for doc in stats['recent_activity']:
                lines.append(f"- **{doc['title']}** - {format_timestamp(doc['updated_at'])}")
            
            return "\n".join(lines)
        else:
            return json.dumps(stats, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": f"Failed to get statistics: {str(e)}"
        }, indent=2)


# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
