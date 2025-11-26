What I just did
From the MCP project directory, I started the server once via CLI:
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server/backend/mcp_document_server
uv run python document_mcp_server.py
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server/backend/mcp_document_serveruv run python document_mcp_server.py
It ran successfully and printed the banner to stderr:
Starting Document Management MCP Server 'document_mcp'...
Starting Document Management MCP Server 'document_mcp'...
I then tested the server implementation via CLI using the direct MCP test:
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server/backend/mcp_document
cd /Users/glennmossy/dpg-ai-projects/claude_document_mcp_server/backend/mcp_document
Result: 1 passed in 0.42s – the direct MCP connectivity test passed.
How you can reproduce on your CLI
From your project root:
cd backend/mcp_document_server
uv run python document_mcp_server.py           # quick manual run (prints banner, then exits when stdin closes)
uv run pytest tests/test_mcp_direct.py -q     # CLI test of MCP server behavior
cd backend/mcp_document_serveruv run python document_mcp_server.py           # quick manual run (prints banner, then exits when stdin closes)uv run pytest tests/test_mcp_direct.py -q     # CLI test of MCP server behavior
For interactive tool testing, use MCP Inspector as documented in README.md (that’s still the best way to “talk” to the server).
