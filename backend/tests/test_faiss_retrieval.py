"""Test FAISS retrieval"""

import asyncio
import sys
sys.path.insert(0, '/app')

from backend.database.faiss_store import faiss_manager


async def test_faiss_search():
    """Test FAISS search functionality"""
    
    # Initialize FAISS
    await faiss_manager.initialize()
    
    # Test query
    query = "Anonim şirket nasıl kurulur?"
    
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}\n")
    
    # Search in ticaret_hukuku collection
    results = await faiss_manager.search(
        collection_name="ticaret_hukuku",
        query=query,
        limit=3
    )
    
    print(f"Found {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"\n--- Result {i} ---")
        print(f"ID: {result.get('id')}")
        print(f"Score: {result.get('score', 0):.4f}")
        print(f"Text (first 200 chars):\n{result.get('text', '')[:200]}...")
        print(f"\nMetadata:")
        for key, value in result.get('metadata', {}).items():
            print(f"  {key}: {value}")
    
    # Get collection stats
    print(f"\n{'='*60}")
    print("Collection Stats:")
    print(f"{'='*60}")
    stats = faiss_manager.get_stats()
    for name, stat in stats.items():
        print(f"{name}: {stat}")


if __name__ == "__main__":
    asyncio.run(test_faiss_search())
