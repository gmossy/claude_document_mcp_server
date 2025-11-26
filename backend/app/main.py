"""FastAPI application entry point.

This module initializes the FastAPI application and registers
all API routers and middleware.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from backend.app.config import settings
from backend.app.api.v1.router import v1_router
from backend.app.logging_config import setup_logging
from backend.app.api.deps import db_adapter

# Setup logging before creating the app
setup_logging(settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("Initializing database schema...")
    conn = db_adapter.connect()
    try:
        db_adapter.init_schema(conn)
        db_adapter.commit(conn)
        logger.info("Database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
    finally:
        db_adapter.close(conn)
    
    yield
    
    # Cleanup on shutdown (if needed)
    logger.info("Shutting down application...")


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., description="Health status", examples=["ok"])


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    logger.info("Creating FastAPI application")
    logger.info("API version: %s", settings.api_version)
    logger.info("Database URL: %s", settings.database_url)

    application = FastAPI(
        title="Mission Library API",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Configure CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("CORS middleware configured with origins: %s", settings.allow_origins)

    # Include versioned router
    application.include_router(v1_router, prefix="/api/v1")
    logger.info("API routers registered")

    @application.get(
        "/healthz",
        tags=["health"],
        response_model=HealthResponse,
        summary="Root health check",
        description=(
            "Check the health status of the API service at the root level. "
            "Returns 'ok' if the service is healthy and operational."
        ),
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
            }
        }
    )
    async def healthz():
        """
        Root health check endpoint.

        Returns the current health status of the API service.
        This endpoint can be used by monitoring systems and load balancers
        to check if the service is operational.
        """
        logger.debug("Health check requested")
        return {"status": "ok"}

    return application


app = create_app()

