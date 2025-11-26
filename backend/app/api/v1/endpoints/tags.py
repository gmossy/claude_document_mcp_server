"""Tag management endpoints.

Provides operations for listing and managing document tags.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.core.services import DocumentService
from backend.app.api.deps import get_document_service

logger = logging.getLogger(__name__)

router = APIRouter()


class TagItem(BaseModel):
    """Tag with usage count."""
    tag: str = Field(..., description="Tag name", examples=["ai-testing"])
    count: int = Field(..., description="Number of documents with this tag", examples=[5])


class TagsListResponse(BaseModel):
    """Response model for listing tags."""
    tags: list[TagItem] = Field(
        ...,
        description="List of tags with usage counts",
        examples=[[{"tag": "ai-testing", "count": 5}, {"tag": "engineering", "count": 3}]]
    )
    total: int = Field(..., description="Total number of unique tags", examples=[10])


@router.get(
    "/",
    response_model=TagsListResponse,
    summary="List all tags",
    description=(
        "Retrieve a list of all tags used in the system with their usage counts. "
        "Supports filtering by minimum count and sorting options."
    ),
    responses={
        200: {
            "description": "List of tags retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "tags": [
                            {"tag": "ai-testing", "count": 5},
                            {"tag": "engineering", "count": 3},
                            {"tag": "finance", "count": 2}
                        ],
                        "total": 3
                    }
                }
            }
        }
    }
)
async def list_tags(
    sort_by_count: bool = Query(
        True,
        description="Sort by usage count (true) or alphabetically (false)",
        examples=[True, False]
    ),
    min_count: int = Query(
        1,
        ge=0,
        description="Minimum number of documents required for tag to be included",
        examples=[1, 2, 5]
    ),
    service: DocumentService = Depends(get_document_service),
):
    """
    List all tags with their usage counts.

    Returns tags sorted by usage count (descending) or alphabetically,
    filtered by minimum usage count.

    Example:
        GET /api/v1/tags/?sort_by_count=true&min_count=2
    """
    logger.info(
        "Listing tags: sort_by_count=%s, min_count=%s",
        sort_by_count, min_count
    )

    try:
        # Get all documents to extract tags
        all_docs = service.list_documents(limit=10000)
        tag_counts: dict[str, int] = {}

        for doc in all_docs["documents"]:
            tags = doc.get("tags", [])
            for tag in tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Filter by min_count
        filtered_tags = {
            tag: count
            for tag, count in tag_counts.items()
            if count >= min_count
        }

        # Sort
        if sort_by_count:
            sorted_tags = sorted(
                filtered_tags.items(), key=lambda x: x[1], reverse=True
            )
        else:
            sorted_tags = sorted(filtered_tags.items())

        tag_list = [{"tag": tag, "count": count} for tag, count in sorted_tags]

        logger.info("Listed %s tags", len(tag_list))
        return {
            "tags": tag_list,
            "total": len(tag_list)
        }
    except Exception as e:
        logger.error("Error listing tags: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list tags") from e

