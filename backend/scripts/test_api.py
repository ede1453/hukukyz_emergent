"""Script to test HukukYZ API"""

import asyncio
import httpx
import json
from typing import Dict

BASE_URL = "http://localhost:8001"


async def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_mcp_health():
    """Test MCP servers health"""
    print("\n" + "="*60)
    print("Testing MCP Servers Health")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/chat/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200


async def test_query(query: str):
    """Test query endpoint"""
    print("\n" + "="*60)
    print(f"Testing Query: {query}")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/api/chat/query",
            json={
                "query": query,
                "user_id": "test_user",
                "session_id": "test_session"
            }
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nAnswer:")
            print("-" * 60)
            print(data.get("answer", "No answer"))
            print("-" * 60)
            print(f"\nConfidence: {data.get('confidence', 0):.2f}")
            print(f"Citations: {len(data.get('citations', []))}")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200


async def test_list_documents():
    """Test list documents endpoint"""
    print("\n" + "="*60)
    print("Testing List Documents")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/api/documents/list")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            docs = response.json()
            print(f"Total documents: {len(docs)}")
            for doc in docs[:5]:  # Show first 5
                print(f"  - {doc['filename']} ({doc['hukuk_dali']}, {doc['chunks_count']} chunks)")
        else:
            print(f"Error: {response.text}")
        
        return response.status_code == 200


async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*70)
    print("HukukYZ API Test Suite")
    print("="*70)
    
    results = {}
    
    # Test 1: Health
    results["health"] = await test_health()
    await asyncio.sleep(1)
    
    # Test 2: MCP Health
    results["mcp_health"] = await test_mcp_health()
    await asyncio.sleep(1)
    
    # Test 3: List Documents
    results["list_documents"] = await test_list_documents()
    await asyncio.sleep(1)
    
    # Test 4: Simple Query
    results["query_simple"] = await test_query("TTK 11. madde nedir?")
    await asyncio.sleep(2)
    
    # Test 5: Complex Query
    results["query_complex"] = await test_query(
        "Anonim şirket ile kollektif şirket arasındaki farklar nelerdir?"
    )
    await asyncio.sleep(2)
    
    # Test 6: TBK Query
    results["query_tbk"] = await test_query("TBK'da sözleşme nasıl kurulur?")
    
    # Summary
    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:20s}: {status}")
    
    total_passed = sum(results.values())
    total_tests = len(results)
    
    print("-" * 70)
    print(f"Total: {total_passed}/{total_tests} tests passed")
    print("="*70)
    
    return total_passed == total_tests


if __name__ == "__main__":
    print("Starting API tests...")
    print("Make sure the backend server is running on http://localhost:8001")
    print()
    
    success = asyncio.run(run_all_tests())
    
    exit(0 if success else 1)
