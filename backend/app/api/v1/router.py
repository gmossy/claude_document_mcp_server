from fastapi import APIRouter

from .endpoints import auth, documents, search, analytics, health

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(auth.router, prefix="/auth", tags=["auth"])
v1_router.include_router(documents.router, prefix="/documents", tags=["documents"])
v1_router.include_router(search.router, prefix="/search", tags=["search"])
v1_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

