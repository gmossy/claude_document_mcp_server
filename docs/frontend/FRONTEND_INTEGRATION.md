# Frontend-Backend Integration Guide

## Overview

This guide explains how to integrate the React frontend with the FastAPI backend. The frontend is in a separate git submodule, so integration changes should be made in that repository.

## FastAPI Endpoints Available

### Document Management

1. **List Documents**
   ```http
   GET /api/v1/documents/?status=draft&tags=tag1,tag2&limit=50&offset=0&order_by=created_at&order_desc=true
   ```
   Response: `{ "documents": [...], "total": 100, "limit": 50, "offset": 0 }`

2. **Upload Document**
   ```http
   POST /api/v1/documents/upload
   Content-Type: multipart/form-data
   
   file: <binary>
   title: "Optional title"
   tags: '["tag1", "tag2"]'
   status: "draft"
   metadata: '{"category": "Training", "source": "US Army"}'
   ```
   Response: `{ "success": true, "document_id": "doc_...", "title": "...", ... }`

3. **Delete/Archive Document**
   ```http
   DELETE /api/v1/documents/{document_id}?permanent=false
   ```
   Response: `{ "success": true, "action": "archived", ... }`

### Search

4. **Search by Filename/Title**
   ```http
   GET /api/v1/search/?q=search+term&limit=50
   ```
   Response: `{ "results": [...], ... }`

5. **Semantic Search** (POST endpoint)
   ```http
   POST /api/v1/search/semantic
   Content-Type: application/json
   
   { "query": "search term", "limit": 20 }
   ```
   Response: `{ "results": [...], ... }`

### Analytics

6. **Get Analytics Overview**
   ```http
   GET /api/v1/analytics/overview
   ```
   Response: `{ "totals": {...} }`

### Health

7. **Health Check**
   ```http
   GET /api/v1/healthz
   ```
   Response: `{ "status": "ok" }`

## Frontend Integration Steps

### 1. Create API Service File

Create `frontend/src/services/api.js` with the following content:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function handleResponse(response) {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }
  return response.json();
}

// Upload document
export async function uploadDocument(file, metadata = {}) {
  const formData = new FormData();
  formData.append('file', file);
  if (metadata.title) formData.append('title', metadata.title);
  formData.append('tags', JSON.stringify(metadata.tags || []));
  formData.append('status', metadata.status || 'draft');
  formData.append('metadata', JSON.stringify(metadata.metadata || {}));

  const response = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: 'POST',
    body: formData,
  });
  return handleResponse(response);
}

// List documents
export async function getDocuments(params = {}) {
  const queryParams = new URLSearchParams();
  if (params.status) queryParams.append('status', params.status);
  if (params.tags?.length) queryParams.append('tags', params.tags.join(','));
  if (params.limit) queryParams.append('limit', params.limit);
  if (params.offset) queryParams.append('offset', params.offset);
  if (params.order_by) queryParams.append('order_by', params.order_by);
  if (params.order_desc !== undefined) {
    queryParams.append('order_desc', params.order_desc);
  }

  const url = `${API_BASE_URL}/documents/${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
  return handleResponse(await fetch(url));
}

// Search documents
export async function searchDocuments(query, limit = 50) {
  const queryParams = new URLSearchParams();
  queryParams.append('q', query);
  queryParams.append('limit', limit.toString());
  return handleResponse(await fetch(`${API_BASE_URL}/search/?${queryParams.toString()}`));
}

// Delete document
export async function deleteDocument(documentId, permanent = false) {
  return handleResponse(await fetch(
    `${API_BASE_URL}/documents/${documentId}?permanent=${permanent}`,
    { method: 'DELETE' }
  ));
}

// Get analytics
export async function getAnalytics() {
  return handleResponse(await fetch(`${API_BASE_URL}/analytics/overview`));
}
```

### 2. Update DocumentLibrary Component

Replace the mock data and handlers with API calls:

```javascript
import { useState, useEffect } from 'react';
import * as api from '../services/api';

// In component:
const [documents, setDocuments] = useState([]);
const [loading, setLoading] = useState(true);

useEffect(() => {
  loadDocuments();
}, []);

const loadDocuments = async () => {
  try {
    setLoading(true);
    const response = await api.getDocuments({ limit: 100 });
    setDocuments(response.documents || []);
  } catch (err) {
    console.error('Error loading documents:', err);
  } finally {
    setLoading(false);
  }
};

const handleUpload = async () => {
  if (!uploadFile) return;
  
  try {
    const tags = uploadTags.split(',').map(t => t.trim()).filter(t => t);
    const result = await api.uploadDocument(uploadFile, {
      title: uploadTitle || uploadFile.name,
      tags: tags,
      status: 'draft',
      metadata: {
        category: uploadCategory,
        source: uploadSource,
        description: uploadDescription,
      },
    });
    
    alert(`Uploaded: ${result.document_id}`);
    setShowUploadModal(false);
    loadDocuments(); // Refresh list
  } catch (err) {
    alert(`Upload failed: ${err.message}`);
  }
};
```

### 3. Environment Configuration

Create `frontend/.env` (or `.env.local`):

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

For production:
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
```

### 4. CORS Configuration

If you encounter CORS errors, the backend already allows all origins by default. If you need to restrict it, update `backend/app/config.py`:

```python
allow_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
```

## Data Mapping

### Backend Response Format
```json
{
  "id": "doc_abc123",
  "title": "Document Title",
  "tags": ["tag1", "tag2"],
  "status": "draft",
  "created_at": "2024-11-26T03:38:54Z",
  "updated_at": "2024-11-26T03:38:54Z",
  "size": 1024,
  "metadata": "{\"category\": \"Training\", \"source\": \"US Army\"}"
}
```

### Frontend Display Format
```javascript
{
  id: "doc_abc123",
  name: "Document Title",        // from title
  category: "Training",          // from metadata.category
  source: "US Army",             // from metadata.source
  tags: ["tag1", "tag2"],
  status: "draft",
  uploadDate: "2024-11-26",     // from created_at
  size: "1.0 KB"                 // formatted from size
}
```

## Testing the Integration

1. **Start Backend:**
   ```bash
   docker-compose up -d api
   # Or: uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
   ```

2. **Start Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Test Upload:**
   - Open http://localhost:5173
   - Click "Upload Document"
   - Select a file and fill in metadata
   - Click "Upload Document"
   - Verify document appears in list

4. **Test Search:**
   - Type in search box
   - Verify results update

## Troubleshooting

### CORS Errors
- Verify backend is running: `curl http://localhost:8000/healthz`
- Check browser console for CORS errors
- Verify `VITE_API_BASE_URL` in `.env` file

### Upload Failures
- Check file size (backend limit: 10MB)
- Verify file format is supported
- Check backend logs: `docker-compose logs api`

### Search Not Working
- Verify search endpoint: `curl "http://localhost:8000/api/v1/search/?q=test"`
- Check network tab in browser dev tools

## Next Steps

1. Add authentication (JWT tokens)
2. Implement document preview
3. Add download functionality
4. Implement pagination
5. Add real-time updates (WebSocket or polling)

