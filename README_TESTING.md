# Testing Guide

## Quick Start

### 1. Install Test Dependencies

```bash
# Using pip
pip install requests

# Or using requirements file
pip install -r requirements-test.txt
```

### 2. Start the API Server

```bash
# Using Docker (recommended)
docker-compose up -d api

# Or directly with uvicorn
cd backend
source .venv/bin/activate
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### 3. Run the Test Script

```bash
# Test with default URL (http://localhost:8000)
python test_all_endpoints.py

# Test with custom URL
python test_all_endpoints.py --base-url http://localhost:8000
```

## Test Coverage

The test script (`test_all_endpoints.py`) tests all available endpoints:

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
```
============================================================
FastAPI Endpoint Test Suite
Base URL: http://localhost:8000
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

```python
import requests

# Upload a document
with open('test.pdf', 'rb') as f:
    files = {'file': f}
    data = {
        'title': 'Test Document',
        'tags': '["test"]',
        'status': 'draft'
    }
    response = requests.post(
        'http://localhost:8000/api/v1/documents/upload',
        files=files,
        data=data
    )
    print(response.json())

# List documents
response = requests.get('http://localhost:8000/api/v1/documents/')
print(response.json())

# Search documents
response = requests.get(
    'http://localhost:8000/api/v1/search/',
    params={'q': 'test', 'limit': 10}
)
print(response.json())
```

### Using JavaScript/Fetch

```javascript
// Upload document
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'Test Document');
formData.append('tags', JSON.stringify(['test']));

const response = await fetch('http://localhost:8000/api/v1/documents/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log(result);
```

## Troubleshooting

### Connection Refused
- Ensure the API server is running: `docker-compose ps api`
- Check the port: `curl http://localhost:8000/healthz`
- Verify firewall settings

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
  run: pip install -r requirements-test.txt

- name: Start API server
  run: docker-compose up -d api

- name: Wait for API
  run: sleep 10

- name: Run endpoint tests
  run: python test_all_endpoints.py
```

## Performance Testing

For load testing, use tools like:
- `ab` (Apache Bench)
- `wrk`
- `locust` (Python-based)

Example with `ab`:
```bash
ab -n 1000 -c 10 http://localhost:8000/api/v1/documents/
```

## Security Testing

Test authentication and authorization when implemented:
- Test with invalid tokens
- Test with missing required fields
- Test file upload size limits
- Test SQL injection in search queries

