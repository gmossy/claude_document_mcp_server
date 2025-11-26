# Testing Guide for Document MCP Server

## Prerequisites

1. **Activate your virtual environment**:
   ```bash
   source .venv/bin/activate
   ```

2. **Verify installation**:
   ```bash
   ./test_server.sh
   ```

## Testing Methods

### Method 1: MCP Inspector (Recommended for Interactive Testing)

The MCP Inspector provides a web-based UI to test all server tools:

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run the inspector
npx @modelcontextprotocol/inspector python document_mcp_server.py
```

**What happens:**
- Opens browser at http://localhost:5173
- Shows all available tools in a sidebar
- Lets you call tools with JSON inputs
- Displays responses in real-time
- Great for exploring and debugging

**Try these test cases:**

1. **Create a document**:
   ```json
   {
     "title": "My First Document",
     "content": "This is a test document with some content.",
     "tags": ["test", "demo"],
     "status": "draft"
   }
   ```
   Tool: `document_create`

2. **Search for it**:
   ```json
   {
     "query": "test",
     "response_format": "json"
   }
   ```
   Tool: `document_search`

3. **Get statistics**:
   ```json
   {
     "response_format": "markdown"
   }
   ```
   Tool: `document_statistics`

4. **Analyze the document**:
   ```json
   {
     "document_id": "<paste_id_from_create>",
     "include_stats": true,
     "include_keywords": true
   }
   ```
   Tool: `document_analyze`

### Method 2: Claude Desktop Integration

**Step 1: Find your config file**

- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

**Step 2: Add server configuration**

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

**Step 3: Restart Claude Desktop**

**Step 4: Test in Claude**

Ask Claude things like:
- "Create a document about Python testing"
- "Search for documents about testing"
- "Show me document statistics"
- "Analyze the document we just created"

### Method 3: Direct Server Testing

Run the server directly to see if it starts without errors:

```bash
# Activate environment
source .venv/bin/activate

# Run server
python document_mcp_server.py
```

**Expected behavior:**
- Server starts silently
- Waits for stdin input (MCP protocol messages)
- No output unless there's an error
- Press Ctrl+C to stop

**If you see errors:**
- Check that all dependencies are installed: `uv sync`
- Verify Python version: `python --version` (should be 3.13.x)
- Check for syntax errors: `python -m py_compile document_mcp_server.py`

## Common Test Workflows

### Workflow 1: Document Lifecycle

1. Create a draft document
2. Update it with more content
3. Analyze the content
4. Update status to "published"
5. Search for it
6. Compare versions

### Workflow 2: Bulk Operations

1. Create multiple documents
2. Use `document_bulk_tag` to tag them all
3. Search by tags
4. List all tags with counts

### Workflow 3: Version Control

1. Create a document
2. Update it several times with version comments
3. Get the document with version history
4. Compare different versions
5. Retrieve a specific old version

## Troubleshooting

### Server won't start

```bash
# Check Python version
python --version  # Should be 3.13.x

# Reinstall dependencies
uv sync

# Check for import errors
python -c "import document_mcp_server"
```

### Tools not appearing in Claude Desktop

1. Check config file path is correct
2. Use absolute paths in config
3. Restart Claude Desktop completely
4. Check Claude Desktop logs for errors

### MCP Inspector connection issues

```bash
# Make sure no other process is using port 5173
lsof -i :5173

# Try running inspector with verbose output
npx @modelcontextprotocol/inspector python document_mcp_server.py --verbose
```

## Database and Storage

The server creates these automatically on first run:

- `documents.db` - SQLite database
- `document_storage/` - Document content directory

**To reset everything:**
```bash
rm documents.db
rm -rf document_storage/
# Server will recreate on next run
```

## Performance Testing

For testing with many documents:

```python
# Create test_bulk.py
import json
import subprocess

for i in range(100):
    doc = {
        "title": f"Test Document {i}",
        "content": f"Content for document {i}" * 100,
        "tags": [f"tag{i % 10}", "test"]
    }
    # Use MCP Inspector or write custom test client
```

## Next Steps

After basic testing works:

1. Try all 13 tools in the inspector
2. Test error cases (invalid IDs, missing fields)
3. Test pagination with many documents
4. Test version comparison features
5. Export documents in different formats
6. Test search with complex queries

## Getting Help

If you encounter issues:

1. Check the main README.md for configuration details
2. Review error messages carefully
3. Test with MCP Inspector first before Claude Desktop
4. Verify all dependencies are installed
5. Check that database and storage directories are writable
