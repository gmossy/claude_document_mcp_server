import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from backend.mcp_document_server.document_parsers import extract_text_from_file
from backend.core.services import DocumentService

from ....api.deps import get_document_service

router = APIRouter()


@router.get("/")
async def list_documents(
    service: DocumentService = Depends(get_document_service),
):
    """List all documents."""
    # TODO: Implement pagination and filtering
    return {"documents": []}


@router.post("/")
async def create_document():
    return {"document_id": "doc_placeholder"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    tags: Optional[str] = Form("[]"),
    status: str = Form("draft"),
    metadata: Optional[str] = Form("{}"),
    service: DocumentService = Depends(get_document_service),
):
    """Upload a document file (Word, PDF, etc.) and store with versioning."""
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        tags_list = json.loads(tags) if tags else []
        metadata_dict = json.loads(metadata) if metadata else {}
        if not isinstance(tags_list, list):
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Tags and metadata must be valid JSON.",
        )

    chosen_title = title or Path(file.filename or "document").stem or "document"
    tmp_path = None
    extracted_text = ""
    try:
        suffix = Path(file.filename or "").suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)
        extracted_text, _ = extract_text_from_file(tmp_path)
    except Exception:
        # Fallback to decoding as text
        extracted_text = file_bytes.decode("utf-8", errors="ignore")
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink(missing_ok=True)

    file_format = (
        Path(file.filename or "").suffix.lstrip(".").lower() or "binary"
    )

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
    return result

