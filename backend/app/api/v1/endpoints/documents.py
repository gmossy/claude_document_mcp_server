"""Document management endpoints.

Provides CRUD operations for documents, including file uploads,
versioning, and exports.
"""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File,
    Form,
    HTTPException,
    Query,
    Response,
)
from fastapi.responses import StreamingResponse
from io import BytesIO
from pydantic import BaseModel, Field

from backend.core.services import DocumentService
from backend.app.api.deps import get_document_service

# Import formatters for analysis and export
try:
    from backend.mcp_document_server.mcp_formatters import (
        calculate_reading_time,
        extract_keywords,
        format_document_markdown,
    )
except ImportError:
    # Fallback if MCP server not available
    def calculate_reading_time(content: str) -> int:
        word_count = len(content.split())
        return max(1, round(word_count / 200))
    
    def extract_keywords(content: str, top_n: int = 10) -> list[str]:
        words = content.lower().split()
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
        word_freq: dict[str, int] = {}
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:top_n]]
    
    def format_document_markdown(doc: dict, include_content: bool = True, include_versions: bool = False) -> str:
        lines = [f"# {doc['title']}", "", f"**ID**: `{doc['id']}`"]
        if include_content:
            lines.append("")
            lines.append("## Content")
            lines.append("")
            lines.append(doc.get('content', ''))
        if include_versions and 'versions' in doc:
            lines.append("")
            lines.append("## Version History")
            for ver in doc.get('versions', []):
                lines.append(f"- **v{ver.get('version_number', '?')}**")
        return "\n".join(lines)

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentListResponse(BaseModel):
    """Response model for listing documents."""
    documents: list[dict] = Field(
        default_factory=list,
        description="List of document summaries",
        examples=[[
            {
                "id": "doc_abc123def456",
                "title": "AI Test Engineering Report",
                "status": "published",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
                "size": 1024,
                "tags": ["ai-testing", "engineering"]
            }
        ]]
    )
    total: int = Field(
        ...,
        description="Total number of documents matching the filters",
        examples=[42]
    )
    limit: int = Field(
        ...,
        description="Maximum number of documents returned",
        examples=[50]
    )
    offset: int = Field(
        ...,
        description="Number of documents skipped",
        examples=[0]
    )


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List all documents",
    description=(
        "Retrieve a list of documents in the system with pagination and filtering. "
        "Supports filtering by status and tags, and pagination via limit/offset."
    ),
    responses={
        200: {
            "description": "List of documents retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "documents": [
                            {
                                "id": "doc_abc123def456",
                                "title": "AI Test Engineering Report",
                                "status": "published",
                                "created_at": "2024-01-15T10:30:00Z",
                                "updated_at": "2024-01-16T14:20:00Z",
                                "size": 1024,
                                "tags": ["ai-testing", "engineering"]
                            },
                            {
                                "id": "doc_xyz789ghi012",
                                "title": "Meeting Notes 2024-01-14",
                                "status": "draft",
                                "created_at": "2024-01-14T14:20:00Z",
                                "updated_at": "2024-01-14T14:20:00Z",
                                "size": 512,
                                "tags": ["meetings", "notes"]
                            }
                        ],
                        "total": 42,
                        "limit": 50,
                        "offset": 0
                    }
                }
            }
        }
    }
)
async def list_documents(
    status: Optional[str] = Query(
        None,
        description="Filter by document status (draft, published, archived)",
        examples=["draft", "published", "archived"]
    ),
    tags: Optional[str] = Query(
        None,
        description="Comma-separated list of tags to filter by (documents must have all tags)",
        examples=["ai-testing,engineering", "meetings"]
    ),
    category: Optional[str] = Query(
        None,
        description="Filter by metadata category (DOTMLPF-P category)",
        examples=["Training", "Doctrine", "Organization", "Materiel", "Leadership", "Personnel", "Facilities", "Policy"]
    ),
    limit: int = Query(
        50,
        ge=1,
        le=100,
        description="Maximum number of documents to return (1-100)",
        examples=[50]
    ),
    offset: int = Query(
        0,
        ge=0,
        description="Number of documents to skip for pagination",
        examples=[0]
    ),
    order_by: str = Query(
        "created_at",
        description="Field to order by (created_at, updated_at, title, status)",
        examples=["created_at", "updated_at", "title"]
    ),
    order_desc: bool = Query(
        True,
        description="Whether to order descending (true) or ascending (false)",
        examples=[True]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    List documents in the document library with pagination and filtering.

    Returns a paginated list of documents with their metadata. Supports:
    - Filtering by status (draft, published, archived)
    - Filtering by tags (comma-separated, documents must have all specified tags)
    - Filtering by category (metadata.category field)
    - Pagination via limit and offset
    - Sorting by created_at, updated_at, title, or status

    Example:
        GET /api/v1/documents/?status=draft&tags=finance,2024&category=Training
        &limit=50&offset=0&order_by=created_at&order_desc=true
    """
    logger.info(
        "Listing documents: status=%s, tags=%s, category=%s, limit=%s, offset=%s, order_by=%s",
        status, tags, category, limit, offset, order_by
    )
    tags_list = None
    if tags:
        tags_list = [
            tag.strip() for tag in tags.split(",") if tag.strip()
        ]

    try:
        result = service.list_documents(
            status=status,
            tags=tags_list,
            category=category,
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
        logger.info("Listed %s documents", result.get('total', 0))
        return result
    except Exception as e:
        logger.error("Error listing documents: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents") from e


class DocumentResponse(BaseModel):
    """Response model for a single document."""
    id: str = Field(
        ...,
        description="Unique document identifier",
        examples=["doc_abc123def456"]
    )
    title: str = Field(
        ..., description="Document title", examples=["AI Test Engineering Report"]
    )
    content: Optional[str] = Field(
        None,
        description="Document content (text/markdown)",
        examples=["This is the document content..."]
    )
    status: str = Field(
        ..., description="Document status", examples=["draft", "published", "archived"]
    )
    tags: list[str] = Field(
        ..., description="List of tags", examples=[["ai-testing", "engineering"]]
    )
    metadata: dict = Field(
        ...,
        description="Additional metadata",
        examples=[{"author": "John Doe", "department": "AI Engineering"}]
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of creation",
        examples=["2024-01-15T10:30:00Z"]
    )
    updated_at: str = Field(
        ...,
        description="ISO timestamp of last update",
        examples=["2024-01-16T14:20:00Z"]
    )
    size: int = Field(
        ..., description="Document size in bytes", examples=[1024]
    )
    content_hash: str = Field(
        ...,
        description="SHA256 hash of document content",
        examples=["a1b2c3d4e5f6..."]
    )
    versions: Optional[list[dict]] = Field(
        None,
        description="Version history (if requested)",
        examples=[[
            {
                "version_number": 1,
                "title": "AI Test Engineering Report",
                "created_at": "2024-01-15T10:30:00Z",
                "comment": "Initial version",
                "content_hash": "a1b2c3d4e5f6..."
            }
        ]]
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get a document by ID",
    description=(
        "Retrieve a single document by its unique identifier. "
        "Optionally include full content and version history."
    ),
    responses={
        200: {
            "description": "Document retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "doc_abc123def456",
                        "title": "AI Test Engineering Report",
                        "content": "This is the document content...",
                        "status": "published",
                        "tags": ["ai-testing", "engineering"],
                        "metadata": {"author": "John Doe"},
                        "created_at": "2024-01-15T10:30:00Z",
                        "updated_at": "2024-01-16T14:20:00Z",
                        "size": 1024,
                        "content_hash": "a1b2c3d4e5f6...",
                        "versions": None
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Document with ID 'doc_abc123def456' not found."
                    }
                }
            }
        }
    }
)
async def get_document(
    document_id: str,
    include_content: bool = Query(
        True,
        description="Whether to include full document content",
        examples=[True, False]
    ),
    include_versions: bool = Query(
        False,
        description="Whether to include version history",
        examples=[True, False]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Retrieve a single document by its unique identifier.

    Returns the complete document information including metadata, tags, and
    optionally the full content and version history.

    Query Parameters:
    - include_content: Set to false to exclude document content (faster)
    - include_versions: Set to true to include version history

    Example:
        GET /api/v1/documents/doc_abc123?include_content=true&include_versions=false
    """
    logger.info(
        "Getting document: document_id=%s, include_content=%s, include_versions=%s",
        document_id, include_content, include_versions
    )

    try:
        doc = service.get_document(
            document_id=document_id,
            include_content=include_content,
            include_versions=include_versions,
        )
        if not doc:
            logger.warning("Document not found: document_id=%s", document_id)
            raise HTTPException(
                status_code=404,
                detail=f"Document with ID '{document_id}' not found."
            )
        logger.info("Retrieved document: document_id=%s, title=%s", document_id, doc.get('title'))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting document: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve document"
        ) from e


class CreateDocumentResponse(BaseModel):
    """Response model for document creation."""
    document_id: str = Field(
        ...,
        description="Unique identifier for the created document",
        examples=["doc_abc123def456"]
    )


@router.post(
    "/",
    response_model=CreateDocumentResponse,
    summary="Create a new document",
    description=(
        "Create a new document in the system. "
        "This is a placeholder endpoint that will be fully implemented."
    ),
    responses={
        200: {
            "description": "Document created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "doc_abc123def456"
                    }
                }
            }
        }
    }
)
async def create_document():
    """
    Create a new document.

    This endpoint is currently a placeholder and will be fully implemented
    to accept document content, title, tags, and metadata.
    """
    return {"document_id": "doc_placeholder"}


class UploadDocumentResponse(BaseModel):
    """Response model for document upload."""
    success: bool = Field(
        ..., description="Whether the upload was successful", examples=[True]
    )
    document_id: str = Field(
        ...,
        description="Unique identifier for the created document",
        examples=["doc_abc123def456"]
    )
    title: str = Field(
        ..., description="Document title", examples=["AI Test Engineering Report"]
    )
    status: str = Field(
        ..., description="Document status", examples=["draft"]
    )
    created_at: str = Field(
        ...,
        description="ISO timestamp of creation",
        examples=["2024-01-15T10:30:00Z"]
    )
    size: int = Field(
        ..., description="Document size in bytes", examples=[1024]
    )
    tags: list[str] = Field(
        ..., description="List of tags", examples=[["ai-testing", "engineering"]]
    )
    version: int = Field(
        ..., description="Document version number", examples=[1]
    )
    message: str = Field(
        ...,
        description="Success message",
        examples=[
            "Document 'AI Test Engineering Report' created successfully with ID doc_abc123def456"
        ]
    )
    binary: dict = Field(..., description="Binary file metadata", examples=[{
        "filename": "report.pdf",
        "mime_type": "application/pdf",
        "format": "pdf",
        "size_bytes": 1024
    }])


@router.post(
    "/upload",
    response_model=UploadDocumentResponse,
    summary="Upload a document file",
    description=(
        "Upload a document file and store it with automatic versioning. "
        "Supports Word (.docx), Excel (.xlsx), PDF (.pdf), OpenUSD (.usd, .usda, .usdc), "
        "code files (.py, .js, .cpp, .cue, etc.), and markdown (.md) files. "
        "Files are stored as-is without parsing or conversion."
    ),
    responses={
        200: {
            "description": "Document uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "document_id": "doc_abc123def456",
                        "title": "AI Test Engineering Report",
                        "status": "draft",
                        "created_at": "2024-01-15T10:30:00Z",
                        "size": 1024,
                        "tags": ["ai-testing", "engineering"],
                        "version": 1,
                        "message": (
                            "Document 'AI Test Engineering Report' created successfully "
                            "with ID doc_abc123def456"
                        ),
                        "binary": {
                            "filename": "test-report.pdf",
                            "mime_type": "application/pdf",
                            "format": "pdf",
                            "size_bytes": 1024
                        }
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid file or parameters",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Uploaded file is empty."
                    }
                }
            }
        }
    }
)
async def upload_document(
    file: UploadFile = File(
        ...,
        description=(
            "Document file to upload. Supports: "
            "Word (.docx), Excel (.xlsx), PDF (.pdf), OpenUSD (.usd, .usda, .usdc), "
            "code files (.py, .js, .cpp, .cue, etc.), markdown (.md), and other formats."
        ),
        examples=["test-report.pdf", "meeting_notes.docx", "presentation.pptx"]
    ),
    title: Optional[str] = Form(
        None,
        description=(
            "Custom title for the document (defaults to filename without extension)"
        ),
        examples=["AI Test Engineering Report", "Meeting Notes 2024-01-15"]
    ),
    tags: Optional[str] = Form(
        "[]",
        description="JSON array of tags as a string",
        examples=['["ai-testing", "engineering"]', '["meetings", "notes"]']
    ),
    status: str = Form(
        "draft",
        description="Document status",
        examples=["draft", "published", "archived"]
    ),
    metadata: Optional[str] = Form(
        "{}",
        description="JSON object with additional metadata",
        examples=['{"author": "John Doe", "department": "AI Engineering"}']
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Upload a document file and store it in the document library.

    This endpoint accepts binary files and stores them as-is without parsing,
    text extraction, or format conversion. Files are stored in versioned
    directories with metadata tracking.

    Supported file types:
    - Word documents (.docx)
    - Excel spreadsheets (.xlsx)
    - PDF files (.pdf)
    - OpenUSD files (.usd, .usda, .usdc)
    - Code files (.py, .js, .cpp, .cue, etc.)
    - Markdown files (.md)
    - Any other file format

    Features:
    - Automatic versioning on upload
    - Metadata management (title, tags, status)
    - Binary file storage
    - No parsing or conversion performed

    Example:
        curl -X POST "http://localhost:8000/api/v1/documents/upload" \\
          -F "file=@report.pdf" \\
          -F "title=Q4 Report" \\
          -F "tags=[\\"finance\\", \\"2024\\"]" \\
          -F "status=draft"
    """
    file_size = file.size if hasattr(file, 'size') else 'unknown'
    logger.info(
        "Upload request: filename=%s, content_type=%s, size=%s",
        file.filename, file.content_type, file_size
    )
    file_bytes = await file.read()
    if not file_bytes:
        logger.warning("Upload failed: empty file")
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        tags_list = json.loads(tags) if tags else []
        metadata_dict = json.loads(metadata) if metadata else {}
        if not isinstance(tags_list, list):
            raise ValueError("Tags must be a JSON array")
    except (ValueError, json.JSONDecodeError) as exc:
        logger.warning("Invalid JSON in upload request: %s", exc)
        raise HTTPException(
            status_code=400,
            detail="Tags and metadata must be valid JSON.",
        ) from exc

    chosen_title = title or Path(file.filename or "document").stem or "document"
    # Use filename as content placeholder (no text extraction)
    extracted_text = file.filename or "uploaded_file"

    file_format = (
        Path(file.filename or "").suffix.lstrip(".").lower() or "binary"
    )

    logger.info(
        "Creating document: title=%s, format=%s, size=%s bytes, tags=%s, status=%s",
        chosen_title, file_format, len(file_bytes), tags_list, status
    )

    try:
        result = service.create_document_from_upload(
            title=chosen_title,
            extracted_text=extracted_text,
            tags=tags_list,
            status=status,
            metadata=metadata_dict,
            filename=file.filename or "upload.bin",
            mime_type=file.content_type or "application/octet-stream",
            file_format=file_format,
            content_bytes=file_bytes,
        )
        logger.info(
            "Document uploaded successfully: document_id=%s, version=%s",
            result.get('document_id'), result.get('version')
        )
        return result
    except Exception as e:
        logger.error("Error uploading document: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to upload document"
        ) from e


class DeleteDocumentResponse(BaseModel):
    """Response model for document deletion."""
    success: bool = Field(
        ..., description="Whether the deletion was successful", examples=[True]
    )
    document_id: str = Field(
        ..., description="Document identifier", examples=["doc_abc123def456"]
    )
    title: str = Field(
        ..., description="Document title", examples=["Test Document"]
    )
    action: str = Field(
        ...,
        description="Action taken: 'archived' or 'permanently deleted'",
        examples=["archived"],
    )
    message: str = Field(
        ...,
        description="Success message",
        examples=["Document 'Test Document' has been archived."],
    )


@router.delete(
    "/{document_id}",
    response_model=DeleteDocumentResponse,
    summary="Delete a document",
    description=(
        "Delete or archive a document. By default, archives the document "
        "(sets status to 'archived'). Use permanent=true to permanently delete."
    ),
    responses={
        200: {
            "description": "Document deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "document_id": "doc_abc123def456",
                        "title": "Test Document",
                        "action": "archived",
                        "message": "Document 'Test Document' has been archived."
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Document with ID 'doc_abc123def456' not found."
                    }
                }
            }
        }
    }
)
async def delete_document(
    document_id: str,
    permanent: bool = Query(
        False,
        description="If True, permanently deletes; if False, archives the document",
        examples=[False, True]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Delete or archive a document.

    By default, archives the document (sets status to 'archived'), which preserves
    the document and all versions for potential recovery.

    Permanent deletion removes:
    - The document record from the database
    - All version history
    - All stored binary files from disk

    Example:
        DELETE /api/v1/documents/doc_abc123?permanent=false  # Archive
        DELETE /api/v1/documents/doc_abc123?permanent=true   # Permanent delete
    """
    action = "permanently delete" if permanent else "archive"
    logger.info("Request to %s document: %s", action, document_id)

    try:
        result = service.delete_document(
            document_id=document_id,
            permanent=permanent,
        )
        if not result.get("success"):
            error_msg = result.get("error", "Document not found")
            logger.warning("Delete failed: %s", error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        logger.info(
            "Document %sd successfully: document_id=%s, title=%s",
            action, document_id, result.get('title')
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting document: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to delete document"
        ) from e


class CreateDocumentFileRequest(BaseModel):
    """Request model for creating document files."""
    document_id: str = Field(
        ..., description="Document ID to convert", examples=["doc_abc123def456"]
    )
    file_format: str = Field(
        ...,
        description="Output format: docx, pdf, or xlsx",
        examples=["docx", "pdf", "xlsx"],
    )
    version_number: Optional[int] = Field(
        None,
        description="Specific version to use (defaults to latest)",
        examples=[1, 2],
    )
    file_name: Optional[str] = Field(
        None,
        description="Custom filename (defaults to document title)",
        examples=["report.docx"],
    )
    excel_data: Optional[list[list[str]]] = Field(
        None,
        description=(
            "For Excel format: list of rows (list of lists). "
            "If None, converts content to single column."
        ),
        examples=[[["Name", "Age"], ["John", "30"], ["Jane", "25"]]],
    )


class CreateDocumentFileResponse(BaseModel):
    """Response model for document file creation."""
    success: bool = Field(
        ..., description="Whether creation was successful", examples=[True]
    )
    document_id: str = Field(
        ..., description="Document identifier", examples=["doc_abc123def456"]
    )
    version_number: int = Field(
        ..., description="Version number used", examples=[1]
    )
    title: str = Field(
        ..., description="Document title", examples=["Test Document"]
    )
    file_path: str = Field(
        ...,
        description="Path to created file",
        examples=["/path/to/document_storage/doc_123/v1/report.docx"],
    )
    file_size: int = Field(..., description="File size in bytes", examples=[1024])
    format: str = Field(..., description="File format created", examples=["docx"])
    message: str = Field(
        ...,
        description="Success message",
        examples=["Created DOCX document: report.docx"],
    )


@router.post(
    "/create-file",
    response_model=CreateDocumentFileResponse,
    summary="Create Word, PDF, or Excel document",
    description=(
        "Create a formatted document (Word, PDF, or Excel) from a stored "
        "document's text content. This generates new formatted documents from "
        "text content in the document library. Requires python-docx (for Word), "
        "reportlab (for PDF), and openpyxl (for Excel)."
    ),
    responses={
        200: {
            "description": "Document file created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "document_id": "doc_abc123def456",
                        "version_number": 1,
                        "title": "Test Document",
                        "file_path": (
                            "/path/to/document_storage/"
                            "doc_abc123def456/v1/Test_Document.docx"
                        ),
                        "file_size": 1024,
                        "format": "docx",
                        "message": "Created DOCX document: Test_Document.docx"
                    }
                }
            }
        },
        400: {
            "description": "Bad request - invalid format or missing dependencies",
            "content": {
                "application/json": {
                    "example": {
                        "detail": (
                            "Unsupported format: txt. "
                            "Supported formats: 'docx', 'pdf', 'xlsx'"
                        )
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Document 'doc_abc123def456' not found."
                    }
                }
            }
        }
    }
)
async def create_document_file(
    request: CreateDocumentFileRequest,
    service: DocumentService = Depends(get_document_service),
):
    """
    Create a Word, PDF, or Excel document from a stored document's text content.

    This endpoint generates formatted documents from text content stored in the
    document library. It's separate from binary file upload - this creates
    new formatted documents from existing text content.

    Supported formats:
    - docx: Microsoft Word document (requires python-docx)
    - pdf: PDF document (requires reportlab)
    - xlsx: Microsoft Excel spreadsheet (requires openpyxl)

    For Excel format, you can provide structured data as excel_data (list of rows).
    If not provided, the document content is converted to a single column.

    Example:
        POST /api/v1/documents/create-file
        {
            "document_id": "doc_abc123",
            "file_format": "docx",
            "version_number": 1
        }
    """
    try:
        result = service.create_document_file(
            document_id=request.document_id,
            file_format=request.file_format,
            version_number=request.version_number,
            file_name=request.file_name,
            excel_data=request.excel_data,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Required library not installed: {str(e)}"
        ) from e


class UpdateDocumentRequest(BaseModel):
    """Request model for updating a document."""
    title: Optional[str] = Field(
        None, description="New document title", examples=["Updated Title"]
    )
    content: Optional[str] = Field(
        None, description="New document content", examples=["Updated content..."]
    )
    tags: Optional[list[str]] = Field(
        None, description="New tags list", examples=[["tag1", "tag2"]]
    )
    status: Optional[str] = Field(
        None, description="New status", examples=["published", "draft", "archived"]
    )
    metadata: Optional[dict] = Field(
        None, description="Metadata to merge with existing", examples=[{"author": "John"}]
    )
    version_comment: Optional[str] = Field(
        "Updated document",
        description="Comment for new version if content changes",
        examples=["Added new section"]
    )


class UpdateDocumentResponse(BaseModel):
    """Response model for document update."""
    success: bool = Field(..., description="Whether update was successful", examples=[True])
    document_id: str = Field(..., description="Document identifier", examples=["doc_abc123"])
    title: str = Field(..., description="Updated title", examples=["Updated Title"])
    status: str = Field(..., description="Updated status", examples=["published"])
    updated_at: str = Field(..., description="ISO timestamp of update", examples=["2024-01-16T14:20:00Z"])
    version_created: bool = Field(..., description="Whether a new version was created", examples=[True])
    message: str = Field(..., description="Success message", examples=["Document 'Title' updated successfully"])


@router.patch(
    "/{document_id}",
    response_model=UpdateDocumentResponse,
    summary="Update a document",
    description=(
        "Update document content, title, tags, metadata, or status. "
        "If content changes, automatically creates a new version."
    ),
    responses={
        200: {
            "description": "Document updated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "document_id": "doc_abc123def456",
                        "title": "Updated Title",
                        "status": "published",
                        "updated_at": "2024-01-16T14:20:00Z",
                        "version_created": True,
                        "message": "Document 'Updated Title' updated successfully"
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document 'doc_abc123def456' not found."}
                }
            }
        }
    }
)
async def update_document(
    document_id: str,
    request: UpdateDocumentRequest,
    service: DocumentService = Depends(get_document_service),
):
    """
    Update a document's content, metadata, or status.

    If content is changed, automatically creates a new version.
    Other changes (title, tags, status, metadata) update the current document.

    Example:
        PATCH /api/v1/documents/doc_abc123
        {
            "title": "Updated Title",
            "content": "New content...",
            "tags": ["updated", "tags"],
            "version_comment": "Added new section"
        }
    """
    logger.info("Updating document: document_id=%s", document_id)

    try:
        result = service.update_document(
            document_id=document_id,
            title=request.title,
            content=request.content,
            tags=request.tags,
            status=request.status,
            metadata=request.metadata,
            version_comment=request.version_comment or "Updated document",
        )
        logger.info(
            "Document updated: document_id=%s, version_created=%s",
            document_id, result.get('version_created')
        )
        return result
    except ValueError as e:
        logger.warning("Update failed: %s", e)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Error updating document: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update document") from e


class DocumentVersionResponse(BaseModel):
    """Response model for a document version."""
    document_id: str = Field(..., description="Document identifier", examples=["doc_abc123"])
    version_number: int = Field(..., description="Version number", examples=[2])
    title: str = Field(..., description="Title at this version", examples=["Document Title"])
    content: str = Field(..., description="Content at this version", examples=["Content..."])
    tags: list[str] = Field(..., description="Tags at this version", examples=[["tag1", "tag2"]])
    status: str = Field(..., description="Status at this version", examples=["published"])
    metadata: dict = Field(..., description="Metadata at this version", examples=[{}])
    created_at: str = Field(..., description="ISO timestamp of version creation", examples=["2024-01-15T10:30:00Z"])
    comment: str = Field(..., description="Version comment", examples=["Initial version"])
    content_hash: str = Field(..., description="Content hash", examples=["abc123..."])


@router.get(
    "/{document_id}/versions/{version_number}",
    response_model=DocumentVersionResponse,
    summary="Get a specific document version",
    description="Retrieve a specific historical version of a document by version number.",
    responses={
        200: {
            "description": "Version retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "doc_abc123def456",
                        "version_number": 2,
                        "title": "Document Title",
                        "content": "Content at version 2...",
                        "tags": ["tag1", "tag2"],
                        "status": "published",
                        "metadata": {},
                        "created_at": "2024-01-15T10:30:00Z",
                        "comment": "Updated with new section",
                        "content_hash": "abc123..."
                    }
                }
            }
        },
        404: {
            "description": "Document or version not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Version 2 not found for document 'doc_abc123'."}
                }
            }
        }
    }
)
async def get_document_version(
    document_id: str,
    version_number: int,
    service: DocumentService = Depends(get_document_service),
):
    """
    Get a specific version of a document.

    Returns the document as it existed at the specified version number,
    including full content and metadata.

    Example:
        GET /api/v1/documents/doc_abc123/versions/2
    """
    logger.info(
        "Getting document version: document_id=%s, version_number=%s",
        document_id, version_number
    )

    try:
        version = service.get_document_version(
            document_id=document_id,
            version_number=version_number,
        )
        if not version:
            logger.warning(
                "Version not found: document_id=%s, version_number=%s",
                document_id, version_number
            )
            raise HTTPException(
                status_code=404,
                detail=f"Version {version_number} not found for document '{document_id}'."
            )
        logger.info("Retrieved version: document_id=%s, version_number=%s", document_id, version_number)
        return version
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting document version: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve document version"
        ) from e


class CompareVersionsResponse(BaseModel):
    """Response model for version comparison."""
    document_id: str = Field(..., description="Document identifier", examples=["doc_abc123"])
    version_a: int = Field(..., description="First version number", examples=[1])
    version_b: int = Field(..., description="Second version number", examples=[2])
    changed: bool = Field(..., description="Whether content changed", examples=[True])
    stats: dict = Field(
        ...,
        description="Comparison statistics",
        examples=[{
            "lines_added": 5,
            "lines_removed": 2,
            "content_length_a": 1000,
            "content_length_b": 1200
        }]
    )
    version_a_title: str = Field(..., description="Title at version A", examples=["Original Title"])
    version_b_title: str = Field(..., description="Title at version B", examples=["Updated Title"])
    version_a_created: str = Field(..., description="Creation time of version A", examples=["2024-01-15T10:30:00Z"])
    version_b_created: str = Field(..., description="Creation time of version B", examples=["2024-01-16T14:20:00Z"])


@router.get(
    "/{document_id}/versions/{version_a}/compare/{version_b}",
    response_model=CompareVersionsResponse,
    summary="Compare two document versions",
    description="Compare two versions of a document to see what changed.",
    responses={
        200: {
            "description": "Comparison completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "doc_abc123def456",
                        "version_a": 1,
                        "version_b": 2,
                        "changed": True,
                        "stats": {
                            "lines_added": 5,
                            "lines_removed": 2,
                            "content_length_a": 1000,
                            "content_length_b": 1200
                        },
                        "version_a_title": "Original Title",
                        "version_b_title": "Updated Title",
                        "version_a_created": "2024-01-15T10:30:00Z",
                        "version_b_created": "2024-01-16T14:20:00Z"
                    }
                }
            }
        },
        404: {
            "description": "Document or version not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Version 1 not found for document 'doc_abc123'."}
                }
            }
        }
    }
)
async def compare_versions(
    document_id: str,
    version_a: int,
    version_b: int,
    service: DocumentService = Depends(get_document_service),
):
    """
    Compare two versions of a document.

    Returns statistics about changes between the two versions, including
    lines added/removed and content length differences.

    Example:
        GET /api/v1/documents/doc_abc123/versions/1/compare/2
    """
    logger.info(
        "Comparing versions: document_id=%s, version_a=%s, version_b=%s",
        document_id, version_a, version_b
    )

    try:
        result = service.compare_versions(
            document_id=document_id,
            version_a=version_a,
            version_b=version_b,
        )
        logger.info(
            "Versions compared: document_id=%s, changed=%s",
            document_id, result.get('changed')
        )
        return result
    except ValueError as e:
        logger.warning("Compare failed: %s", e)
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        logger.error("Error comparing versions: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to compare versions") from e


class DocumentAnalyzeResponse(BaseModel):
    """Response model for document analysis."""
    document_id: str = Field(..., description="Document identifier", examples=["doc_abc123"])
    title: str = Field(..., description="Document title", examples=["Document Title"])
    stats: Optional[dict] = Field(
        None,
        description="Content statistics",
        examples=[{
            "word_count": 1234,
            "character_count": 5678,
            "character_count_no_spaces": 4567,
            "line_count": 50,
            "paragraph_count": 10,
            "reading_time_minutes": 6
        }]
    )
    keywords: Optional[list[str]] = Field(
        None, description="Top keywords", examples=[["keyword1", "keyword2", "keyword3"]]
    )


@router.get(
    "/{document_id}/analyze",
    response_model=DocumentAnalyzeResponse,
    summary="Analyze document content",
    description=(
        "Get content statistics and extract keywords from a document. "
        "Provides word count, character count, reading time, and top keywords."
    ),
    responses={
        200: {
            "description": "Analysis completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "document_id": "doc_abc123def456",
                        "title": "Document Title",
                        "stats": {
                            "word_count": 1234,
                            "character_count": 5678,
                            "line_count": 50,
                            "paragraph_count": 10,
                            "reading_time_minutes": 6
                        },
                        "keywords": ["keyword1", "keyword2", "keyword3"]
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document 'doc_abc123def456' not found."}
                }
            }
        }
    }
)
async def analyze_document(
    document_id: str,
    include_stats: bool = Query(
        True, description="Include word count, character count, reading time"
    ),
    include_keywords: bool = Query(
        True, description="Extract top keywords from content"
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Analyze document content to get statistics and keywords.

    Returns word count, character count, line count, paragraph count,
    estimated reading time, and top keywords extracted from the content.

    Example:
        GET /api/v1/documents/doc_abc123/analyze?include_stats=true&include_keywords=true
    """
    logger.info(
        "Analyzing document: document_id=%s, include_stats=%s, include_keywords=%s",
        document_id, include_stats, include_keywords
    )

    try:
        doc = service.get_document(
            document_id=document_id,
            include_content=True,
        )
        if not doc:
            logger.warning("Document not found: document_id=%s", document_id)
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found."
            )

        content = doc.get("content", "")
        stats = None
        keywords = None

        if include_stats:
            stats = {
                "word_count": len(content.split()),
                "character_count": len(content),
                "character_count_no_spaces": len(content.replace(" ", "")),
                "line_count": len(content.splitlines()),
                "paragraph_count": len([p for p in content.split("\n\n") if p.strip()]),
                "reading_time_minutes": calculate_reading_time(content),
            }

        if include_keywords:
            keywords = extract_keywords(content, top_n=15)

        result = {
            "document_id": document_id,
            "title": doc["title"],
            "stats": stats,
            "keywords": keywords,
        }

        logger.info("Document analyzed: document_id=%s", document_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error analyzing document: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to analyze document") from e


class BulkTagRequest(BaseModel):
    """Request model for bulk tag operations."""
    document_ids: list[str] = Field(
        ...,
        description="List of document IDs to update",
        examples=[["doc_abc123", "doc_def456", "doc_ghi789"]],
        min_length=1
    )
    add_tags: Optional[list[str]] = Field(
        None, description="Tags to add to all documents", examples=[["reviewed", "2024"]]
    )
    remove_tags: Optional[list[str]] = Field(
        None, description="Tags to remove from all documents", examples=[["draft"]]
    )


class BulkTagResult(BaseModel):
    """Result for a single document in bulk tag operation."""
    document_id: str = Field(..., description="Document identifier", examples=["doc_abc123"])
    success: bool = Field(..., description="Whether operation succeeded", examples=[True])
    error: Optional[str] = Field(None, description="Error message if failed", examples=[None])
    current_tags: list[str] = Field(..., description="Current tags after operation", examples=[["tag1", "tag2"]])


class BulkTagResponse(BaseModel):
    """Response model for bulk tag operations."""
    results: list[BulkTagResult] = Field(
        ...,
        description="Results for each document",
        examples=[[
            {
                "document_id": "doc_abc123",
                "success": True,
                "error": None,
                "current_tags": ["tag1", "tag2", "reviewed"]
            }
        ]]
    )
    total: int = Field(..., description="Total number of documents processed", examples=[3])
    successful: int = Field(..., description="Number of successful operations", examples=[3])
    failed: int = Field(..., description="Number of failed operations", examples=[0])


@router.post(
    "/bulk-tag",
    response_model=BulkTagResponse,
    summary="Bulk tag operations",
    description=(
        "Add or remove tags from multiple documents at once. "
        "Efficiently updates tags across multiple documents in a single operation."
    ),
    responses={
        200: {
            "description": "Bulk tag operation completed",
            "content": {
                "application/json": {
                    "example": {
                        "results": [
                            {
                                "document_id": "doc_abc123",
                                "success": True,
                                "error": None,
                                "current_tags": ["tag1", "tag2", "reviewed"]
                            }
                        ],
                        "total": 3,
                        "successful": 3,
                        "failed": 0
                    }
                }
            }
        }
    }
)
async def bulk_tag_documents(
    request: BulkTagRequest,
    service: DocumentService = Depends(get_document_service),
):
    """
    Add or remove tags from multiple documents.

    Updates tags across all specified documents. Tags are added or removed
    from each document's existing tag list.

    Example:
        POST /api/v1/documents/bulk-tag
        {
            "document_ids": ["doc_abc123", "doc_def456"],
            "add_tags": ["reviewed", "2024"],
            "remove_tags": ["draft"]
        }
    """
    logger.info(
        "Bulk tagging: document_ids=%s, add_tags=%s, remove_tags=%s",
        request.document_ids, request.add_tags, request.remove_tags
    )

    results = []
    successful = 0
    failed = 0

    for doc_id in request.document_ids:
        try:
            doc = service.get_document(document_id=doc_id, include_content=False)
            if not doc:
                results.append({
                    "document_id": doc_id,
                    "success": False,
                    "error": "Document not found",
                    "current_tags": []
                })
                failed += 1
                continue

            current_tags = doc.get("tags", [])
            new_tags = set(current_tags)

            if request.add_tags:
                new_tags.update(request.add_tags)
            if request.remove_tags:
                new_tags.difference_update(request.remove_tags)

            # Update document with new tags
            service.update_document(
                document_id=doc_id,
                tags=list(new_tags),
                version_comment="Bulk tag update"
            )

            results.append({
                "document_id": doc_id,
                "success": True,
                "error": None,
                "current_tags": list(new_tags)
            })
            successful += 1
        except Exception as e:
            logger.warning("Bulk tag failed for %s: %s", doc_id, e)
            error_msg = str(e) if e else "Unknown error"
            results.append({
                "document_id": doc_id,
                "success": False,
                "error": error_msg,
                "current_tags": []
            })
            failed += 1

    logger.info(
        "Bulk tag completed: total=%s, successful=%s, failed=%s",
        len(request.document_ids), successful, failed
    )

    return {
        "results": results,
        "total": len(request.document_ids),
        "successful": successful,
        "failed": failed
    }


@router.get(
    "/{document_id}/export",
    summary="Export document to text format",
    description=(
        "Export a document to Markdown, HTML, JSON, or plain text format. "
        "Returns the document content in the specified format."
    ),
    responses={
        200: {
            "description": "Document exported successfully",
            "content": {
                "text/markdown": {"example": "# Document Title\n\nContent..."},
                "text/html": {"example": "<html><body>...</body></html>"},
                "application/json": {"example": {"id": "doc_123", "title": "...", "content": "..."}},
                "text/plain": {"example": "Document content as plain text"}
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document 'doc_abc123def456' not found."}
                }
            }
        }
    }
)
async def export_document(
    document_id: str,
    export_format: str = Query(
        "markdown",
        description="Export format",
        examples=["markdown", "html", "json", "txt"],
        alias="format"
    ),
    include_metadata: bool = Query(
        True, description="Include metadata in export"
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Export a document to Markdown, HTML, JSON, or plain text format.

    Returns the document content in the specified format. For JSON format,
    includes structured data with metadata. For other formats, returns
    formatted text.

    Example:
        GET /api/v1/documents/doc_abc123/export?format=markdown
        GET /api/v1/documents/doc_abc123/export?format=json&include_metadata=true
    """
    logger.info(
        "Exporting document: document_id=%s, format=%s, include_metadata=%s",
        document_id, export_format, include_metadata
    )

    try:
        doc = service.get_document(
            document_id=document_id,
            include_content=True,
        )
        if not doc:
            logger.warning("Document not found: document_id=%s", document_id)
            raise HTTPException(
                status_code=404,
                detail=f"Document '{document_id}' not found."
            )

        format_lower = export_format.lower()

        if format_lower == "json":
            export_data = {
                "id": doc["id"],
                "title": doc["title"],
                "content": doc["content"],
                "tags": doc.get("tags", []),
                "status": doc["status"],
                "created_at": doc["created_at"],
                "updated_at": doc["updated_at"],
            }
            if include_metadata:
                export_data["metadata"] = doc.get("metadata", {})
            return Response(
                content=json.dumps(export_data, indent=2),
                media_type="application/json"
            )

        elif format_lower == "html":
            tags = doc.get("tags", [])
            tags_str = ", ".join(tags) if tags else "None"
            html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{doc['title']}</title>
    <meta charset="UTF-8">
</head>
<body>
    <h1>{doc['title']}</h1>
    <p><strong>ID:</strong> {doc['id']}</p>
    <p><strong>Status:</strong> {doc['status']}</p>
    <p><strong>Tags:</strong> {tags_str}</p>
    <p><strong>Created:</strong> {doc['created_at']}</p>
    <p><strong>Updated:</strong> {doc['updated_at']}</p>
    <hr>
    <div>{doc['content'].replace(chr(10), '<br>')}</div>
</body>
</html>"""
            return Response(content=html, media_type="text/html")

        elif format_lower == "txt":
            return Response(content=doc["content"], media_type="text/plain")

        else:  # markdown
            markdown = format_document_markdown(doc, include_content=True)
            return Response(content=markdown, media_type="text/markdown")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting document: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export document") from e


@router.get(
    "/{document_id}/download",
    summary="Download document binary file",
    description=(
        "Download the original binary file for a document. "
        "Returns the file as it was uploaded, without any conversion."
    ),
    responses={
        200: {
            "description": "File downloaded successfully",
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        404: {
            "description": "Document or file not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document or binary file not found."}
                }
            }
        }
    }
)
async def download_document_file(
    document_id: str,
    version_number: Optional[int] = Query(
        None,
        description="Specific version to download (defaults to latest)",
        examples=[1, 2]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    Download the original binary file for a document.

    Returns the file exactly as it was uploaded, without any parsing,
    conversion, or modification. Supports all file formats.

    Query Parameters:
    - version_number: Optional version number (defaults to latest version)

    Example:
        GET /api/v1/documents/doc_abc123/download
        GET /api/v1/documents/doc_abc123/download?version_number=2
    """
    logger.info(
        "Download request: document_id=%s, version_number=%s",
        document_id, version_number
    )

    try:
        binary_data = service.get_binary_file(
            document_id=document_id,
            version_number=version_number,
        )

        if not binary_data:
            logger.warning(
                "Binary file not found: document_id=%s, version_number=%s",
                document_id, version_number
            )
            raise HTTPException(
                status_code=404,
                detail="Document or binary file not found."
            )

        filename = binary_data["filename"]
        mime_type = binary_data["mime_type"] or "application/octet-stream"
        content_bytes = binary_data["content_bytes"]

        logger.info(
            "Serving file: document_id=%s, filename=%s, size=%s bytes",
            document_id, filename, len(content_bytes)
        )

        # Return file as streaming response
        return StreamingResponse(
            BytesIO(content_bytes),
            media_type=mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(content_bytes)),
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error downloading file: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to download file"
        ) from e

