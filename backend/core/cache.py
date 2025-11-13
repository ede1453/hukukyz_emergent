"""Redis-based caching system for HukukYZ

Caching Strategy:
1. Query Cache: Full query -> answer caching (1 hour TTL)
2. Document Cache: Retrieval results (30 min TTL)
3. Embedding Cache: Text -> embedding vectors (24 hours TTL)
4. LLM Response Cache: Prompt -> response (1 hour TTL)
"""

import redis.asyncio as redis
import json
import hashlib
import logging
from typing import Optional, Dict, List, Any
from datetime import timedelta

from backend.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager with multiple cache types"""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
        
        # TTL configurations (in seconds)
        self.TTL_QUERY = 3600  # 1 hour for query results
        self.TTL_DOCUMENTS = 1800  # 30 minutes for document retrieval
        self.TTL_EMBEDDINGS = 86400  # 24 hours for embeddings
        self.TTL_LLM = 3600  # 1 hour for LLM responses
        self.TTL_ANALYSIS = 7200  # 2 hours for analysis results
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = await redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            self._connected = True
            logger.info("✅ Redis cache connected successfully")
        except Exception as e:
            logger.warning(f"⚠️  Redis connection failed: {e}. Cache disabled.")
            self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis cache disconnected")
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate cache key with hash
        
        Args:
            prefix: Key prefix (e.g., 'query', 'doc', 'emb')
            *args: Arguments to hash
        
        Returns:
            Cache key string
        """
        # Create a deterministic hash from arguments
        content = json.dumps(args, sort_keys=True, ensure_ascii=False)
        hash_digest = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"hukukyz:{prefix}:{hash_digest}"
    
    # ========== Query Cache ==========
    
    async def get_query_cache(self, query: str, collections: List[str] = None) -> Optional[Dict]:
        """Get cached query result
        
        Args:
            query: User query
            collections: Target collections
        
        Returns:
            Cached result or None
        """
        if not self._connected:
            return None
        
        try:
            key = self._generate_key("query", query, collections or [])
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.info(f"✅ Query cache HIT: {query[:50]}...")
                return json.loads(cached)
            
            logger.debug(f"❌ Query cache MISS: {query[:50]}...")
            return None
        except Exception as e:
            logger.error(f"Query cache get error: {e}")
            return None
    
    async def set_query_cache(
        self, 
        query: str, 
        result: Dict, 
        collections: List[str] = None
    ):
        """Cache query result
        
        Args:
            query: User query
            result: Query result to cache
            collections: Target collections
        """
        if not self._connected:
            return
        
        try:
            key = self._generate_key("query", query, collections or [])
            await self.redis_client.setex(
                key,
                self.TTL_QUERY,
                json.dumps(result, ensure_ascii=False)
            )
            logger.info(f"✅ Query cached: {query[:50]}...")
        except Exception as e:
            logger.error(f"Query cache set error: {e}")
    
    # ========== Document Retrieval Cache ==========
    
    async def get_document_cache(
        self, 
        query: str, 
        collections: List[str],
        limit: int = 5
    ) -> Optional[List[Dict]]:
        """Get cached document retrieval results"""
        if not self._connected:
            return None
        
        try:
            key = self._generate_key("doc", query, collections, limit)
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.info(f"✅ Document cache HIT: {query[:50]}...")
                return json.loads(cached)
            
            return None
        except Exception as e:
            logger.error(f"Document cache get error: {e}")
            return None
    
    async def set_document_cache(
        self,
        query: str,
        collections: List[str],
        documents: List[Dict],
        limit: int = 5
    ):
        """Cache document retrieval results"""
        if not self._connected:
            return
        
        try:
            key = self._generate_key("doc", query, collections, limit)
            await self.redis_client.setex(
                key,
                self.TTL_DOCUMENTS,
                json.dumps(documents, ensure_ascii=False)
            )
            logger.info(f"✅ Documents cached: {len(documents)} docs")
        except Exception as e:
            logger.error(f"Document cache set error: {e}")
    
    # ========== Embedding Cache ==========
    
    async def get_embedding_cache(self, text: str) -> Optional[List[float]]:
        """Get cached embedding vector"""
        if not self._connected:
            return None
        
        try:
            key = self._generate_key("emb", text[:500])  # Limit text length
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.debug(f"✅ Embedding cache HIT")
                return json.loads(cached)
            
            return None
        except Exception as e:
            logger.error(f"Embedding cache get error: {e}")
            return None
    
    async def set_embedding_cache(self, text: str, embedding: List[float]):
        """Cache embedding vector"""
        if not self._connected:
            return
        
        try:
            key = self._generate_key("emb", text[:500])
            await self.redis_client.setex(
                key,
                self.TTL_EMBEDDINGS,
                json.dumps(embedding)
            )
            logger.debug(f"✅ Embedding cached")
        except Exception as e:
            logger.error(f"Embedding cache set error: {e}")
    
    # ========== LLM Response Cache ==========
    
    async def get_llm_cache(
        self, 
        prompt: str, 
        model: str,
        temperature: float = 0.0
    ) -> Optional[str]:
        """Get cached LLM response"""
        if not self._connected or temperature > 0:  # Don't cache non-deterministic
            return None
        
        try:
            key = self._generate_key("llm", prompt, model)
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.info(f"✅ LLM cache HIT")
                return cached
            
            return None
        except Exception as e:
            logger.error(f"LLM cache get error: {e}")
            return None
    
    async def set_llm_cache(
        self,
        prompt: str,
        model: str,
        response: str,
        temperature: float = 0.0
    ):
        """Cache LLM response"""
        if not self._connected or temperature > 0:
            return
        
        try:
            key = self._generate_key("llm", prompt, model)
            await self.redis_client.setex(
                key,
                self.TTL_LLM,
                response
            )
            logger.info(f"✅ LLM response cached")
        except Exception as e:
            logger.error(f"LLM cache set error: {e}")
    
    # ========== Analysis Cache ==========
    
    async def get_analysis_cache(self, doc_ids: List[str]) -> Optional[Dict]:
        """Get cached analysis results"""
        if not self._connected:
            return None
        
        try:
            key = self._generate_key("analysis", sorted(doc_ids))
            cached = await self.redis_client.get(key)
            
            if cached:
                logger.info(f"✅ Analysis cache HIT")
                return json.loads(cached)
            
            return None
        except Exception as e:
            logger.error(f"Analysis cache get error: {e}")
            return None
    
    async def set_analysis_cache(self, doc_ids: List[str], analysis: Dict):
        """Cache analysis results"""
        if not self._connected:
            return
        
        try:
            key = self._generate_key("analysis", sorted(doc_ids))
            await self.redis_client.setex(
                key,
                self.TTL_ANALYSIS,
                json.dumps(analysis, ensure_ascii=False)
            )
            logger.info(f"✅ Analysis cached")
        except Exception as e:
            logger.error(f"Analysis cache set error: {e}")
    
    # ========== Cache Management ==========
    
    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern
        
        Args:
            pattern: Redis key pattern (e.g., 'hukukyz:query:*')
        """
        if not self._connected:
            return
        
        try:
            cursor = 0
            deleted = 0
            
            while True:
                cursor, keys = await self.redis_client.scan(
                    cursor=cursor,
                    match=pattern,
                    count=100
                )
                
                if keys:
                    deleted += await self.redis_client.delete(*keys)
                
                if cursor == 0:
                    break
            
            logger.info(f"✅ Invalidated {deleted} keys matching {pattern}")
        except Exception as e:
            logger.error(f"Cache invalidation error: {e}")
    
    async def clear_all(self):
        """Clear all HukukYZ cache"""
        if not self._connected:
            return
        
        try:
            await self.invalidate_pattern("hukukyz:*")
            logger.info("✅ All cache cleared")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._connected:
            return {"connected": False}
        
        try:
            info = await self.redis_client.info("stats")
            
            return {
                "connected": True,
                "hits": info.get("keyspace_hits", 0),
                "misses": info.get("keyspace_misses", 0),
                "hit_rate": round(
                    info.get("keyspace_hits", 0) / 
                    max(info.get("keyspace_hits", 0) + info.get("keyspace_misses", 0), 1) * 100,
                    2
                )
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"connected": False, "error": str(e)}


# Global cache manager instance
cache_manager = CacheManager()
