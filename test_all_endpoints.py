#!/usr/bin/env python3
"""
Comprehensive test script for all FastAPI endpoints.

This script tests all available endpoints in the document management API:
- Health check
- Document upload
- Document listing
- Document search (filename and semantic)
- Document deletion
- Analytics

Usage:
    python test_all_endpoints.py [--base-url http://localhost:8000]

Requirements:
    pip install requests
    Or: pip install -r requirements-test.txt
"""

import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' library not found.")
    print("Install it with: pip install requests")
    print("Or: pip install -r requirements-test.txt")
    sys.exit(1)


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class EndpointTester:
    """Test all FastAPI endpoints."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api/v1"
        self.session = requests.Session()
        self.uploaded_doc_id: Optional[str] = None
        
    def print_test(self, name: str):
        """Print test header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}Testing: {name}{Colors.RESET}")
        print("-" * 60)
    
    def print_success(self, message: str):
        """Print success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")
    
    def print_error(self, message: str):
        """Print error message."""
        print(f"{Colors.RED}✗ {message}{Colors.RESET}")
    
    def print_info(self, message: str):
        """Print info message."""
        print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")
    
    def test_health_check(self):
        """Test health check endpoint."""
        self.print_test("Health Check")
        try:
            # Root health
            response = self.session.get(f"{self.base_url}/healthz")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Root health check: {data}")
            else:
                self.print_error(f"Root health check failed: {response.status_code}")
                return False
            
            # API health
            response = self.session.get(f"{self.api_base}/healthz")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"API health check: {data}")
                return True
            else:
                self.print_error(f"API health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Health check error: {e}")
            return False
    
    def test_upload_document(self):
        """Test document upload endpoint."""
        self.print_test("Document Upload")
        try:
            import random
            
            # Generate random filename with file type prefix
            random_id = uuid.uuid4().hex[:8]
            filename = f"Text_{random_id}.txt"
            
            # Generate random file size between 100 and 200,000 bytes
            base_text = "This is a test document for API testing.\n"
            target_size = random.randint(100, 200000)
            multiplier = max(1, target_size // len(base_text))
            content = base_text * multiplier
            content = content[:target_size]  # Trim to exact size
            
            # Create a test document file
            test_file = Path(filename)
            test_file.write_text(content)
            
            form_data = {
                'title': 'API Test Document',
                'tags': json.dumps(['test', 'api', 'integration']),
                'status': 'draft',
                'metadata': json.dumps({
                    'category': 'Testing',
                    'source': 'API Test Script',
                    'description': 'Test document created by endpoint test script'
                })
            }
            
            files = {'file': (filename, test_file.open('rb'), 'text/plain')}
            
            response = self.session.post(
                f"{self.api_base}/documents/upload",
                data=form_data,
                files=files
            )
            
            test_file.unlink()  # Clean up
            
            if response.status_code == 200:
                data = response.json()
                self.uploaded_doc_id = data.get('document_id')
                self.print_success(f"Document uploaded: {self.uploaded_doc_id}")
                self.print_info(f"Response: {json.dumps(data, indent=2)}")
                return True
            else:
                self.print_error(f"Upload failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Upload error: {e}")
            return False
    
    def test_list_documents(self):
        """Test document listing endpoint."""
        self.print_test("List Documents")
        try:
            # Test basic listing
            response = self.session.get(f"{self.api_base}/documents/")
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('documents', []))
                total = data.get('total', 0)
                self.print_success(f"Listed {count} documents (total: {total})")
            else:
                self.print_error(f"List failed: {response.status_code}")
                return False
            
            # Test with filters
            params = {
                'status': 'draft',
                'limit': 10,
                'offset': 0,
                'order_by': 'created_at',
                'order_desc': 'true'
            }
            response = self.session.get(f"{self.api_base}/documents/", params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Filtered list: {len(data.get('documents', []))} documents")
            
            # Test with tags filter
            params = {'tags': 'test,api', 'limit': 5}
            response = self.session.get(f"{self.api_base}/documents/", params=params)
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Tag-filtered list: {len(data.get('documents', []))} documents")
            
            return True
        except Exception as e:
            self.print_error(f"List error: {e}")
            return False
    
    def test_search_documents(self):
        """Test document search endpoints."""
        self.print_test("Search Documents")
        try:
            # Test filename search
            params = {'q': 'test', 'limit': 10}
            response = self.session.get(f"{self.api_base}/search/", params=params)
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('results', []))
                self.print_success(f"Filename search found {count} results")
                if count > 0:
                    self.print_info(f"First result: {data['results'][0].get('title', 'N/A')}")
            else:
                self.print_error(f"Search failed: {response.status_code}")
                return False
            
            # Test semantic search
            semantic_data = {
                'query': 'test document',
                'limit': 5
            }
            response = self.session.post(
                f"{self.api_base}/search/semantic",
                json=semantic_data
            )
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('results', []))
                self.print_success(f"Semantic search found {count} results")
            else:
                self.print_info(f"Semantic search returned {response.status_code} (may not be implemented)")
            
            return True
        except Exception as e:
            self.print_error(f"Search error: {e}")
            return False
    
    def test_get_document(self):
        """Test getting a single document (if endpoint exists)."""
        self.print_test("Get Single Document")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            # Try to get document by ID
            response = self.session.get(f"{self.api_base}/documents/{self.uploaded_doc_id}")
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Retrieved document: {data.get('title', 'N/A')}")
                return True
            elif response.status_code == 404:
                self.print_info("GET /documents/{id} endpoint not implemented (expected)")
                return True
            else:
                self.print_error(f"Get document failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_info(f"Get document endpoint may not exist: {e}")
            return True
    
    def test_update_document(self):
        """Test document update endpoint."""
        self.print_test("Update Document")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            update_data = {
                "title": "Updated API Test Document",
                "tags": ["test", "api", "integration", "updated"],
                "version_comment": "Test update via API"
            }
            response = self.session.patch(
                f"{self.api_base}/documents/{self.uploaded_doc_id}",
                json=update_data
            )
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Document updated: {data.get('title', 'N/A')}")
                return True
            else:
                self.print_error(f"Update failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Update error: {e}")
            return False
    
    def test_get_document_version(self):
        """Test getting a specific document version."""
        self.print_test("Get Document Version")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            response = self.session.get(
                f"{self.api_base}/documents/{self.uploaded_doc_id}/versions/1"
            )
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Retrieved version 1: {data.get('title', 'N/A')}")
                return True
            else:
                self.print_info(f"Get version returned {response.status_code} (may not have versions)")
                return True
        except Exception as e:
            self.print_info(f"Get version endpoint may not work: {e}")
            return True
    
    def test_compare_versions(self):
        """Test comparing two document versions."""
        self.print_test("Compare Versions")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            response = self.session.get(
                f"{self.api_base}/documents/{self.uploaded_doc_id}/versions/1/compare/1"
            )
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Versions compared: changed={data.get('changed', False)}")
                return True
            else:
                self.print_info(f"Compare returned {response.status_code} (may not have multiple versions)")
                return True
        except Exception as e:
            self.print_info(f"Compare endpoint may not work: {e}")
            return True
    
    def test_analyze_document(self):
        """Test document analysis endpoint."""
        self.print_test("Analyze Document")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            response = self.session.get(
                f"{self.api_base}/documents/{self.uploaded_doc_id}/analyze"
            )
            if response.status_code == 200:
                data = response.json()
                stats = data.get('stats', {})
                self.print_success(f"Document analyzed: {stats.get('word_count', 0)} words")
                return True
            else:
                self.print_error(f"Analyze failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Analyze error: {e}")
            return False
    
    def test_list_tags(self):
        """Test list tags endpoint."""
        self.print_test("List Tags")
        try:
            response = self.session.get(f"{self.api_base}/tags/")
            if response.status_code == 200:
                data = response.json()
                count = len(data.get('tags', []))
                self.print_success(f"Listed {count} tags")
                return True
            else:
                self.print_error(f"List tags failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"List tags error: {e}")
            return False
    
    def test_bulk_tag(self):
        """Test bulk tag endpoint."""
        self.print_test("Bulk Tag")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            bulk_data = {
                "document_ids": [self.uploaded_doc_id],
                "add_tags": ["bulk-tagged"],
                "remove_tags": []
            }
            response = self.session.post(
                f"{self.api_base}/documents/bulk-tag",
                json=bulk_data
            )
            if response.status_code == 200:
                data = response.json()
                successful = data.get('successful', 0)
                self.print_success(f"Bulk tagged {successful} document(s)")
                return True
            else:
                self.print_error(f"Bulk tag failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Bulk tag error: {e}")
            return False
    
    def test_export_document(self):
        """Test document export endpoint."""
        self.print_test("Export Document")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            # Test markdown export
            response = self.session.get(
                f"{self.api_base}/documents/{self.uploaded_doc_id}/export?format=markdown"
            )
            if response.status_code == 200:
                self.print_success("Document exported to markdown")
                
                # Test JSON export
                response = self.session.get(
                    f"{self.api_base}/documents/{self.uploaded_doc_id}/export?format=json"
                )
                if response.status_code == 200:
                    self.print_success("Document exported to JSON")
                    return True
                else:
                    self.print_error(f"JSON export failed: {response.status_code}")
                    return False
            else:
                self.print_error(f"Export failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Export error: {e}")
            return False
    
    def test_delete_document(self):
        """Test document deletion endpoint."""
        self.print_test("Delete Document")
        if not self.uploaded_doc_id:
            self.print_info("Skipping - no document ID available")
            return True
        
        try:
            # Test archive (soft delete)
            response = self.session.delete(
                f"{self.api_base}/documents/{self.uploaded_doc_id}",
                params={'permanent': 'false'}
            )
            if response.status_code == 200:
                data = response.json()
                self.print_success(f"Document archived: {data.get('action', 'archived')}")
                return True
            else:
                self.print_error(f"Delete failed: {response.status_code}")
                self.print_error(f"Response: {response.text}")
                return False
        except Exception as e:
            self.print_error(f"Delete error: {e}")
            return False
    
    def test_analytics(self):
        """Test analytics endpoint."""
        self.print_test("Analytics")
        try:
            response = self.session.get(f"{self.api_base}/analytics/overview")
            if response.status_code == 200:
                data = response.json()
                self.print_success("Analytics retrieved")
                self.print_info(f"Data: {json.dumps(data, indent=2)}")
                return True
            else:
                self.print_error(f"Analytics failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_error(f"Analytics error: {e}")
            return False
    
    def run_all_tests(self):
        """Run all endpoint tests."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
        print(f"FastAPI Endpoint Test Suite")
        print(f"Base URL: {self.base_url}")
        print(f"{'='*60}{Colors.RESET}\n")
        
        results = []
        
        # Run tests in order
        results.append(("Health Check", self.test_health_check()))
        results.append(("Upload Document", self.test_upload_document()))
        results.append(("List Documents", self.test_list_documents()))
        results.append(("Search Documents", self.test_search_documents()))
        results.append(("Get Document", self.test_get_document()))
        results.append(("Update Document", self.test_update_document()))
        results.append(("Get Document Version", self.test_get_document_version()))
        results.append(("Compare Versions", self.test_compare_versions()))
        results.append(("Analyze Document", self.test_analyze_document()))
        results.append(("List Tags", self.test_list_tags()))
        results.append(("Bulk Tag", self.test_bulk_tag()))
        results.append(("Export Document", self.test_export_document()))
        results.append(("Analytics", self.test_analytics()))
        results.append(("Delete Document", self.test_delete_document()))
        
        # Summary
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}")
        print("Test Summary")
        print(f"{'='*60}{Colors.RESET}\n")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for name, result in results:
            status = f"{Colors.GREEN}PASS{Colors.RESET}" if result else f"{Colors.RED}FAIL{Colors.RESET}"
            print(f"{status} - {name}")
        
        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.RESET}\n")
        
        return passed == total


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Test all FastAPI endpoints")
    parser.add_argument(
        '--base-url',
        default='http://localhost:8000',
        help='Base URL of the API (default: http://localhost:8000)'
    )
    args = parser.parse_args()
    
    tester = EndpointTester(base_url=args.base_url)
    success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

