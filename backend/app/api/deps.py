from collections.abc import Generator
import sqlite3
from pathlib import Path

from ..config import settings
from backend.core.services import DocumentService

db_path = Path(settings.database_url.replace("sqlite:///", ""))
storage_dir = Path(settings.storage_dir)
document_service = DocumentService(db_path, storage_dir)


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def get_document_service() -> DocumentService:
    return document_service

