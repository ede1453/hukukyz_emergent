"""Test script for versioning system

Demonstrates:
1. Creating version 1 of a document
2. Creating version 2 that replaces version 1
3. Deprecating version 1
4. Querying specific versions
5. Getting version history
"""

import asyncio
from backend.core.version_manager import version_manager, DocumentStatus
from backend.database.qdrant_client import qdrant_manager
from backend.utils.embeddings import get_embedding


async def test_versioning():
    """Test the versioning system"""
    
    print("=" * 60)
    print("🧪 Testing Versioning System")
    print("=" * 60)
    
    collection = "ticaret_hukuku"
    doc_id = "TTK_11"
    
    # Step 1: Create version 1
    print("\n📝 Step 1: Creating version 1...")
    
    v1_metadata = await version_manager.create_version_metadata(
        doc_id=doc_id,
        version="2023.01.01",
        status=DocumentStatus.ACTIVE,
        effective_date="2023-01-01T00:00:00",
        reason="Initial version"
    )
    
    # Simulate adding document with version
    text_v1 = "TTK Madde 11 (Versiyon 1): Anonim şirket en az bir kişi tarafından kurulabilir."
    embedding = await get_embedding(text_v1)
    
    point = {
        "id": 10001,
        "vector": embedding,
        "payload": {
            "doc_id": doc_id,
            "text": text_v1,
            "kaynak": "TTK",
            "madde_no": 11,
            **v1_metadata
        }
    }
    
    qdrant_manager.upsert_points(collection, [point])
    print(f"✅ Version 1 created: {v1_metadata['version']}")
    print(f"   Status: {v1_metadata['status']}")
    print(f"   Effective: {v1_metadata['effective_date']}")
    
    # Step 2: Get all versions
    print("\n📚 Step 2: Getting all versions...")
    versions = await version_manager.get_versions(
        qdrant_manager.client,
        collection,
        doc_id,
        include_deprecated=True
    )
    print(f"✅ Found {len(versions)} version(s)")
    for v in versions:
        print(f"   - {v.version} ({v.status.value})")
    
    # Step 3: Create version 2
    print("\n📝 Step 3: Creating version 2...")
    
    v2_metadata = await version_manager.create_version_metadata(
        doc_id=doc_id,
        version="2024.11.14",
        status=DocumentStatus.ACTIVE,
        effective_date="2024-11-14T00:00:00",
        reason="Updated law text"
    )
    
    text_v2 = "TTK Madde 11 (Versiyon 2): Anonim şirket en az bir pay sahibi tarafından kurulabilir. Yeni hüküm."
    embedding_v2 = await get_embedding(text_v2)
    
    point_v2 = {
        "id": 10002,
        "vector": embedding_v2,
        "payload": {
            "doc_id": doc_id,
            "text": text_v2,
            "kaynak": "TTK",
            "madde_no": 11,
            **v2_metadata
        }
    }
    
    qdrant_manager.upsert_points(collection, [point_v2])
    print(f"✅ Version 2 created: {v2_metadata['version']}")
    
    # Step 4: Deprecate version 1
    print("\n🗑️  Step 4: Deprecating version 1...")
    await version_manager.deprecate_version(
        qdrant_manager.client,
        collection,
        doc_id,
        "2023.01.01",
        reason="Replaced by newer version",
        replaced_by="2024.11.14"
    )
    print("✅ Version 1 deprecated")
    
    # Step 5: Get all versions again
    print("\n📚 Step 5: Getting updated version list...")
    all_versions = await version_manager.get_versions(
        qdrant_manager.client,
        collection,
        doc_id,
        include_deprecated=True
    )
    print(f"✅ Found {len(all_versions)} version(s)")
    for v in all_versions:
        status_emoji = "🟢" if v.status == DocumentStatus.ACTIVE else "🔴"
        print(f"   {status_emoji} {v.version} ({v.status.value})")
        if v.deprecated_date:
            print(f"      Deprecated: {v.deprecated_date}")
            print(f"      Reason: {v.reason}")
            print(f"      Replaced by: {v.replaced_by}")
    
    # Step 6: Get only active version
    print("\n✨ Step 6: Getting active version...")
    active = await version_manager.get_active_version(
        qdrant_manager.client,
        collection,
        doc_id
    )
    if active:
        print(f"✅ Active version: {active.version}")
        print(f"   Status: {active.status.value}")
        print(f"   Effective: {active.effective_date}")
    
    print("\n" + "=" * 60)
    print("✅ Versioning test completed!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_versioning())
