"""Qdrant vector database client"""

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict, Optional
import logging
import uuid

from backend.config import settings

logger = logging.getLogger(__name__)


class QdrantManager:
    """Qdrant client manager"""
    
    # Collection definitions
    COLLECTIONS = {
        "ticaret_hukuku": "Ticaret Hukuku (TTK)",
        "borclar_hukuku": "Borçlar Hukuku (TBK)",
        "icra_iflas": "İcra İflas (İİK)",
        "medeni_hukuk": "Medeni Hukuk (TMK)",
        "tuketici_haklari": "Tüketici Hakları (TKHK)",
        "bankacilik_hukuku": "Bankacılık Hukuku",
        "hmk": "Hukuk Muhakemeleri Kanunu"
    }
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
    
    async def initialize(self):
        """Initialize Qdrant client and collections"""
        try:
            # Connect to Qdrant
            if settings.qdrant_api_key:
                self.client = QdrantClient(
                    url=settings.qdrant_url,
                    api_key=settings.qdrant_api_key
                )
            else:
                self.client = QdrantClient(url=settings.qdrant_url)
            
            logger.info(f"Connected to Qdrant: {settings.qdrant_url}")
            
            # Create collections if they don't exist
            await self._ensure_collections()
            
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    async def _ensure_collections(self):
        """Ensure all required collections exist"""
        existing_collections = [col.name for col in self.client.get_collections().collections]
        
        for collection_name in self.COLLECTIONS.keys():
            if collection_name not in existing_collections:
                logger.info(f"Creating collection: {collection_name}")
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # text-embedding-3-small dimension
                        distance=Distance.COSINE
                    )
                )
                
                # Create payload indexes for efficient filtering
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="status",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="doc_type",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name="kaynak",
                        field_schema=models.PayloadSchemaType.KEYWORD
                    )
                except Exception as e:
                    logger.warning(f"Could not create all indexes: {e}")
                
                logger.info(f"✅ Collection created: {collection_name}")
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        filters: Optional[Dict] = None,
        score_threshold: Optional[float] = None
    ) -> List[Dict]:
        """Search vectors in collection"""
        try:
            # Build filter if provided
            query_filter = None
            if filters:
                query_filter = models.Filter(
                    must=[
                        models.FieldCondition(
                            key=key,
                            match=models.MatchValue(value=value)
                        )
                        for key, value in filters.items()
                    ]
                )
            
            # Search
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold
            )
            
            # Format results
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "payload": hit.payload
                }
                for hit in results
            ]
            
        except Exception as e:
            logger.error(f"Search error in {collection_name}: {e}")
            return []
    
    def upsert_points(
        self,
        collection_name: str,
        points: List[Dict]
    ) -> bool:
        """Upsert points to collection"""
        try:
            qdrant_points = [
                PointStruct(
                    id=point.get("id", str(uuid.uuid4())),
                    vector=point["vector"],
                    payload=point.get("payload", {})
                )
                for point in points
            ]
            
            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points
            )
            
            logger.info(f"Upserted {len(points)} points to {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Upsert error in {collection_name}: {e}")
            return False
    
    def delete_points(
        self,
        collection_name: str,
        point_ids: List[str]
    ) -> bool:
        """Delete points from collection"""
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=models.PointIdsList(
                    points=point_ids
                )
            )
            logger.info(f"Deleted {len(point_ids)} points from {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Delete error in {collection_name}: {e}")
            return False
    
    def get_collection_info(self, collection_name: str) -> Dict:
        """Get collection info"""
        try:
            info = self.client.get_collection(collection_name=collection_name)
            return {
                "name": collection_name,
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {}
    
    async def add_documents(
        self,
        collection_name: str,
        texts: List[str],
        metadatas: List[Dict],
        batch_size: int = 50  # Smaller batches to avoid payload size limit
    ):
        """Add documents to collection with embeddings in batches"""
        try:
            from backend.utils.embeddings import embedding_service
            
            logger.info(f"Adding {len(texts)} documents to {collection_name} in batches of {batch_size}")
            
            # Get current max ID in collection
            try:
                collection_info = self.client.get_collection(collection_name)
                start_id = collection_info.points_count
            except:
                start_id = 0
            
            total_added = 0
            
            # Process in batches
            for batch_start in range(0, len(texts), batch_size):
                batch_end = min(batch_start + batch_size, len(texts))
                batch_texts = texts[batch_start:batch_end]
                batch_metadatas = metadatas[batch_start:batch_end]
                
                logger.info(f"Processing batch {batch_start//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
                
                # Generate embeddings for this batch
                embeddings = await embedding_service.embed_batch(batch_texts)
                
                # Create points
                points = []
                for i, (text, embedding, metadata) in enumerate(zip(batch_texts, embeddings, batch_metadatas)):
                    points.append({
                        "id": start_id + batch_start + i,
                        "vector": embedding,
                        "payload": {
                            **metadata,
                            "text": text
                        }
                    })
                
                # Upsert this batch to Qdrant
                success = self.upsert_points(collection_name, points)
                if success:
                    total_added += len(points)
                    logger.info(f"✅ Batch uploaded: {len(points)} documents")
                else:
                    logger.error(f"❌ Batch upload failed for range {batch_start}-{batch_end}")
                    raise Exception(f"Failed to upload batch {batch_start}-{batch_end}")
            
            logger.info(f"✅ Successfully added {total_added}/{len(texts)} documents to {collection_name}")
            
        except Exception as e:
            logger.error(f"Error adding documents to {collection_name}: {e}", exc_info=True)
            raise


# Global Qdrant manager instance
qdrant_manager = QdrantManager()
