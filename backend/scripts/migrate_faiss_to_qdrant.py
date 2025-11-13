"""Migrate data from FAISS to Qdrant"""

import asyncio
import sys
sys.path.insert(0, '/app')

from backend.database.faiss_store import faiss_manager
from backend.database.qdrant_client import qdrant_manager
from backend.utils.embeddings import embedding_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Migrate all FAISS collections to Qdrant"""
    try:
        # Initialize both
        logger.info("Initializing FAISS...")
        await faiss_manager.initialize()
        
        logger.info("Initializing Qdrant...")
        await qdrant_manager.initialize()
        
        # Get FAISS stats
        faiss_stats = faiss_manager.get_stats()
        
        logger.info(f"\n{'='*60}")
        logger.info("FAISS Collections:")
        for name, stat in faiss_stats.items():
            logger.info(f"  {name}: {stat['document_count']} documents")
        logger.info(f"{'='*60}\n")
        
        total_migrated = 0
        
        # Migrate each collection
        for collection_name, stat in faiss_stats.items():
            doc_count = stat['document_count']
            
            if doc_count == 0:
                logger.info(f"⏭️  Skipping empty collection: {collection_name}")
                continue
            
            logger.info(f"\n📦 Migrating {collection_name} ({doc_count} documents)...")
            
            # Get FAISS collection
            faiss_collection = faiss_manager.get_collection(collection_name)
            
            if not faiss_collection:
                logger.warning(f"Collection {collection_name} not found in FAISS")
                continue
            
            # Prepare points for Qdrant
            points = []
            
            for i, doc in enumerate(faiss_collection.documents):
                # Extract metadata
                metadata = doc.metadata if doc.metadata else {}
                
                # Get embedding (already stored in FAISS)
                # We need to extract it from FAISS index
                embedding_vector = faiss_collection.index.reconstruct(i)
                
                # Create Qdrant point (ID must be integer or UUID, not string)
                # Use index as ID for simplicity
                point_id = i
                doc_id_str = metadata.get('doc_id', f"{collection_name}_{i}")
                
                points.append({
                    "id": point_id,  # Integer ID
                    "vector": embedding_vector.tolist(),
                    "payload": {
                        "doc_id": doc_id_str,  # Original string ID in payload
                        "text": doc.text,
                        "kaynak": metadata.get('kaynak', 'UNKNOWN'),
                        "doc_type": metadata.get('doc_type', 'kanun'),
                        "hukuk_dali": metadata.get('hukuk_dali', ''),
                        "madde_no": metadata.get('madde_no', ''),
                        "title": metadata.get('title', ''),
                        "content": metadata.get('content', doc.text),
                        "version": metadata.get('version', '1.0'),
                        "status": metadata.get('status', 'active'),
                    }
                })
                
                # Batch upload (every 100 points)
                if len(points) >= 100:
                    qdrant_manager.upsert_points(collection_name, points)
                    logger.info(f"  ✅ Uploaded {len(points)} points")
                    total_migrated += len(points)
                    points = []
            
            # Upload remaining points
            if points:
                qdrant_manager.upsert_points(collection_name, points)
                logger.info(f"  ✅ Uploaded {len(points)} points")
                total_migrated += len(points)
            
            logger.info(f"✅ Completed: {collection_name}")
        
        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 Migration Complete!")
        logger.info(f"Total documents migrated: {total_migrated}")
        logger.info(f"{'='*60}\n")
        
        # Verify Qdrant
        logger.info("Verifying Qdrant collections...")
        for collection_name in faiss_stats.keys():
            try:
                info = qdrant_manager.client.get_collection(collection_name)
                logger.info(f"  ✅ {collection_name}: {info.points_count} points")
            except Exception as e:
                logger.error(f"  ❌ {collection_name}: {e}")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    print("\n" + "="*60)
    print("FAISS → Qdrant Migration")
    print("="*60 + "\n")
    
    asyncio.run(migrate())
    
    print("\n" + "="*60)
    print("Migration script completed!")
    print("="*60 + "\n")
