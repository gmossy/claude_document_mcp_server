FROM python:3.13-slim

# Install system dependencies for document parsing
RUN apt-get update && apt-get install -y \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install document parsing dependencies
RUN pip install --no-cache-dir \
    python-docx>=1.1.0 \
    pypdf>=4.0.0 \
    reportlab>=4.0.0 \
    python-magic>=0.4.27 \
    pillow>=10.0.0 \
    openpyxl>=3.1.0 \
    python-pptx>=0.6.23 \
    pydantic-settings>=2.0.0

# Copy application code maintaining backend structure
COPY backend ./backend

# Set Python path to project root
ENV PYTHONPATH=/app

# Set Python path correctly
ENV PYTHONPATH=/app

# Create data directory
RUN mkdir -p /data
VOLUME ["/data"]

# Environment variables
ENV DATABASE_URL=sqlite:////data/documents.db
ENV STORAGE_DIR=/data/document_storage

# Expose port
EXPOSE 8000

# Run the application (using backend.app.main since we maintain backend structure)
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

