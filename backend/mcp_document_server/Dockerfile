FROM python:3.13-slim

RUN pip install --no-cache-dir uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY document_mcp_server.py document_parsers.py ./
COPY docs ./docs

RUN uv sync --frozen --no-dev

VOLUME ["/data"]
ENV DATABASE_PATH=/data/documents.db
ENV DOCUMENTS_DIR=/data/document_storage

CMD ["uv", "run", "python", "document_mcp_server.py"]