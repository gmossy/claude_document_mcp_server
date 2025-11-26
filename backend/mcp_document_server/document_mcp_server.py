#!/usr/bin/env python3
"""
Document Management MCP Server

A comprehensive MCP server for document management with features including:
- Document CRUD operations with versioning
- Full-text search with highlighting
- Tagging and categorization
- Content analysis and summarization
- Export to multiple formats
- Batch operations
"""

import sys
from contextlib import asynccontextmanager
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Ensure repository root is importable for shared services
SCRIPT_DIR = Path(__file__).parent.absolute()
REPO_ROOT = SCRIPT_DIR.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# pylint: disable=wrong-import-position
from backend.core.db import SQLiteAdapter
from backend.core.services.documents import DocumentService

# Models and formatters are imported by tools when needed

# ============================================================================
# Constants
# ============================================================================

DATABASE_PATH = SCRIPT_DIR / "documents.db"
DOCUMENTS_DIR = SCRIPT_DIR / "document_storage"

# Initialize database adapter and service
db_adapter = SQLiteAdapter(DATABASE_PATH)
document_service = DocumentService(db_adapter, DOCUMENTS_DIR)

# ============================================================================
# Database Management
# ============================================================================


def init_database():
    """Initialize the database with required tables using the adapter.

    Uses the database adapter to create all necessary tables, indexes,
    and triggers. This function is database-agnostic and works with
    any adapter implementation (SQLite, PostgreSQL, etc.).
    """
    conn = db_adapter.connect()
    try:
        db_adapter.init_schema(conn)
    finally:
        db_adapter.close(conn)


# ============================================================================
# Lifespan Management
# ============================================================================


@asynccontextmanager
async def app_lifespan(_app):
    """Manage application lifecycle."""
    # Initialize database and storage
    DOCUMENTS_DIR.mkdir(parents=True, exist_ok=True)
    init_database()

    yield {}


# ============================================================================
# MCP Server Initialization
# ============================================================================

mcp = FastMCP("document_mcp", lifespan=app_lifespan)

# Import and register all MCP tools
from backend.mcp_document_server.mcp_tools import register_tools

register_tools(mcp)

# ============================================================================
# Server Entry Point
# ============================================================================

if __name__ == "__main__":
    mcp.run()
