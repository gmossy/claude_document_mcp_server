# Mission Library – MCP Document Server

This directory packages the Claude-style document MCP server as a standalone, dockerized component for the Mission Library backend.

**Note**: This is a document library management system. Files are stored as binary files without parsing or conversion. The system focuses on file organization, versioning, and metadata management.

## Frontend

The frontend UI is located in a separate repository:

- **Repository**: `Physical-AI/Mission-Library`
- **Branch**: `dotmilpf-frontend`
- **URL**: `https://github.boozallencsn.com/Physical-AI/Mission-Library/tree/dotmilpf-frontend`

The frontend communicates with this backend via the FastAPI REST API endpoints.

## Project structure

```text
backend/
  mcp_document_server/
    document_mcp_server.py   # Main MCP server implementation
    document_parsers.py      # Multi-format document parsing utilities
    docs/                    # MCP/server docs
    document_storage/        # Runtime storage (created automatically)
    documents.db             # SQLite DB (created automatically)
    tests/                   # Test suite and sample files
    pyproject.toml           # Project configuration
    uv.lock                  # uv dependency lockfile
    Dockerfile               # Container image for this server
    README-mcp.md            # This file
```

### Local dev

```bash
cd backend/mcp_document_server
uv sync
uv run python document_mcp_server.py
```

### Test with MCP Inspector

Option A — Direct (no config)

```bash
cd <project-root>
npx @modelcontextprotocol/inspector python backend/mcp_document_server/document_mcp_server.py
```

Option B — Config file

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

```bash
npx @modelcontextprotocol/inspector --config inspector.config.json --server document-mcp
```

Then open the printed URL, ensure Transport Type is STDIO, click Connect, and select `document_mcp` to see tools.

### Docker

Build and run the containerized MCP server:

```bash
cd backend/mcp_document_server
docker build -t mission-mcp-document-server .
docker run --rm -it mission-mcp-document-server
```

### Database tables (auto-created)

- `documents` – main document records with metadata
- `document_versions` – version history per document
- `documents_fts` – FTS index for search
- `document_files` – on-disk exports tracked per version
- `document_binary` – raw uploaded files (binary blobs + metadata)
- `document_embeddings` – semantic chunks + embeddings (for text documents)

### File Upload

Files can be uploaded via the FastAPI REST API endpoint:

- `POST /api/v1/documents/upload` - Upload files (Word, Excel, PDF, OpenUSD, code, markdown, etc.)
- Files are stored as binary without parsing or conversion
- Automatic versioning on upload

```bash
cd backend/mcp_document_server
docker build -t mission-mcp-document-server .
docker run --rm -it mission-mcp-document-server
```

### JSON examples you can paste into MCP Inspector

All tools accept JSON. Below are ready-to-paste examples.

- List ALL documents (paginate, newest first)

```json
{
  "response_format": "json",
  "limit": 100,
  "offset": 0
}
```

Use the tool: `document_search` with the JSON above. Leave other fields empty to get everything.

- Search by keywords and tags

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

- Create a document

```json
{
  "title": "Q4 Report",
  "content": "Executive summary...\n\nHighlights...",
  "tags": ["finance", "2024"],
  "status": "draft",
  "metadata": { "author": "Glenn", "department": "Finance" }
}
```

- Get a document (with content and versions)

```json
{
  "document_id": "doc_abc123def456",
  "include_content": true,
  "include_versions": true,
  "response_format": "json"
}
```

- Update a document (creates version if content changes)

```json
{
  "document_id": "doc_abc123def456",
  "content": "Updated body...",
  "tags": ["finance", "2024", "reviewed"],
  "version_comment": "Added CFO notes"
}
```

- Delete vs archive

Archive (default):

```json
{ "document_id": "doc_abc123def456", "permanent": false }
```

Permanent delete:

```json
{ "document_id": "doc_abc123def456", "permanent": true }
```

- List all tags (top-used first)

```json
{
  "sort_by_count": true,
  "min_count": 1,
  "response_format": "json"
}
```

- Statistics overview

```json
{ "response_format": "json" }
```
