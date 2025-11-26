"""API v1 router configuration.

This module aggregates all v1 API endpoints into a single router.
"""

from fastapi import APIRouter

from .endpoints import auth, documents, search, analytics, health, tags

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(documents.router, prefix="/documents", tags=["documents"])
v1_router.include_router(search.router, prefix="/search", tags=["search"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
v1_router.include_router(tags.router, prefix="/tags", tags=["tags"])

