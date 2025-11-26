"""Health check endpoint.

Provides health status and system information endpoints.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status", examples=["ok", "degraded", "down"])


@router.get(
    "/healthz",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API service. Returns 'ok' if the service is healthy and operational.",
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok"
                    }
                }
            }
        },
        503: {
            "description": "Service is unavailable",
            "content": {
                "application/json": {
                    "example": {
                        "status": "down",
                        "message": "Database connection failed"
                    }
                }
            }
        }
    }
)
async def healthz():
    """
    Health check endpoint.

    Returns the current health status of the API service.
    This endpoint can be used by monitoring systems and load balancers
    to check if the service is operational.
    """
    return {"status": "ok"}

