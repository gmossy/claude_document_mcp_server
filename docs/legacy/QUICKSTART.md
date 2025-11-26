# Quick Start Guide

## 1. Setup (One Time)

```bash
# Activate virtual environment
source .venv/bin/activate

# Verify installation
./test_server.sh
```

## 2. Run the Server

### Option A: With MCP Inspector (Best for Testing)

```bash
npx @modelcontextprotocol/inspector python document_mcp_server.py
```

Opens web UI at http://localhost:5173

### Option B: With Claude Desktop

1. Edit config file:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

2. Add this configuration:

```json
{
  "mcpServers": {
    "document-mcp": {
      "command": "python",
      "args": ["/Volumes/My Book8TB-6TB Partition/claude_document_mcp_server/document_mcp_server.py"]
    }
  }
}
```

3. Restart Claude Desktop

### Option C: Direct (For Integration)

```bash
python document_mcp_server.py
```

Server runs on stdio, waiting for MCP protocol messages.

## 3. Test It

In MCP Inspector or Claude, try:

**Create a document:**
```json
{
  "title": "Test Document",
  "content": "Hello world!",
  "tags": ["test"]
}
```

**Search for it:**
```json
{
  "query": "hello"
}
```

**Get stats:**
```json
{}
```

## Available Tools (13 Total)

- `document_create` - Create new document
- `document_get` - Retrieve document
- `document_update` - Update document
- `document_delete` - Delete/archive document
- `document_search` - Full-text search
- `document_list_tags` - List all tags
- `document_get_version` - Get specific version
- `document_compare_versions` - Compare versions
- `document_analyze` - Analyze content
- `document_export` - Export to formats
- `document_bulk_tag` - Bulk tag operations
- `document_statistics` - System statistics

## Files Created

- `documents.db` - SQLite database (auto-created)
- `document_storage/` - Document files (auto-created)

## Troubleshooting

**Server won't start?**
```bash
source .venv/bin/activate
uv sync
python -c "import document_mcp_server"
```

**Tools not in Claude Desktop?**
- Check config file path
- Use absolute paths
- Restart Claude Desktop

**Need more help?**
- See `TESTING.md` for detailed testing guide
- See `README.md` for full documentation
