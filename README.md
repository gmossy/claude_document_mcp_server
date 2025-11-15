# Document Management MCP Server

A comprehensive Model Context Protocol (MCP) server for document management, providing AI assistants with powerful tools to create, search, version, and analyze documents.

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
- **Multi-format export** (Markdown, HTML, JSON, TXT)
- **Bulk operations** for efficient tag management
- **Comprehensive statistics** and system monitoring

## Quick Start

### Installation

**Using UV (Recommended):**
```bash
# Install UV if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Navigate to project directory
cd document_mcp_server

# Install Python 3.13 and create virtual environment
uv python install 3.13
uv venv --python 3.13

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

**Using pip:**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Or install dependencies directly
pip install mcp pydantic httpx
```

### Running the Server

The server runs using stdio transport for MCP communication:

```bash
# Activate your virtual environment first
source .venv/bin/activate  # or source venv/bin/activate

# Run the server
python document_mcp_server.py
```

The server will start and wait for MCP protocol messages on stdin/stdout. It's designed to be used with MCP clients like Claude Desktop or the MCP Inspector.

### Testing the Server

**Option 1: MCP Inspector (Recommended)**

The MCP Inspector provides a web UI to interact with your server:

```bash
# Install and run MCP Inspector
npx @modelcontextprotocol/inspector python document_mcp_server.py
```

This will:
1. Start your MCP server
2. Open a web interface at http://localhost:5173
3. Let you test all tools interactively with a visual interface

**Option 2: Manual Testing with Claude Desktop**

Add to your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "document-mcp": {
      "command": "python",
      "args": ["/absolute/path/to/document_mcp_server.py"],
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
```
document_mcp/
├── document_mcp_server.py    # Main server implementation
├── pyproject.toml            # Project configuration
├── README.md                 # This file
├── documents.db              # SQLite database (auto-created)
└── document_storage/         # Storage directory (auto-created)
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

## Acknowledgments

Built following the [Model Context Protocol](https://modelcontextprotocol.io/) specification and best practices.
