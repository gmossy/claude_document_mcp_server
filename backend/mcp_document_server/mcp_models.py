"""Pydantic models and enums for MCP document server."""

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Constants (needed by models)
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
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid"
    )

    title: str = Field(
        ...,
        description=(
            "Document title (e.g., 'AI Test Engineering Report', "
            "'Meeting Notes 2024-01-15')"
        ),
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
        description=(
            "List of tags for categorization "
            "(e.g., ['ai-testing', 'engineering', 'test-report'])"
        ),
        max_length=MAX_TAGS
    )
    status: DocumentStatus = Field(
        default=DocumentStatus.DRAFT,
        description="Initial status: 'draft', 'published', or 'archived'"
    )
    metadata: Optional[dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Additional metadata as key-value pairs "
            "(e.g., {'author': 'John', 'department': 'Engineering'})"
        )
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


class ExportFileInput(BaseModel):
    """Input for exporting a document version to a versioned file on disk."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100,
    )
    version_number: Optional[int] = Field(
        default=None,
        description="Version to export (defaults to latest)."
    )
    format: str = Field(
        ...,
        description="Export format: markdown, txt, or code (no conversion to Word/PDF)",
        pattern=r"^(markdown|txt|code)$",
    )
    file_name: Optional[str] = Field(
        default=None,
        description="Optional file name (without directories). Uses a sanitized title if omitted.",
        max_length=200,
    )
    code_extension: Optional[str] = Field(
        default=None,
        description=(
            "File extension for code exports (e.g., '.py', '.cpp', '.usd'). "
            "Required when format='code'."
        ),
        max_length=16,
    )


class DownloadFileInput(BaseModel):
    """Input for downloading a document's binary file."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    document_id: str = Field(
        ...,
        description="Unique document identifier",
        min_length=1,
        max_length=100,
    )
    version_number: Optional[int] = Field(
        default=None,
        description="Specific version to download (defaults to latest version)."
    )

