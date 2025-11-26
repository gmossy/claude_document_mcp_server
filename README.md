# Document Management MCP Server

> **Created by Glenn Mossy**  
  *Booz Allen Hamilton
> *Sr. AI Software Developer & Data Scientist*  
> November 27, 2024

[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0+-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

A production-ready, enterprise-grade Model Context Protocol (MCP) server that provides AI assistants with comprehensive document management capabilities. Built with modern Python 3.13, this server demonstrates advanced software engineering practices including clean architecture, comprehensive testing, and multi-format document processing.

### Key Highlights

- **13 Production-Ready MCP Tools** for complete document lifecycle management
- **Multi-Format Support**: Word (.docx), PDF, Excel (.xlsx), Markdown, and plain text
- **Advanced Search**: Full-text search with FTS5 indexing and semantic filtering
- **Version Control**: Complete document history with diff comparison
- **Enterprise Features**: Bulk operations, analytics, and export capabilities
- **Robust Architecture**: SQLite with FTS5, async operations, comprehensive error handling

## Features

### Core Document Operations
- **Create** documents with titles, content, tags, metadata, and status
- **Read** documents with optional version history
- **Update** documents with automatic versioning
- **Delete** or archive documents safely

### Advanced Capabilities
- **Full-text search** with FTS5 indexing across titles and content
- **Tag-based filtering** with AND logic for precise results
- **Version control** with complete history and comparison tools
- **Content analysis** including word count, reading time, and keyword extraction
- **Multi-format export** (Markdown, HTML, JSON, TXT, Word, PDF, Excel)
- **Bulk operations** for efficient tag management
- **Comprehensive statistics** and system monitoring

### Document Format Support
- **Microsoft Word** (.docx) - Read and write with metadata extraction
- **PDF** - Read and create with multi-page support
- **Microsoft Excel** (.xlsx) - Multi-sheet extraction and creation
- **Microsoft PowerPoint** (.pptx) - Slide extraction and presentation creation
- **Markdown** (.md) - Full support with formatting
- **Plain Text** (.txt) - Universal compatibility

## Technical Architecture

### Technology Stack
- **Python 3.13** - Latest Python with performance improvements
- **FastMCP** - Modern MCP server framework with async support
- **SQLite with FTS5** - Full-text search indexing for performance
- **Pydantic v2** - Type-safe data validation and serialization
- **openpyxl** - Excel file processing
- **python-docx** - Word document manipulation
- **python-pptx** - PowerPoint presentation handling
- **pypdf & reportlab** - PDF reading and generation

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

The server runs using stdio transport for MCP communication:

```bash
cd backend/mcp_document_server
source .venv/bin/activate  # or source venv/bin/activate
python document_mcp_server.py
```

The server will start and wait for MCP protocol messages on stdin/stdout. It's designed to be used with MCP clients like Claude Desktop or the MCP Inspector.

### Testing the Server

**Option 1: MCP Inspector (Recommended)**

The MCP Inspector provides a web UI to interact with your server. Use one of the following:

Option A — Direct (no config, simplest)

```bash
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server
npx @modelcontextprotocol/inspector python backend/mcp_document_server/document_mcp_server.py
```

Option B — Using an Inspector config file

1) Create `inspector.config.json` in the repo root:

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

2) Start Inspector with that server:

```bash
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server
npx @modelcontextprotocol/inspector --config inspector.config.json --server document-mcp
```

Then:
- Open the URL printed in the terminal (contains MCP_PROXY_AUTH_TOKEN).
- In the left panel, Transport Type should be STDIO. Click Connect.
- In the sidebar, select server `document_mcp` to see the tools.

Troubleshooting:
- If you see HTTP 404 or “Connection Error” when using Streamable HTTP, switch to STDIO and click Connect (this server does not expose /sse).
- If Inspector says the server isn’t found, ensure your config uses the key `mcpServers` (not `servers`) and you passed `--config`.
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

**Option 2: Manual Testing with Claude Desktop**

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

**Option 3: Quick Syntax Check**

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

**Creating and Publishing a Report:**
1. `document_create` - Create initial draft
2. `document_update` - Add content revisions
3. `document_analyze` - Check statistics
4. `document_update` - Set status to "published"

**Organizing Documents:**
1. `document_search` - Find related documents
2. `document_bulk_tag` - Apply consistent tags
3. `document_list_tags` - Review tag organization

**Reviewing Changes:**
1. `document_get` - Get current version with history
2. `document_compare_versions` - See what changed
3. `document_get_version` - Retrieve specific version

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

dist/
  document_mcp-*.whl, *.tar.gz # Built artifacts
```

### Code Quality
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
- **Documentation**: 5 detailed guides + inline documentation
- **Supported Formats**: 5 (Word, PDF, Excel, Markdown, Text)
- **MCP Tools**: 13 production-ready endpoints
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
- **Document Processing** - Multi-format parsing and text extraction
- **Search & Retrieval** - Full-text search with ranking algorithms
- **Content Analysis** - Statistical analysis and keyword extraction
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

- **Project Date**: November 26, 2024
- **Role**: Creator & Lead Developer

## Acknowledgments

Built following the [Model Context Protocol](https://modelcontextprotocol.io/) specification and best practices.

---

*This project serves as a portfolio piece demonstrating advanced software engineering, AI integration, and data science capabilities.*
