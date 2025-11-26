FROM python:3.13-slim

WORKDIR /app

# Install system dependencies in one layer (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install all Python dependencies in a single layer with cache mount
# This allows pip to cache packages between builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    python-docx>=1.1.0 \
    pypdf>=4.0.0 \
    reportlab>=4.0.0 \
    python-magic>=0.4.27 \
    pillow>=10.0.0 \
    openpyxl>=3.1.0 \
    python-pptx>=0.6.23 \
    pydantic-settings>=2.0.0 \
    pytest>=7.0.0 \
    pytest-asyncio>=0.23.0 \
    httpx>=0.25.0 \
    requests>=2.31.0

# Copy application code maintaining backend structure
COPY backend ./backend

# Set environment variables (consolidated)
ENV PYTHONPATH=/app \
    DATABASE_URL=sqlite:////data/documents.db \
    STORAGE_DIR=/data/document_storage

# Create data directory
RUN mkdir -p /data
VOLUME ["/data"]

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
