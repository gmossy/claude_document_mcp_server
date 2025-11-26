"""Document search endpoints.

Provides full-text search and semantic search capabilities for documents.
"""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from backend.app.api.deps import get_document_service
from backend.core.services import DocumentService

router = APIRouter()


class SearchDocumentsResponse(BaseModel):
    """Response model for document search."""
    results: list[dict] = Field(
        default_factory=list,
        description="List of matching documents",
        examples=[[
            {
                "document_id": "doc_abc123def456",
                "title": "AI Test Engineering Report",
                "status": "published",
                "tags": ["ai-testing", "engineering"],
                "snippet": (
                    "The AI test engineering <b>report</b> shows significant "
                    "test coverage improvements..."
                )
            }
        ]]
    )


@router.get(
    "/",
    response_model=SearchDocumentsResponse,
    summary="Search documents by filename",
    description=(
        "Search for documents by filename, title, or metadata. "
        "Searches in document titles and stored filenames. "
        "Useful for finding files in the document library."
    ),
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "document_id": "doc_abc123def456",
                                "title": "report.pdf",
                                "status": "published",
                                "tags": ["test"],
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-15T10:30:00Z",
                                "size": 1024
                            }
                        ]
                    }
                }
            }
        }
    }
)
async def search_documents(
    q: str = Query(
        ...,
        description="Search query (filename, title, or partial match)",
        examples=["report.pdf", "test", "document.docx"],
        min_length=1
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of results to return",
        examples=[50]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Search for documents by filename, title, or metadata.

    This is the primary search endpoint for finding files in the document library.
    Searches across:
    - Document titles (which often match filenames)
    - Stored filenames in the database
    - Metadata fields

    Returns matching documents with their metadata (document_id, title, status,
    tags, created_at, updated_at, size).

    Example:
        GET /api/v1/search/?q=report.pdf&limit=50
        GET /api/v1/search/?q=test&limit=10
    """
    results = service.search_by_filename(q, limit)
    return {"results": results}


class SemanticSearchRequest(BaseModel):
    """Request model for semantic search."""
    query: str = Field(
        ...,
        description="Search query string",
        examples=["ai test engineering", "meeting notes", "test results"],
        min_length=1,
        max_length=500
    )
    limit: int = Field(
        default=5,
        description="Maximum number of results to return",
        examples=[5, 10, 20],
        ge=1,
        le=100
    )


class SemanticSearchResult(BaseModel):
    """Model for a single semantic search result."""
    document_id: str = Field(
        ..., description="Unique document identifier", examples=["doc_abc123def456"]
    )
    title: str = Field(
        ..., description="Document title", examples=["AI Test Engineering Report"]
    )
    status: str = Field(
        ..., description="Document status", examples=["published"]
    )
    tags: list[str] = Field(
        ..., description="List of tags", examples=[["ai-testing", "engineering"]]
    )
    snippet: str = Field(
        ...,
        description="Highlighted text snippet with matching terms",
        examples=[
            "The AI test engineering <b>report</b> shows significant "
            "test coverage improvements..."
        ],
    )


class SemanticSearchResponse(BaseModel):
    """Response model for semantic search."""
    results: list[SemanticSearchResult] = Field(
        ...,
        description="List of matching documents with snippets",
        examples=[[
            {
                "document_id": "doc_abc123def456",
                "title": "AI Test Engineering Report",
                "status": "published",
                "tags": ["ai-testing", "engineering"],
                "snippet": (
                    "The AI test engineering <b>report</b> shows significant "
                    "improvements in test coverage..."
                )
            }
        ]]
    )


@router.post(
    "/semantic",
    response_model=SemanticSearchResponse,
    summary="Semantic document search",
    description=(
        "Perform a semantic full-text search on documents using SQLite FTS5. "
        "Returns matching documents with highlighted snippets showing where "
        "the query terms appear."
    ),
    responses={
        200: {
            "description": "Search completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "document_id": "doc_abc123def456",
                                "title": "AI Test Engineering Report",
                                "status": "published",
                                "tags": ["ai-testing", "engineering"],
                                "snippet": (
                                    "The AI test engineering <b>report</b> shows "
                                    "significant improvements in test coverage. "
                                    "Key highlights include..."
                                )
                            },
                            {
                                "document_id": "doc_xyz789ghi012",
                                "title": "Meeting Notes 2024-01-14",
                                "status": "draft",
                                "tags": ["meetings", "notes"],
                                "snippet": (
                                    "Discussed AI test engineering <b>performance</b> "
                                    "metrics and future test strategies. "
                                    "The team reviewed..."
                                )
                            }
                        ]
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid query",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Query cannot be empty"
                    }
                }
            }
        }
    }
)
async def semantic_search(
    payload: SemanticSearchRequest,
    service: DocumentService = Depends(get_document_service),
):
    """
    Perform semantic full-text search on documents.

    Uses SQLite FTS5 for text matching with snippet highlighting. The search
    matches terms in document titles and content. If the query looks like a
    filename (contains dots, slashes, or extensions), it also searches by
    filename.

    Matching terms in snippets are wrapped in <b> tags for highlighting.

    Example queries:
    - "ai test engineering" - finds documents containing these words
    - "test results" - searches for documents with these terms
    - "report.pdf" - searches by filename if query looks like a filename
    - "meeting notes" - finds documents matching this phrase

    Note: This endpoint searches text content. For binary files, use the
    filename search endpoint (GET /api/v1/search/?q=filename) instead.
    """
    results = service.semantic_search(payload.query, payload.limit)
    return {"results": results}

