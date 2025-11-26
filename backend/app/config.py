"""Application configuration with environment variable support.

Configuration can be set via environment variables or a .env file.
The .env file should be placed in the project root directory.

Example .env file:
    DATABASE_URL=sqlite:///./documents.db
    STORAGE_DIR=document_storage
    API_VERSION=0.1.0
    ALLOW_ORIGINS=["*"]

For PostgreSQL:
    DATABASE_URL=postgresql://user:password@localhost:5432/dbname
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support.

    All settings can be overridden via environment variables or .env file.
    """

    api_version: str = "0.1.0"
    """API version string."""

    database_url: str = "sqlite:///./documents.db"
    """Database connection URL.
    
    Supported formats:
    - SQLite: sqlite:///path/to/database.db
    - PostgreSQL: postgresql://user:password@host:port/dbname
    """

    storage_dir: str = "document_storage"
    """Directory for storing exported document files."""

    allow_origins: list[str] = ["*"]
    """CORS allowed origins."""

    log_level: str = "INFO"
    """Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


settings = Settings()

