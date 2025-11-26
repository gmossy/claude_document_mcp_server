# Testing Guide

## Quick Start

**Note**: When using Docker with nginx (`docker-compose up -d`), access the API via `http://localhost/api/v1` (nginx proxy). When running uvicorn directly, use `http://localhost:8000/api/v1`.

### 1. Install Test Dependencies

```bash
# Using pip
pip install requests

# Or using requirements file
pip install -r backend/requirements-test.txt
```

### 2. Start the API Server

#### Option A: Docker with Nginx (Recommended - Production Setup)

```bash
# Start all services (API, Frontend, Nginx)
docker-compose up -d

# Or start only API (still accessed via nginx if nginx is running)
docker-compose up -d api
```

When using Docker with nginx, the API is accessed via the nginx reverse proxy at `http://localhost/api/v1` (port 80). The API container runs on port 8000 internally but is not directly exposed.

#### Option B: Direct Uvicorn (Development Only)

```bash
cd backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

When running uvicorn directly, the API is available at `http://localhost:8000/api/v1` (direct access, no nginx).

### 3. Run the Test Script

```bash
# Test with nginx proxy URL (recommended when using Docker)
python tests/test_all_endpoints.py --base-url http://localhost/api/v1

# Test with direct API URL (when running uvicorn directly)
python tests/test_all_endpoints.py --base-url http://localhost:8000/api/v1

# Test with default URL (defaults to http://localhost:8000)
python tests/test_all_endpoints.py
```

**Note**: The default URL is `http://localhost:8000` for backward compatibility. If using Docker with nginx, specify `--base-url http://localhost/api/v1` explicitly.

## Test Coverage

The test script (`tests/test_all_endpoints.py`) tests all available endpoints:

1. **Health Check** - `/healthz` and `/api/v1/healthz`
2. **Document Upload** - `POST /api/v1/documents/upload`
3. **List Documents** - `GET /api/v1/documents/` (with various filters)
4. **Search Documents** - `GET /api/v1/search/` and `POST /api/v1/search/semantic`
5. **Get Document** - `GET /api/v1/documents/{id}`
6. **Analytics** - `GET /api/v1/analytics/overview`
7. **Delete Document** - `DELETE /api/v1/documents/{id}`

## Expected Output

The test script provides color-coded output:

- ✓ Green: Test passed
- ✗ Red: Test failed
- ℹ Yellow: Informational message

Example output:

```text
============================================================
FastAPI Endpoint Test Suite
Base URL: http://localhost/api/v1  # or http://localhost:8000/api/v1 for direct access
============================================================

Testing: Health Check
------------------------------------------------------------
✓ Root health check: {'status': 'ok'}
✓ API health check: {'status': 'ok'}

Testing: Document Upload
------------------------------------------------------------
✓ Document uploaded: doc_abc123def456
...

============================================================
Test Summary
============================================================

PASS - Health Check
PASS - Upload Document
PASS - List Documents
PASS - Search Documents
PASS - Get Document
PASS - Analytics
PASS - Delete Document

Total: 7/7 tests passed
```

## Manual Testing

### Using curl

See `docs/ENDPOINT_USAGE.md` for detailed curl examples for each endpoint.

### Using Python

**Note**: Use `http://localhost/api/v1` when accessing via nginx (Docker setup), or `http://localhost:8000/api/v1` when running uvicorn directly.

```python
import requests

# Base URL - choose based on your setup:
# BASE_URL = "http://localhost/api/v1"  # Nginx proxy (Docker)
BASE_URL = "http://localhost:8000/api/v1"  # Direct access (uvicorn)

# Upload a document
with open('test.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'title': 'Test Document',
        'tags': '["test"]',
        'status': 'draft'
    }
    response = requests.post(
        f'{BASE_URL}/documents/upload',
        files=files,
        data=data
    )
    print(response.json())

# List documents
response = requests.get(f'{BASE_URL}/documents/')
print(response.json())

# Search documents
response = requests.get(
    f'{BASE_URL}/search/',
    params={'q': 'test', 'limit': 10}
)
print(response.json())
```

### Using JavaScript/Fetch

**Note**: In production (Docker with nginx), use `http://localhost/api/v1`. For direct uvicorn access, use `http://localhost:8000/api/v1`.

```javascript
// Base URL - choose based on your setup:
const BASE_URL = "http://localhost/api/v1";  // Nginx proxy (Docker - recommended)
// const BASE_URL = "http://localhost:8000/api/v1";  // Direct access (uvicorn)

// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Test Document');
formData.append('tags', JSON.stringify(['test']));

const response = await fetch(`${BASE_URL}/documents/upload`, {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

## Troubleshooting

### Connection Refused

- Ensure the API server is running: `docker-compose ps api`
- Check the API health:
  - **If using Docker with nginx**: `curl http://localhost/api/v1/healthz`
  - **If running uvicorn directly**: `curl http://localhost:8000/api/v1/healthz`
- Verify firewall settings
- If using Docker, ensure nginx container is also running: `docker-compose ps nginx`

### Import Error (requests)

- Install requests: `pip install requests`
- Or use virtual environment: `source .venv/bin/activate && pip install requests`

### Test Failures

- Check API server logs: `docker-compose logs api`
- Verify database is initialized
- Check that test file can be created in current directory

### CORS Errors (Frontend)

- Verify CORS is configured in `backend/app/config.py`
- Check that frontend URL is in allowed origins
- Use browser dev tools to inspect CORS headers

## Continuous Integration

To run tests in CI/CD:

```yaml
# Example GitHub Actions
- name: Install dependencies
  run: pip install -r backend/requirements-test.txt

- name: Start API server
  run: docker-compose up -d api

- name: Wait for API
  run: sleep 10

- name: Run endpoint tests
  run: python tests/test_all_endpoints.py
```

## Performance Testing

For load testing, use tools like:

- `ab` (Apache Bench)
- `wrk`
- `locust` (Python-based)

Example with `ab`:

```bash
# Using nginx proxy (Docker setup - recommended)
ab -n 1000 -c 10 http://localhost/api/v1/documents/

# Or using direct API access (uvicorn)
ab -n 1000 -c 10 http://localhost:8000/api/v1/documents/
```

**Note**: Use the nginx URL (`http://localhost/api/v1`) when testing the production Docker setup, as it includes the reverse proxy overhead which is more representative of real-world performance.

## Security Testing

Test authentication and authorization when implemented:

- Test with invalid tokens
- Test with missing required fields
- Test file upload size limits
- Test SQL injection in search queries
