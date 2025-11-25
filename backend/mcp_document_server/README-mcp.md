## Mission Library – MCP Document Server

### Local dev

cd backend/mcp_document_server
uv sync
uv run python document_mcp_server.py### Docker

cd backend/mcp_document_server
docker build -t mission-mcp-document-server .
docker run --rm -it mission-mcp-document-server
