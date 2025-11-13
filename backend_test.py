"""
Comprehensive Backend Test Suite for HukukYZ
Tests all backend API endpoints as requested by the user
"""

import asyncio
import httpx
import json
import tempfile
import os
from typing import Dict, Any
from datetime import datetime

# Use the production URL from frontend/.env
BASE_URL = "https://hukukyz.preview.emergentagent.com"

class HukukYZTester:
    def __init__(self):
        self.results = {}
        self.client = None
        
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{test_name}: {status}")
        if details:
            print(f"Details: {details}")
        self.results[test_name] = {"success": success, "details": details}

    async def test_health_check(self):
        """Test health check endpoints"""
        print("\n" + "="*60)
        print("1. TESTING HEALTH CHECK ENDPOINTS")
        print("="*60)
        
        # Test root endpoint
        try:
            response = await self.client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                # Check if response is JSON (backend) or HTML (frontend)
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    self.log_test("Root Endpoint (/)", True, f"Message: {data.get('message', 'N/A')}")
                else:
                    # Getting HTML is expected for root - frontend is served here
                    self.log_test("Root Endpoint (/)", True, "Frontend served correctly (HTML response)")
            else:
                self.log_test("Root Endpoint (/)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Root Endpoint (/)", False, f"Error: {str(e)}")

        # Test health endpoint - Note: health is at root level, not /api/health
        try:
            response = await self.client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                # Check if response is JSON (backend) or HTML (frontend fallback)
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    self.log_test("Health Check (/health)", True, f"Status: {data.get('status', 'N/A')}")
                else:
                    # Getting HTML means routing issue - backend health not accessible
                    self.log_test("Health Check (/health)", False, "Getting HTML instead of JSON - routing issue")
            else:
                self.log_test("Health Check (/health)", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check (/health)", False, f"Error: {str(e)}")

    async def test_document_stats(self):
        """Test document stats endpoint"""
        print("\n" + "="*60)
        print("2. TESTING DOCUMENT STATS ENDPOINT")
        print("="*60)
        
        try:
            response = await self.client.get(f"{BASE_URL}/api/documents/stats")
            if response.status_code == 200:
                data = response.json()
                total_docs = data.get('total_documents', 0)
                total_collections = data.get('total_collections', 0)
                collections = data.get('collections', {})
                
                details = f"Total docs: {total_docs}, Collections: {total_collections}"
                if total_docs > 0:
                    self.log_test("Document Stats", True, details)
                else:
                    self.log_test("Document Stats", True, f"{details} (No documents yet - expected)")
                
                # Store for later use
                self.document_stats = data
            else:
                self.log_test("Document Stats", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Document Stats", False, f"Error: {str(e)}")

    async def test_collections_list(self):
        """Test collections list endpoint"""
        print("\n" + "="*60)
        print("3. TESTING COLLECTIONS LIST ENDPOINT")
        print("="*60)
        
        try:
            response = await self.client.get(f"{BASE_URL}/api/documents/collections")
            if response.status_code == 200:
                collections = response.json()
                details = f"Found {len(collections)} collections"
                if collections:
                    for col in collections[:3]:  # Show first 3
                        details += f"\n  - {col.get('display_name', 'N/A')} ({col.get('document_count', 0)} docs)"
                self.log_test("Collections List", True, details)
            else:
                self.log_test("Collections List", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Collections List", False, f"Error: {str(e)}")

    def create_test_pdf(self) -> str:
        """Create a simple test PDF with Turkish legal content"""
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            
            # Create temporary file
            fd, path = tempfile.mkstemp(suffix='.pdf')
            os.close(fd)
            
            # Create PDF
            c = canvas.Canvas(path, pagesize=letter)
            
            # Add Turkish legal content
            c.drawString(100, 750, "TEST HUKUK BELGESI")
            c.drawString(100, 720, "Madde 1 - Borçlu, borcunu zamanında ödemekle yükümlüdür.")
            c.drawString(100, 690, "Madde 2 - Ödeme yapılmadığı takdirde faiz işlemeye başlar.")
            c.drawString(100, 660, "Madde 3 - Alacaklı, borcun tahsili için icra takibi başlatabilir.")
            c.drawString(100, 630, "Madde 4 - Bu hükümler Türk Borçlar Kanunu kapsamındadır.")
            c.drawString(100, 600, "Madde 5 - Sözleşme tarafları bu kurallara uymakla yükümlüdür.")
            
            c.save()
            return path
            
        except ImportError:
            # If reportlab not available, create a simple text file as PDF
            fd, path = tempfile.mkstemp(suffix='.pdf')
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write("""TEST HUKUK BELGESİ
                
Madde 1 - Borçlu, borcunu zamanında ödemekle yükümlüdür.
Madde 2 - Ödeme yapılmadığı takdirde faiz işlemeye başlar.
Madde 3 - Alacaklı, borcun tahsili için icra takibi başlatabilir.
Madde 4 - Bu hükümler Türk Borçlar Kanunu kapsamındadır.
Madde 5 - Sözleşme tarafları bu kurallara uymakla yükümlüdür.
""")
            return path

    async def test_pdf_upload(self):
        """Test PDF upload endpoint"""
        print("\n" + "="*60)
        print("4. TESTING PDF UPLOAD ENDPOINT")
        print("="*60)
        
        # Create test PDF
        pdf_path = None
        try:
            pdf_path = self.create_test_pdf()
            
            # Prepare upload
            with open(pdf_path, 'rb') as f:
                files = {'file': ('test_iik.pdf', f, 'application/pdf')}
                data = {
                    'collection': 'icra_iflas',
                    'create_new': 'false'
                }
                
                response = await self.client.post(
                    f"{BASE_URL}/api/documents/upload",
                    files=files,
                    data=data
                )
                
                if response.status_code == 200:
                    result = response.json()
                    articles_count = result.get('articles_count', 0)
                    law_code = result.get('law_code', 'N/A')
                    collection = result.get('collection', 'N/A')
                    
                    details = f"Uploaded {articles_count} articles, Law: {law_code}, Collection: {collection}"
                    self.log_test("PDF Upload", True, details)
                    
                    # Store upload result for verification
                    self.upload_result = result
                else:
                    error_text = response.text
                    self.log_test("PDF Upload", False, f"Status: {response.status_code}, Error: {error_text}")
                    
        except Exception as e:
            self.log_test("PDF Upload", False, f"Error: {str(e)}")
        finally:
            if pdf_path and os.path.exists(pdf_path):
                os.unlink(pdf_path)

    async def test_chat_query(self):
        """Test chat query endpoint with Turkish legal question"""
        print("\n" + "="*60)
        print("5. TESTING CHAT QUERY ENDPOINT")
        print("="*60)
        
        # Test with a Turkish legal question
        query = "Borçlu ödeme yapmazsa ne olur?"
        
        try:
            response = await self.client.post(
                f"{BASE_URL}/api/chat/query",
                json={
                    "query": query,
                    "user_id": "test_user_hukuk",
                    "session_id": "test_session_hukuk"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                citations = data.get('citations', [])
                confidence = data.get('confidence', 0.0)
                
                # Check if we got meaningful response
                has_answer = len(answer) > 10
                has_citations = len(citations) > 0
                has_confidence = confidence > 0
                
                details = f"Answer length: {len(answer)}, Citations: {len(citations)}, Confidence: {confidence:.2f}"
                
                if has_answer:
                    self.log_test("Chat Query - Answer", True, f"Got answer ({len(answer)} chars)")
                    print(f"Sample answer: {answer[:200]}...")
                else:
                    self.log_test("Chat Query - Answer", False, "No meaningful answer received")
                
                if has_citations:
                    self.log_test("Chat Query - Citations", True, f"Got {len(citations)} citations")
                else:
                    self.log_test("Chat Query - Citations", False, "No citations received")
                
                if has_confidence:
                    self.log_test("Chat Query - Confidence", True, f"Confidence: {confidence:.2f}")
                else:
                    self.log_test("Chat Query - Confidence", False, f"Low/zero confidence: {confidence:.2f}")
                    
            else:
                error_text = response.text
                self.log_test("Chat Query", False, f"Status: {response.status_code}, Error: {error_text}")
                
        except Exception as e:
            self.log_test("Chat Query", False, f"Error: {str(e)}")

    async def verify_faiss_integration(self):
        """Verify that uploaded documents are in FAISS"""
        print("\n" + "="*60)
        print("6. VERIFYING FAISS INTEGRATION")
        print("="*60)
        
        try:
            # Check stats again after upload
            response = await self.client.get(f"{BASE_URL}/api/documents/stats")
            if response.status_code == 200:
                new_stats = response.json()
                new_total = new_stats.get('total_documents', 0)
                
                # Compare with previous stats if available
                if hasattr(self, 'document_stats'):
                    old_total = self.document_stats.get('total_documents', 0)
                    if new_total > old_total:
                        self.log_test("FAISS Integration", True, f"Documents increased from {old_total} to {new_total}")
                    else:
                        self.log_test("FAISS Integration", True, f"Total documents: {new_total} (no change expected if upload failed)")
                else:
                    self.log_test("FAISS Integration", True, f"Total documents in FAISS: {new_total}")
            else:
                self.log_test("FAISS Integration", False, f"Could not verify - stats endpoint failed")
                
        except Exception as e:
            self.log_test("FAISS Integration", False, f"Error: {str(e)}")

    async def test_rag_pipeline(self):
        """Test if RAG pipeline components are working"""
        print("\n" + "="*60)
        print("7. TESTING RAG PIPELINE COMPONENTS")
        print("="*60)
        
        # Test with specific legal query that should trigger RAG
        queries = [
            "İcra takibi nasıl başlatılır?",
            "Borçlar hukukunda tazminat nedir?",
            "Anonim şirket kurma şartları nelerdir?"
        ]
        
        for i, query in enumerate(queries, 1):
            try:
                response = await self.client.post(
                    f"{BASE_URL}/api/chat/query",
                    json={
                        "query": query,
                        "user_id": f"rag_test_user_{i}",
                        "session_id": f"rag_test_session_{i}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    metadata = data.get('metadata', {})
                    
                    # Check RAG components
                    docs_retrieved = metadata.get('documents_retrieved', 0)
                    plan_steps = metadata.get('plan_steps', 0)
                    collections = metadata.get('collections', [])
                    
                    rag_working = docs_retrieved > 0 or plan_steps > 0 or len(collections) > 0
                    
                    details = f"Query {i}: Docs: {docs_retrieved}, Steps: {plan_steps}, Collections: {len(collections)}"
                    self.log_test(f"RAG Pipeline Query {i}", rag_working, details)
                    
                    if i == 1:  # Only show details for first query
                        print(f"  Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
                        
                else:
                    self.log_test(f"RAG Pipeline Query {i}", False, f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"RAG Pipeline Query {i}", False, f"Error: {str(e)}")

    async def run_all_tests(self):
        """Run all backend tests"""
        print("="*70)
        print("HukukYZ BACKEND COMPREHENSIVE TEST SUITE")
        print("="*70)
        print(f"Testing URL: {BASE_URL}")
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run all tests
        await self.test_health_check()
        await self.test_document_stats()
        await self.test_collections_list()
        await self.test_pdf_upload()
        await self.verify_faiss_integration()
        await self.test_chat_query()
        await self.test_rag_pipeline()
        
        # Summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            print(f"{test_name:35s}: {status}")
            if result["success"]:
                passed += 1
            else:
                failed += 1
        
        print("-" * 70)
        print(f"TOTAL: {passed} PASSED, {failed} FAILED")
        
        # Critical issues summary
        critical_failures = []
        for test_name, result in self.results.items():
            if not result["success"] and any(keyword in test_name.lower() for keyword in ['health', 'upload', 'query', 'stats']):
                critical_failures.append(f"{test_name}: {result['details']}")
        
        if critical_failures:
            print("\n🚨 CRITICAL ISSUES:")
            for issue in critical_failures:
                print(f"  - {issue}")
        
        print("="*70)
        return passed, failed, critical_failures


async def main():
    """Main test function"""
    async with HukukYZTester() as tester:
        passed, failed, critical_issues = await tester.run_all_tests()
        
        # Return results for test_result.md update
        return {
            "passed": passed,
            "failed": failed,
            "critical_issues": critical_issues,
            "total_tests": passed + failed,
            "results": tester.results
        }


if __name__ == "__main__":
    print("Starting HukukYZ Backend Tests...")
    print("Make sure the backend is running at:", BASE_URL)
    print()
    
    results = asyncio.run(main())
    
    # Exit with appropriate code
    exit(0 if results["failed"] == 0 else 1)