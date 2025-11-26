FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

# Copy project structure
# Note: Build context should be from project root: docker build -f backend/mcp_document_server/Dockerfile .
COPY backend/mcp_document_server/pyproject.toml backend/mcp_document_server/uv.lock ./
COPY backend/mcp_document_server/document_mcp_server.py ./
COPY backend/mcp_document_server/document_parsers.py ./
COPY backend/mcp_document_server/mcp_tools.py ./
COPY backend/mcp_document_server/mcp_models.py ./
COPY backend/mcp_document_server/mcp_formatters.py ./
COPY backend/core ./backend/core

RUN uv sync --frozen --no-dev

VOLUME ["/data"]
ENV DATABASE_PATH=/data/documents.db
ENV DOCUMENTS_DIR=/data/document_storage

CMD ["uv", "run", "python", "document_mcp_server.py"]