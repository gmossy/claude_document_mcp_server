# FastAPI Endpoint Usage Documentation

Complete documentation for all available endpoints in the Document Management API.

## Base URL

All endpoints are prefixed with `/api/v1`:
```
http://localhost:8000/api/v1
```

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

---

## Health Check Endpoints

### Root Health Check
```http
GET /healthz
```

**Description:** Check if the API service is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/healthz
```

### API Health Check
```http
GET /api/v1/healthz
```

**Description:** Check if the API v1 service is running.

**Response:**
```json
{
  "status": "ok"
}
```

**Example:**
```bash
curl http://localhost:8000/api/v1/healthz
```

---

## Document Management Endpoints

### List Documents
```http
GET /api/v1/documents/
```

**Description:** Retrieve a paginated list of documents with optional filtering.

**Query Parameters:**
- `status` (optional): Filter by status (`draft`, `published`, `archived`)
- `tags` (optional): Comma-separated list of tags (documents must have ALL tags)
- `limit` (optional, default: 50): Maximum number of documents (1-100)
- `offset` (optional, default: 0): Number of documents to skip
- `order_by` (optional, default: `created_at`): Field to sort by (`created_at`, `updated_at`, `title`, `status`)
- `order_desc` (optional, default: `true`): Sort descending (`true`) or ascending (`false`)

**Response:**
```json
{
  "documents": [
    {
      "id": "doc_abc123def456",
      "title": "Document Title",
      "status": "draft",
      "created_at": "2024-11-26T03:38:54.877484+00:00",
      "updated_at": "2024-11-26T03:38:54.877484+00:00",
      "size": 1024,
      "tags": ["tag1", "tag2"]
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

**Examples:**
```bash
# List all documents
curl "http://localhost:8000/api/v1/documents/"

# Filter by status
curl "http://localhost:8000/api/v1/documents/?status=draft"

# Filter by tags
curl "http://localhost:8000/api/v1/documents/?tags=test,api"

# Pagination
curl "http://localhost:8000/api/v1/documents/?limit=10&offset=20"

# Sort by title ascending
curl "http://localhost:8000/api/v1/documents/?order_by=title&order_desc=false"
```

---

### Upload Document
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data
```

**Description:** Upload a document file with metadata.

**Form Fields:**
- `file` (required): The document file (binary)
- `title` (optional): Document title (defaults to filename if not provided)
- `tags` (optional): JSON array of tags, e.g., `["tag1", "tag2"]` (default: `[]`)
- `status` (optional): Document status (`draft`, `published`, `archived`) (default: `draft`)
- `metadata` (optional): JSON object with custom metadata (default: `{}`)

**Supported File Types:**
- Word: `.docx`, `.doc`
- PDF: `.pdf`
- Excel: `.xlsx`, `.xls`
- PowerPoint: `.pptx`, `.ppt`
- Text: `.txt`, `.md`
- Code files: `.py`, `.js`, `.cpp`, etc.
- OpenUSD: `.usd`, `.usda`, `.usdc`
- Any other binary format

**Response:**
```json
{
  "success": true,
  "document_id": "doc_abc123def456",
  "title": "Document Title",
  "status": "draft",
  "created_at": "2024-11-26T03:38:54.877484+00:00",
  "size": 1024,
  "tags": ["tag1", "tag2"],
  "version": 1,
  "message": "Document 'Document Title' created successfully with ID doc_abc123def456",
  "binary": {
    "filename": "document.pdf",
    "mime_type": "application/pdf",
    "format": "pdf",
    "size_bytes": 1024
  }
}
```

**Examples:**
```bash
# Basic upload
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@document.pdf"

# Upload with metadata
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@report.docx" \
  -F "title=Q4 Report" \
  -F 'tags=["finance", "2024"]' \
  -F "status=draft" \
  -F 'metadata={"category": "Finance", "source": "Accounting"}'

# Using JavaScript/FormData
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'My Document');
formData.append('tags', JSON.stringify(['tag1', 'tag2']));
formData.append('status', 'draft');
formData.append('metadata', JSON.stringify({category: 'Training'}));

fetch('http://localhost:8000/api/v1/documents/upload', {
  method: 'POST',
  body: formData
});
```

---

### Delete/Archive Document
```http
DELETE /api/v1/documents/{document_id}
```

**Description:** Delete or archive a document.

**Query Parameters:**
- `permanent` (optional, default: `false`): If `true`, permanently deletes; if `false`, archives (soft delete)

**Response (Archive):**
```json
{
  "success": true,
  "document_id": "doc_abc123def456",
  "title": "Document Title",
  "action": "archived",
  "message": "Document 'Document Title' has been archived."
}
```

**Response (Permanent Delete):**
```json
{
  "success": true,
  "document_id": "doc_abc123def456",
  "title": "Document Title",
  "action": "deleted",
  "message": "Document 'Document Title' has been permanently deleted."
}
```

**Examples:**
```bash
# Archive document (soft delete)
curl -X DELETE "http://localhost:8000/api/v1/documents/doc_abc123def456?permanent=false"

# Permanently delete document
curl -X DELETE "http://localhost:8000/api/v1/documents/doc_abc123def456?permanent=true"
```

---

## Search Endpoints

### Search by Filename/Title
```http
GET /api/v1/search/
```

**Description:** Search for documents by filename, title, or metadata.

**Query Parameters:**
- `q` (required): Search query (filename, title, or partial match)
- `limit` (optional, default: 50): Maximum number of results (1-100)

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc_abc123def456",
      "title": "report.pdf",
      "status": "published",
      "tags": ["test"],
      "created_at": "2024-11-26T03:38:54.877484+00:00",
      "updated_at": "2024-11-26T03:38:54.877484+00:00",
      "size": 1024
    }
  ]
}
```

**Examples:**
```bash
# Search for documents
curl "http://localhost:8000/api/v1/search/?q=report"

# Search with limit
curl "http://localhost:8000/api/v1/search/?q=test&limit=10"
```

---

### Semantic Search
```http
POST /api/v1/search/semantic
Content-Type: application/json
```

**Description:** Semantic/full-text search for documents (if implemented).

**Request Body:**
```json
{
  "query": "search term",
  "limit": 20
}
```

**Response:**
```json
{
  "results": [
    {
      "document_id": "doc_abc123def456",
      "title": "Document Title",
      "status": "published",
      "tags": ["tag1"],
      "created_at": "2024-11-26T03:38:54.877484+00:00",
      "updated_at": "2024-11-26T03:38:54.877484+00:00",
      "size": 1024,
      "relevance_score": 0.95
    }
  ]
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/v1/search/semantic" \
  -H "Content-Type: application/json" \
  -d '{"query": "test document", "limit": 10}'
```

---

## Analytics Endpoints

### Get Analytics Overview
```http
GET /api/v1/analytics/overview
```

**Description:** Get summary statistics about documents in the system.

**Response:**
```json
{
  "totals": {
    "total_documents": 150,
    "total_size_bytes": 52428800,
    "documents_by_status": {
      "draft": 45,
      "published": 90,
      "archived": 15
    },
    "documents_by_format": {
      "pdf": 60,
      "docx": 50,
      "xlsx": 25,
      "pptx": 15
    },
    "most_used_tags": [
      {"tag": "ai-testing", "count": 30},
      {"tag": "meetings", "count": 25}
    ]
  }
}
```

**Example:**
```bash
curl "http://localhost:8000/api/v1/analytics/overview"
```

---

## Error Responses

All endpoints may return error responses in the following format:

**400 Bad Request:**
```json
{
  "detail": "Invalid request parameters"
}
```

**404 Not Found:**
```json
{
  "detail": "Document with ID 'doc_abc123' not found."
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Failed to process request"
}
```

---

## Frontend Integration Examples

### React/JavaScript Upload Example
```javascript
async function uploadDocument(file, metadata) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('title', metadata.title || file.name);
  formData.append('tags', JSON.stringify(metadata.tags || []));
  formData.append('status', metadata.status || 'draft');
  formData.append('metadata', JSON.stringify(metadata.metadata || {}));

  const response = await fetch('http://localhost:8000/api/v1/documents/upload', {
    method: 'POST',
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Upload failed');
  }

  return response.json();
}
```

### React/JavaScript List Documents Example
```javascript
async function listDocuments(filters = {}) {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.tags?.length) params.append('tags', filters.tags.join(','));
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.offset) params.append('offset', filters.offset);

  const response = await fetch(
    `http://localhost:8000/api/v1/documents/?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error('Failed to fetch documents');
  }

  return response.json();
}
```

### React/JavaScript Search Example
```javascript
async function searchDocuments(query, limit = 50) {
  const params = new URLSearchParams();
  params.append('q', query);
  params.append('limit', limit.toString());

  const response = await fetch(
    `http://localhost:8000/api/v1/search/?${params.toString()}`
  );

  if (!response.ok) {
    throw new Error('Search failed');
  }

  return response.json();
}
```

---

## Testing

Use the provided test script to test all endpoints:

```bash
# Test with default URL
python test_all_endpoints.py

# Test with custom URL
python test_all_endpoints.py --base-url http://localhost:8000
```

The test script will:
1. Test health check endpoints
2. Upload a test document
3. List documents with various filters
4. Search for documents
5. Get analytics
6. Delete the test document

---

## Rate Limiting

Currently, no rate limiting is implemented. All endpoints are rate-limited only by server resources.

---

## CORS

CORS is configured to allow requests from:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (React dev server)
- All origins (configurable in `backend/app/config.py`)

---

## Notes

- All timestamps are in ISO 8601 format with UTC timezone
- File sizes are in bytes
- Document IDs follow the pattern: `doc_<hex_string>`
- Tags are case-sensitive
- Metadata is stored as JSON strings in the database

