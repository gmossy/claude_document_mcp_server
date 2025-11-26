from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ....api.deps import get_document_service
from backend.core.services import DocumentService

router = APIRouter()


@router.get("/")
async def search_documents():
    return {"results": []}


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.post("/semantic")
async def semantic_search(
    payload: SemanticSearchRequest,
    service: DocumentService = Depends(get_document_service),
):
    results = service.semantic_search(payload.query, payload.limit)
    return {"results": results}

