#!/usr/bin/env python3
"""Test all API endpoints."""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient
from backend.app.main import create_app
from backend.core.services import DocumentService
from backend.core.db import SQLiteAdapter
from tempfile import TemporaryDirectory

# Create test app
app = create_app()

# Create test database
with TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)
    db_path = tmp_path / "test.db"
    storage_dir = tmp_path / "storage"
    
    # Initialize database
    db_adapter = SQLiteAdapter(db_path)
    conn = db_adapter.connect()
    db_adapter.init_schema(conn)
    db_adapter.close(conn)
    
    # Create service
    service = DocumentService(db_adapter, storage_dir)
    
    # Override dependency
    from backend.app.api.deps import get_document_service
    app.dependency_overrides[get_document_service] = lambda: service
    
    client = TestClient(app)
    
    print("=" * 60)
    print("Testing API Endpoints")
    print("=" * 60)
    print()
    
    # Test 1: Health Check
    print("1. Testing GET /api/v1/healthz")
    response = client.get("/api/v1/healthz")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json()["status"] == "ok"
    print("   ✓ Health check passed")
    print()
    
    # Test 2: List Documents (empty)
    print("2. Testing GET /api/v1/documents/")
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    data = response.json()
    assert "documents" in data
    assert "total" in data
    print(f"   ✓ List documents passed (found {data['total']} documents)")
    print()
    
    # Test 3: Upload Document
    print("3. Testing POST /api/v1/documents/upload")
    test_file_content = b"This is a test document file content."
    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("test.txt", test_file_content, "text/plain")},
        data={
            "title": "Test Document",
            "tags": '["test", "upload"]',
            "status": "draft"
        }
    )
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    upload_data = response.json()
    assert upload_data["success"] is True
    assert "document_id" in upload_data
    doc_id = upload_data["document_id"]
    print(f"   ✓ Upload passed (document_id: {doc_id})")
    print()
    
    # Test 4: List Documents (with data)
    print("4. Testing GET /api/v1/documents/ (after upload)")
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    print(f"   ✓ List documents passed (found {data['total']} document(s))")
    print()
    
    # Test 5: Search Documents by filename
    print("5. Testing GET /api/v1/search/?q=test")
    response = client.get("/api/v1/search/?q=test")
    assert response.status_code == 200
    search_data = response.json()
    assert "results" in search_data
    print(f"   ✓ Search by filename passed (found {len(search_data['results'])} result(s))")
    print()
    
    # Test 5b: Delete Document
    print("5b. Testing DELETE /api/v1/documents/{doc_id}")
    response = client.delete(f"/api/v1/documents/{doc_id}")
    assert response.status_code == 200
    delete_data = response.json()
    assert delete_data["success"] is True
    assert delete_data["action"] == "archived"
    print(f"   ✓ Delete document passed (document archived)")
    print()
    
    # Test 6: Analytics Overview
    print("6. Testing GET /api/v1/analytics/overview")
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 200
    analytics_data = response.json()
    assert "totals" in analytics_data
    print(f"   ✓ Analytics passed")
    print()
    
    # Test 7: Create Document (placeholder)
    print("7. Testing POST /api/v1/documents/")
    response = client.post("/api/v1/documents/")
    assert response.status_code == 200
    create_data = response.json()
    assert "document_id" in create_data
    print(f"   ✓ Create document passed (placeholder)")
    print()
    
    print("=" * 60)
    print("All endpoint tests passed! ✓")
    print("=" * 60)

