from fastapi import FastAPI

from .config import settings
from .api.v1.router import v1_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Mission Library API",
        version=settings.api_version,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Include versioned router
    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/healthz", tags=["health"])
    async def healthz():
        return {"status": "ok"}

    return app


app = create_app()

