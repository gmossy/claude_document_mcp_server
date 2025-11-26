from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_version: str = "0.1.0"
    database_url: str = "sqlite:///./documents.db"
    storage_dir: str = "document_storage"
    allow_origins: list[str] = ["*"]

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


settings = Settings()

