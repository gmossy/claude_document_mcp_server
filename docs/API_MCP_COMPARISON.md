# FastAPI Endpoints vs MCP Tools Comparison

## FastAPI Endpoints

### Documents
1. ✅ `GET /api/v1/documents/` - **list_documents** (pagination, filtering)
2. ✅ `GET /api/v1/documents/{document_id}` - **get_document** (with optional content/versions)
3. ⚠️ `POST /api/v1/documents/` - **create_document** (placeholder, not implemented)
4. ✅ `POST /api/v1/documents/upload` - **upload_document** (file upload - **used by frontend**)
5. ✅ `DELETE /api/v1/documents/{document_id}` - **delete_document** (archive/permanent)
6. ✅ `POST /api/v1/documents/create-file` - **create_document_file** (Word/PDF/Excel generation)

### Search
7. ✅ `GET /api/v1/search/` - **search_documents** (filename/title search)
8. ✅ `POST /api/v1/search/semantic` - **semantic_search** (full-text search)

### Analytics
9. ✅ `GET /api/v1/analytics/overview` - **analytics_overview** (system statistics)

### Auth
10. ✅ `POST /api/v1/auth/login` - **login** (authentication)
11. ✅ `GET /api/v1/auth/me` - **get_current_user** (user info)

### Health
12. ✅ `GET /api/v1/healthz` - **healthz** (health check)

## MCP Tools

1. ❌ `document_create` - Create document (text content)
   - **FastAPI Equivalent**: **NONE** - This is MCP-only for AI/LLM use
   - **Note**: Frontend uses `POST /api/v1/documents/upload` for file uploads (different purpose)
   - **Use Case**: AI assistants creating documents from text via MCP protocol

2. ✅ `document_get` - Get document by ID
   - **FastAPI Equivalent**: `GET /api/v1/documents/{document_id}` ✅

3. ❌ `document_update` - Update document content
   - **FastAPI Equivalent**: **MISSING** - No update endpoint

4. ✅ `document_delete` - Delete/archive document
   - **FastAPI Equivalent**: `DELETE /api/v1/documents/{document_id}` ✅

5. ✅ `document_search` - Full-text search
   - **FastAPI Equivalent**: `GET /api/v1/search/` and `POST /api/v1/search/semantic` ✅

6. ❌ `document_list_tags` - List all tags with counts
   - **FastAPI Equivalent**: **MISSING**

7. ❌ `document_get_version` - Get specific version
   - **FastAPI Equivalent**: **MISSING** (can get versions via get_document with include_versions=true, but not specific version)

8. ❌ `document_compare_versions` - Compare two versions
   - **FastAPI Equivalent**: **MISSING**

9. ❌ `document_analyze` - Content analysis (word count, keywords)
   - **FastAPI Equivalent**: **MISSING**

10. ❌ `document_export` - Export to Markdown/HTML/JSON/TXT
    - **FastAPI Equivalent**: **MISSING** (has create-file for Word/PDF/Excel, but not text exports)

11. ✅ `document_export_file` - Export to file format
    - **FastAPI Equivalent**: `POST /api/v1/documents/create-file` ✅

12. ❌ `document_bulk_tag` - Bulk tag operations
    - **FastAPI Equivalent**: **MISSING**

13. ✅ `document_statistics` - System statistics
    - **FastAPI Equivalent**: `GET /api/v1/analytics/overview` ✅

## Summary

### ✅ FastAPI Endpoints WITH MCP Tools
- GET /api/v1/documents/{document_id} → document_get
- DELETE /api/v1/documents/{document_id} → document_delete
- GET /api/v1/search/ → document_search
- POST /api/v1/search/semantic → document_search
- POST /api/v1/documents/create-file → document_export_file
- GET /api/v1/analytics/overview → document_statistics

### ❌ MCP Tools WITHOUT FastAPI Endpoints
- `document_update` - Update document content/metadata
- `document_list_tags` - List all tags with usage counts
- `document_get_version` - Get specific version by number
- `document_compare_versions` - Compare two versions
- `document_analyze` - Content analysis (word count, keywords, reading time)
- `document_export` - Export to Markdown/HTML/JSON/TXT formats
- `document_bulk_tag` - Bulk tag add/remove operations

### ⚠️ Partial Coverage / Different Use Cases
- `document_create` - **MCP only**: Creates documents from text content (for AI/LLM use via MCP protocol). **Not used by frontend.**
- `POST /api/v1/documents/upload` - **FastAPI only**: Uploads binary files (used by frontend for file uploads). **Not available as MCP tool.**
- `document_get` - FastAPI can include versions, but MCP has separate `document_get_version` for specific versions

## Recommendations

To achieve full parity, consider adding these FastAPI endpoints:

1. **PATCH /api/v1/documents/{document_id}** - Update document (content, tags, metadata)
2. **GET /api/v1/documents/{document_id}/versions/{version_number}** - Get specific version
3. **GET /api/v1/documents/{document_id}/versions/{v1}/compare/{v2}** - Compare versions
4. **GET /api/v1/documents/{document_id}/analyze** - Content analysis
5. **GET /api/v1/tags/** - List all tags with counts
6. **POST /api/v1/documents/bulk-tag** - Bulk tag operations
7. **GET /api/v1/documents/{document_id}/export** - Export to text formats (Markdown/HTML/JSON/TXT)

