# Document Management MCP Server

> **Created by Glenn Mossy**  
  *Booz Allen Hamilton
> *Sr. AI Software Developer & Data Scientist*  
> November 27, 2024

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A production-ready, enterprise-grade **Document Library Management System** with Model Context Protocol (MCP) server integration. Built with modern Python 3.13, this system provides comprehensive document storage, versioning, and search capabilities. Files are stored as-is (binary storage) with metadata management - no parsing or conversion is performed.

### Key Highlights

- **13 Production-Ready MCP Tools** for complete document lifecycle management
- **Multi-Format Support**: Word (.docx), Excel (.xlsx), PDF (.pdf), OpenUSD (.usd, .usda, .usdc), code files, and Markdown (.md)
- **Binary File Storage**: Files stored as-is without parsing or conversion
- **Automatic Versioning**: Complete document history with version tracking
- **Filename Search**: Search documents by filename, title, or metadata
- **RESTful API**: FastAPI endpoints for upload, delete, list, and search
- **Enterprise Features**: Bulk operations, analytics, and export capabilities
- **Robust Architecture**: SQLite with FTS5, async operations, comprehensive error handling

## Features

### Core Document Operations

- **Upload** files (Word, Excel, PDF, OpenUSD, code, markdown) - stored as binary files
- **List** documents with pagination, filtering by status/tags, and sorting
- **Search** by filename, title, or metadata
- **Delete** or archive documents (with permanent delete option)
- **Version** documents automatically on upload

### Advanced Capabilities

- **Filename Search**: Search documents by filename, title, or metadata fields
- **Tag-based filtering** with AND logic for precise results
- **Version control** with complete history and comparison tools
- **Binary file storage**: Files stored as-is in versioned directories
- **Metadata management**: Title, tags, status, and custom metadata
- **Multi-format export** (Markdown, TXT, code formats only - no conversion)
- **Bulk operations** for efficient tag management
- **Comprehensive statistics** and system monitoring

### Document Format Support

All file formats are supported for upload and storage:

- **Microsoft Word** (.docx) - Binary storage
- **PDF** (.pdf) - Binary storage
- **Microsoft Excel** (.xlsx) - Binary storage
- **OpenUSD** (.usd, .usda, .usdc) - Binary storage
- **Code files** (.py, .js, .cpp, etc.) - Binary storage
- **Markdown** (.md) - Binary storage
- **Any other format** - Binary storage

**Note**: This is a document library management system. Files are stored as-is without parsing, text extraction, or format conversion. The system focuses on file organization, versioning, and metadata management.

## Technical Architecture

### Technology Stack

- **Python 3.13** - Latest Python with performance improvements
- **FastAPI** - Modern async web framework for REST API
- **FastMCP** - Modern MCP server framework with async support
- **SQLite with FTS5** - Full-text search indexing for performance
- **Pydantic v2** - Type-safe data validation and serialization
- **Database Abstraction Layer** - SQLite and PostgreSQL adapters

### Design Patterns

- **Clean Architecture** - Separation of concerns with clear boundaries
- **Async/Await** - Non-blocking I/O for scalability
- **Type Safety** - Comprehensive type hints and Pydantic models
- **Error Handling** - Graceful degradation with detailed error messages
- **Version Control** - Automatic versioning with complete audit trail

### Code Quality

- **Comprehensive Testing** - Unit tests for all major components
- **Documentation** - Detailed docstrings and user guides
- **Type Checking** - Full mypy compatibility
- **Code Formatting** - Black and Ruff for consistency
- **Best Practices** - Following PEP 8 and modern Python standards

## Quick Start

### Installation

**Using UV (Recommended):**

```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to MCP document server subproject
cd backend/mcp_document_server

# Install Python 3.13 and sync dependencies
uv python install 3.13
uv venv --python 3.13
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync
```

**Using pip:**

```bash
cd backend/mcp_document_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .[dev]
```

### Running the Server

**MCP Server (for MCP clients):**

```bash
cd backend/mcp_document_server
source .venv/bin/activate  # or source venv/bin/activate
python document_mcp_server.py
```

The server will start and wait for MCP protocol messages on stdin/stdout. It's designed to be used with MCP clients like Claude Desktop or the MCP Inspector.

**FastAPI Server (for frontend/REST API):**

```bash
# Using Docker (recommended)
docker-compose up -d api

# Or directly with uvicorn
cd backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

The FastAPI server will be available at `http://localhost:8000` with:
- API endpoints: `http://localhost:8000/api/v1/`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/healthz`

### Testing the Server

#### Option 1: MCP Inspector (Recommended)

The MCP Inspector provides a web UI to interact with your server. Use one of the following:

#### Option A — Direct (no config, simplest)

```bash
cd <project-root>
npx @modelcontextprotocol/inspector python backend/mcp_document_server/document_mcp_server.py
```

#### Option B — Using an Inspector config file

1. Create `inspector.config.json` in the repo root:

```json
{
  "mcpServers": {
    "document-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "backend/mcp_document_server",
        "python",
        "document_mcp_server.py"
      ]
    }
  }
}
```

1. Start Inspector with that server:

```bash
cd <project-root>
npx @modelcontextprotocol/inspector --config inspector.config.json --server document-mcp
```

Then:

- Open the URL printed in the terminal (contains MCP_PROXY_AUTH_TOKEN).
- In the left panel, Transport Type should be STDIO. Click Connect.
- In the sidebar, select server `document_mcp` to see the tools.

**Troubleshooting:**

- If you see HTTP 404 or "Connection Error" when using Streamable HTTP, switch to STDIO and click Connect (this server does not expose /sse).
- If Inspector says the server isn't found, ensure your config uses the key `mcpServers` (not `servers`) and you passed `--config`.
- If you accidentally launched bare `npx` and dropped into `sh-3.2$`, type `exit` and run the full command.

### JSON examples you can paste into MCP Inspector

All tools accept JSON. Below are ready-to-paste examples for common tasks.

- List ALL documents (paginate, newest first) — use tool `document_search`

```json
{
  "response_format": "json",
  "limit": 100,
  "offset": 0
}
```

- Search by keywords and tags — use tool `document_search`

```json
{
  "query": "quarterly report",
  "tags": ["finance", "2024"],
  "status": "published",
  "limit": 20,
  "offset": 0,
  "response_format": "json"
}
```

- Create a document — use tool `document_create`

```json
{
  "title": "Q4 Report",
  "content": "Executive summary...\n\nHighlights...",
  "tags": ["finance", "2024"],
  "status": "draft",
  "metadata": { "author": "Glenn", "department": "Finance" }
}
```

- Get a document (with content and versions) — use tool `document_get`

```json
{
  "document_id": "doc_abc123def456",
  "include_content": true,
  "include_versions": true,
  "response_format": "json"
}
```

- Update a document (creates version if content changes) — use tool `document_update`

```json
{
  "document_id": "doc_abc123def456",
  "content": "Updated body...",
  "tags": ["finance", "2024", "reviewed"],
  "version_comment": "Added CFO notes"
}
```

- Archive vs permanently delete — use tool `document_delete`

Archive (default):

```json
{ "document_id": "doc_abc123def456", "permanent": false }
```

Permanent delete:

```json
{ "document_id": "doc_abc123def456", "permanent": true }
```

- List all tags — use tool `document_list_tags`

```json
{
  "sort_by_count": true,
  "min_count": 1,
  "response_format": "json"
}
```

- System statistics — use tool `document_statistics`

```json
{ "response_format": "json" }
```

#### Option 2: Manual Testing with Claude Desktop

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "document-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/backend/mcp_document_server/document_mcp_server.py"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/.venv/lib/python3.13/site-packages"
      }
    }
  }
}
```

Then restart Claude Desktop and the tools will be available.

#### Option 3: Quick Syntax Check

```bash
# Verify Python syntax
python -m py_compile document_mcp_server.py

# Check for import errors
python -c "import document_mcp_server; print('✓ Server loads successfully')"
```

### Quick Test Workflow

Once you have the server running in MCP Inspector:

1. **Create a document**:
   - Tool: `document_create`
   - Input: `{"title": "Test Doc", "content": "Hello world", "tags": ["test"]}`

2. **Search for it**:
   - Tool: `document_search`
   - Input: `{"query": "hello"}`

3. **Get statistics**:
   - Tool: `document_statistics`
   - Input: `{}`

4. **Analyze content**:
   - Tool: `document_analyze`
   - Input: `{"document_id": "<id_from_create>"}`

## Available Tools

### Document CRUD Operations

#### `document_create`

Create a new document with automatic versioning.

```json
{
  "title": "Q3 Financial Report",
  "content": "## Executive Summary\n\nThis quarter showed...",
  "tags": ["finance", "quarterly", "2024"],
  "status": "draft",
  "metadata": {
    "author": "Jane Smith",
    "department": "Finance"
  }
}
```

#### `document_get`

Retrieve a document with optional content and version history.

```json
{
  "document_id": "doc_abc123def456",
  "include_content": true,
  "include_versions": true,
  "response_format": "markdown"
}
```

#### `document_update`

Update document content, tags, or metadata with versioning.

```json
{
  "document_id": "doc_abc123def456",
  "content": "Updated content...",
  "tags": ["finance", "quarterly", "2024", "reviewed"],
  "version_comment": "Added review notes from CFO"
}
```

#### `document_delete`

Archive or permanently delete a document.

```json
{
  "document_id": "doc_abc123def456",
  "permanent": false
}
```

### Search and Discovery

#### `document_search`

Powerful search with full-text, tag filtering, and pagination.

```json
{
  "query": "financial report quarterly",
  "tags": ["finance"],
  "status": "published",
  "created_after": "2024-01-01T00:00:00Z",
  "sort_by": "updated_at",
  "sort_order": "desc",
  "limit": 20,
  "offset": 0,
  "response_format": "json"
}
```

#### `document_list_tags`

List all tags with usage counts.

```json
{
  "sort_by_count": true,
  "min_count": 1,
  "response_format": "markdown"
}
```

### Version Control

#### `document_get_version`

Retrieve a specific historical version.

```json
{
  "document_id": "doc_abc123def456",
  "version_number": 2,
  "response_format": "json"
}
```

#### `document_compare_versions`

Compare two versions to see changes.

```json
{
  "document_id": "doc_abc123def456",
  "version_a": 1,
  "version_b": 3
}
```

### Analysis and Export

#### `document_analyze`

Get content statistics and extract keywords.

```json
{
  "document_id": "doc_abc123def456",
  "include_stats": true,
  "include_keywords": true,
  "response_format": "markdown"
}
```

**Output includes:**

- Word count, character count
- Line and paragraph counts
- Average word length
- Estimated reading time
- Top 15 keywords

#### `document_export`

Export to Markdown, HTML, JSON, or plain text.

```json
{
  "document_id": "doc_abc123def456",
  "format": "html",
  "include_metadata": true
}
```

### Bulk Operations

#### `document_bulk_tag`

Add or remove tags from multiple documents.

```json
{
  "document_ids": ["doc_abc123", "doc_def456", "doc_ghi789"],
  "add_tags": ["reviewed", "2024"],
  "remove_tags": ["draft"]
}
```

### System Monitoring

#### `document_statistics`

Get comprehensive system statistics.

```json
{
  "response_format": "markdown"
}
```

**Provides:**

- Total documents and storage usage
- Status distribution (draft/published/archived)
- Version statistics
- Recent activity
- Most versioned documents

## Data Model

### Document Structure

```json
{
  "id": "doc_abc123def456",
  "title": "Document Title",
  "content": "Document content in markdown or plain text",
  "tags": ["tag1", "tag2"],
  "status": "draft|published|archived",
  "metadata": {"key": "value"},
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-16T14:20:00Z",
  "size": 1234,
  "content_hash": "sha256_hash"
}
```

### Version Structure

```json
{
  "document_id": "doc_abc123def456",
  "version_number": 1,
  "title": "Title at this version",
  "content": "Content at this version",
  "tags": ["tags", "at", "version"],
  "status": "status_at_version",
  "metadata": {},
  "created_at": "2024-01-15T10:30:00Z",
  "comment": "Version change description",
  "content_hash": "sha256_hash"
}
```

## Response Formats

All data-returning tools support two formats:

### Markdown (default)

Human-readable format with headers, lists, and formatting:

```markdown
# Document Analysis

**Document**: Q3 Financial Report
**ID**: `doc_abc123def456`

## Statistics

- **Word Count**: 1,234
- **Estimated Reading Time**: 6 minutes
...
```

### JSON

Machine-readable structured data:

```json
{
  "document_id": "doc_abc123def456",
  "title": "Q3 Financial Report",
  "stats": {
    "word_count": 1234,
    "reading_time_minutes": 6
  }
}
```

## Database Schema

The server uses SQLite with the following tables:

1. **documents** - Main document storage
2. **document_versions** - Version history
3. **documents_fts** - Full-text search index (FTS5)
4. **document_files** - Versioned export artifacts stored on disk
5. **document_binary** - Raw uploaded files (binary BLOBs) with metadata
6. **document_embeddings** - Text chunks + vector embeddings for semantic search

Database and document storage are automatically initialized on first run.

## Configuration

Default constants (configurable in source):

- `DATABASE_PATH`: `./documents.db`
- `DOCUMENTS_DIR`: `./document_storage`
- `MAX_CONTENT_SIZE`: 10MB
- `MAX_TAGS`: 50 per document
- `MAX_SEARCH_RESULTS`: 100
- `DEFAULT_PAGE_SIZE`: 20

## Best Practices

### Tool Annotations

All tools include MCP annotations:

- `readOnlyHint`: Whether the tool modifies data
- `destructiveHint`: Whether it performs destructive operations
- `idempotentHint`: Whether repeated calls have the same effect
- `openWorldHint`: Whether it interacts with external services

### Error Handling

All tools return structured error responses with:

- Clear error messages
- Specific suggestions for resolution
- Consistent JSON format

### Pagination

Search tools support pagination with:

- `limit`: Results per page (1-100)
- `offset`: Skip count for pagination
- Response includes `has_more` and `next_offset`

## FastAPI REST API

The system provides a RESTful API for document management. The API is designed for frontend integration and supports standard HTTP methods with JSON responses.

### Quick Start

```bash
# Start the API server
docker-compose up -d api

# Or run directly
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

The API automatically initializes the database schema on startup. All endpoints are available at `http://localhost:8000/api/v1/`.

### Endpoints

#### Upload Document

```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: <binary file>
title: "Optional title"
tags: '["tag1", "tag2"]'
status: "draft"
metadata: '{"author": "John Doe"}'
```

**Supported file types**: Word (.docx), Excel (.xlsx), PDF (.pdf), OpenUSD (.usd, .usda, .usdc), code files (.py, .js, .cpp, etc.), Markdown (.md), and any other format.

**Response**: Document ID, version number, binary file metadata, and document information.

**Frontend Integration**: This endpoint accepts standard `multipart/form-data` uploads, making it compatible with HTML file input elements and drag-and-drop interfaces.

#### List Documents

```http
GET /api/v1/documents/?status=draft&tags=tag1,tag2&limit=50&offset=0&order_by=created_at&order_desc=true
```

**Features**: Pagination, filtering by status/tags, sorting.

#### Search by Filename

```http
GET /api/v1/search/?q=report.pdf&limit=50
```

**Searches**: Document titles, stored filenames, and metadata.

#### Delete Document

```http
DELETE /api/v1/documents/{document_id}?permanent=false
```

**Options**: Archive (default) or permanent delete.

#### Health Check

```http
GET /api/v1/healthz
```

### Example API Usage

**Upload a Word document:**

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@report.docx" \
  -F "title=Q4 Report" \
  -F "tags=[\"finance\", \"2024\"]" \
  -F "status=draft"
```

**Search for files:**

```bash
curl "http://localhost:8000/api/v1/search/?q=report.pdf&limit=10"
```

**List all documents:**

```bash
curl "http://localhost:8000/api/v1/documents/?limit=50&offset=0"
```

**Delete a document:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/doc_abc123?permanent=false"
```

## Integration Examples

### Claude Desktop Configuration

Add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "document-mcp": {
      "command": "python",
      "args": ["/path/to/document_mcp_server.py"]
    }
  }
}
```

### Example Workflows

**Uploading and Managing Files:**

1. Upload a document via API: `POST /api/v1/documents/upload`
2. Search for files: `GET /api/v1/search/?q=filename`
3. List documents: `GET /api/v1/documents/`
4. Archive document: `DELETE /api/v1/documents/{id}`

**Organizing Documents:**

1. `document_search` - Find related documents
2. `document_bulk_tag` - Apply consistent tags
3. `document_list_tags` - Review tag organization

**Reviewing Changes:**

1. `document_get` - Get current version with history
2. `document_compare_versions` - See what changed
3. `document_get_version` - Retrieve specific version

## Frontend

The frontend UI is located in a separate repository:

- **Repository**: `Physical-AI/Mission-Library`
- **Branch**: `dotmilpf-frontend`
- **URL**: `https://github.boozallencsn.com/Physical-AI/Mission-Library/tree/dotmilpf-frontend`

The frontend communicates with this backend via the FastAPI REST API endpoints documented above.

## Development

### Project Structure

```text
backend/
  mcp_document_server/
    document_mcp_server.py    # Main MCP server implementation
    document_parsers.py       # Document parsing utilities (Word, PDF, Excel, PPTX, etc.)
    docs/                     # MCP/server docs
    document_storage/         # Storage directory (auto-created)
    documents.db              # SQLite database (auto-created)
    tests/                    # Test suite and sample office files
    pyproject.toml            # MCP server project configuration
    uv.lock                   # uv dependency lockfile
    Dockerfile                # Container image for this server
    README-mcp.md             # Subproject README

  app/                        # FastAPI application
    main.py                   # FastAPI entrypoint
    config.py                 # Settings (env-driven)
    api/
      deps.py                 # Shared dependencies
      v1/router.py            # Versioned API router
      v1/endpoints/           # auth, documents, search, analytics, health
    models/                   # Pydantic/SQLAlchemy models

dist/
  document_mcp-*.whl, *.tar.gz # Built artifacts
```

### Frontend Integration

The frontend UI connects to this backend API at:

- **Base URL**: `http://localhost:8000/api/v1` (development)
- **Health Check**: `GET /api/v1/healthz`
- **Document Upload**: `POST /api/v1/documents/upload`
- **Document List**: `GET /api/v1/documents/`
- **Search**: `GET /api/v1/search/?q=filename`
- **Delete**: `DELETE /api/v1/documents/{id}`

### Development Standards

The codebase follows:

- PEP 8 style guidelines
- Type hints throughout
- Pydantic v2 for validation
- Comprehensive docstrings
- DRY principles with shared utilities

### Testing

```bash
# Install dev dependencies
pip install -e .[dev]

# Run linting
ruff check .
black --check .
mypy .
```

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome! Please ensure:

1. Code follows existing patterns
2. All tools have proper annotations
3. Input validation uses Pydantic
4. Error messages are actionable
5. Documentation is updated

## Project Metrics

- **Lines of Code**: 7,300+
- **Test Coverage**: Comprehensive unit and integration tests
- **Documentation**: Detailed guides + inline documentation
- **Supported Formats**: All file formats (binary storage)
- **MCP Tools**: 13 production-ready endpoints
- **REST API Endpoints**: 6+ FastAPI endpoints
- **Dependencies**: Minimal, well-maintained packages
- **Performance**: Sub-second response for most operations

## Skills Demonstrated

This project showcases proficiency in:

### Software Engineering

- **Clean Code Architecture** - Modular design with clear separation of concerns
- **API Design** - RESTful principles applied to MCP tool design
- **Database Design** - Efficient schema with FTS5 indexing
- **Error Handling** - Comprehensive exception handling and validation
- **Documentation** - Professional-grade documentation and examples

### Data Science & AI

- **Document Management** - Binary file storage with metadata
- **Search & Retrieval** - Filename and metadata search
- **Content Analysis** - Statistical analysis and keyword extraction (for text documents)
- **Version Control** - Data versioning and diff algorithms
- **AI Integration** - MCP protocol for LLM tool use

### Modern Python

- **Python 3.13** - Latest language features and optimizations
- **Async Programming** - Non-blocking I/O with asyncio
- **Type Safety** - Comprehensive type hints and Pydantic validation
- **Package Management** - Modern tooling with UV
- **Testing** - Unit tests and integration testing

### DevOps & Tools

- **Git** - Version control and repository management
- **Virtual Environments** - Dependency isolation
- **CI/CD Ready** - Structured for automated deployment
- **Cross-Platform** - Works on macOS, Linux, and Windows

## About the Creator

**Glenn Mossy** is a Senior AI Software Developer and Data Scientist with expertise in building production-ready AI systems. This project demonstrates the ability to:

- Design and implement complex systems from scratch
- Write clean, maintainable, and well-documented code
- Integrate multiple technologies into cohesive solutions
- Follow software engineering best practices
- Deliver enterprise-grade applications

### Contact & Links

- **Project Date**: November 27, 2024
- **Role**: Creator & Lead Developer

## Acknowledgments

Built following the [Model Context Protocol](https://modelcontextprotocol.io/) specification and best practices.

---

*This project serves as a portfolio piece demonstrating advanced software engineering, AI integration, and data science capabilities.*
