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
)
from pydantic import BaseModel, Field

from backend.core.services import DocumentService
from backend.app.api.deps import get_document_service

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
    - Pagination via limit and offset
    - Sorting by created_at, updated_at, title, or status

    Example:
        GET /api/v1/documents/?status=draft&tags=finance,2024
        &limit=50&offset=0&order_by=created_at&order_desc=true
    """
    logger.info(
        f"Listing documents: status={status}, tags={tags}, "
        f"limit={limit}, offset={offset}, order_by={order_by}"
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
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc,
        )
        logger.info(f"Listed {result.get('total', 0)} documents")
        return result
    except Exception as e:
        logger.error(f"Error listing documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list documents") from e


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
        "code files (.py, .js, .cpp, etc.), and markdown (.md) files. "
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
            "code files (.py, .js, .cpp, etc.), markdown (.md), and other formats."
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
    - Code files (.py, .js, .cpp, etc.)
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
    logger.info(
        f"Upload request: filename={file.filename}, "
        f"content_type={file.content_type}, size={file.size if hasattr(file, 'size') else 'unknown'}"
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
        logger.warning(f"Invalid JSON in upload request: {exc}")
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
        f"Creating document: title={chosen_title}, format={file_format}, "
        f"size={len(file_bytes)} bytes, tags={tags_list}, status={status}"
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
            f"Document uploaded successfully: "
            f"document_id={result.get('document_id')}, version={result.get('version')}"
        )
        return result
    except Exception as e:
        logger.error(f"Error uploading document: {e}", exc_info=True)
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
    logger.info(f"Request to {action} document: {document_id}")

    try:
        result = service.delete_document(
            document_id=document_id,
            permanent=permanent,
        )
        if not result.get("success"):
            error_msg = result.get("error", "Document not found")
            logger.warning(f"Delete failed: {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)
        logger.info(
            f"Document {action}d successfully: "
            f"document_id={document_id}, title={result.get('title')}"
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}", exc_info=True)
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

