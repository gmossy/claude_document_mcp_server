# MCP Server Testing Guide

## Overview

The MCP (Model Context Protocol) server can be tested in two ways:

1. **MCP Inspector** (Recommended) - Interactive testing with a web UI
2. **Automated Tests** - Programmatic testing via connectivity tests

## MCP Inspector (Recommended)

The MCP Inspector provides an interactive web interface to test your MCP server. This is the **recommended approach** for testing MCP servers.

### Setup

1. **Install MCP Inspector** (if not already installed):
   ```bash
   npm install -g @modelcontextprotocol/inspector
   ```

2. **Configuration File**: `config/inspector.config.json`
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

3. **Run Inspector**:
   ```bash
   npx @modelcontextprotocol/inspector --config config/inspector.config.json --server document-mcp
   ```

4. **Access Web UI**: The inspector will print a URL (typically `http://localhost:5173`)

### Using MCP Inspector

1. **Connect**: Open the printed URL in your browser
2. **Select Server**: Choose `document-mcp` from the server list
3. **Test Tools**: 
   - View all available tools (14 tools)
   - Test individual tools with sample inputs
   - View tool responses and outputs
4. **Interactive Testing**: 
   - Test document creation, search, updates, etc.
   - See real-time responses
   - Debug tool behavior

### Advantages of MCP Inspector

- ✅ **Interactive**: Test tools with real inputs
- ✅ **Visual**: See responses in a user-friendly format
- ✅ **Debugging**: Easy to identify issues
- ✅ **No Code Required**: Test without writing test scripts
- ✅ **Real-time**: See immediate results

## Automated Testing

For CI/CD and automated testing, we use connectivity tests:

### MCP Server Connectivity Test

**File**: `tests/test_mcp_connectivity.py`

**What it tests**:
- Server initialization
- Protocol version compatibility
- Tool registration (14 tools)
- Basic JSON-RPC communication

**Run**:
```bash
python3 tests/test_mcp_connectivity.py
```

**Output**:
```
✅ MCP Server Transport Test: PASSED
   Server name: document_mcp
   Server version: 1.21.1
   Protocol version: 2024-11-05
   Tools available: 14 tools
```

### When to Use Each Approach

| Use Case | Recommended Method |
|----------|-------------------|
| **Development & Debugging** | MCP Inspector (interactive) |
| **CI/CD Pipelines** | Automated connectivity tests |
| **Quick Verification** | Connectivity test script |
| **Learning MCP Tools** | MCP Inspector (see all tools) |
| **Testing Tool Logic** | MCP Inspector (test with real data) |

## Available MCP Tools

The document MCP server provides 14 tools:

1. `document_create` - Create new documents
2. `document_get` - Get document by ID
3. `document_update` - Update document metadata
4. `document_delete` - Delete documents
5. `document_search` - Search documents
6. `document_list` - List documents with filters
7. `document_analyze` - Analyze document content
8. `document_export` - Export to different formats
9. `document_version_list` - List document versions
10. `document_version_get` - Get specific version
11. `document_version_compare` - Compare versions
12. `document_statistics` - Get document statistics
13. `document_download_file` - Download binary file
14. `document_bulk_tag` - Bulk tag operations

## Testing Workflow

### Recommended Workflow

1. **Initial Setup**: Use MCP Inspector to verify server starts correctly
2. **Tool Testing**: Use MCP Inspector to test each tool interactively
3. **Integration**: Use connectivity test for CI/CD
4. **Debugging**: Use MCP Inspector when issues arise

### Example: Testing Document Creation

**Via MCP Inspector**:
1. Open MCP Inspector
2. Select `document-mcp` server
3. Choose `document_create` tool
4. Enter JSON input:
   ```json
   {
     "title": "Test Document",
     "content": "This is a test",
     "tags": ["test", "example"],
     "status": "draft"
   }
   ```
5. Click "Call Tool"
6. View response with document ID

**Via Connectivity Test**:
```bash
python3 tests/test_mcp_connectivity.py
# Verifies server responds and tools are registered
```

## Troubleshooting

### MCP Inspector Issues

**Problem**: Inspector can't connect to server
- **Solution**: Ensure `uv` is installed and `backend/mcp_document_server` has dependencies installed
- **Check**: Run `cd backend/mcp_document_server && uv sync`

**Problem**: Tools not showing up
- **Solution**: Check server logs for errors
- **Verify**: Run connectivity test to confirm tools are registered

### Connectivity Test Issues

**Problem**: Test fails with "No module named 'mcp'"
- **Solution**: Test requires `uv` environment - this is expected
- **Note**: The test uses `uv run` to ensure proper environment

## Conclusion

**For most use cases, MCP Inspector is the best choice** because:
- It's interactive and visual
- No code required
- Easy to test with real data
- Great for debugging

**Use automated tests for**:
- CI/CD pipelines
- Quick verification
- Regression testing

Both methods complement each other and serve different purposes in the testing workflow.

