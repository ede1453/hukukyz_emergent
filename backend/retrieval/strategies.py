"""Retrieval strategies for RAG pipeline"""

from typing import List, Dict, Optional
from enum import Enum
import logging
import asyncio

from backend.database.qdrant_client import qdrant_manager
from backend.database.faiss_store import faiss_manager
from backend.utils.embeddings import get_embedding
from backend.config import settings

logger = logging.getLogger(__name__)


class SearchStrategy(str, Enum):
    """Search strategy types"""
    VECTOR = "vector"
    KEYWORD = "keyword"
    HYBRID = "hybrid"


class RetrievalPipeline:
    """Multi-stage retrieval pipeline"""
    
    def __init__(self):
        self.qdrant = qdrant_manager
        self.faiss = faiss_manager
        self.vector_store_type = settings.vector_store_type
    
    async def search(
        self,
        query: str,
        collection: str,
        strategy: SearchStrategy = SearchStrategy.HYBRID,
        limit: int = None,
        filters: Optional[Dict] = None,
        rerank: bool = True
    ) -> List[Dict]:
        """Execute search with specified strategy
        
        Args:
            query: Search query
            collection: Qdrant collection name
            strategy: Search strategy
            limit: Number of results
            filters: Metadata filters
            rerank: Apply reranking
        
        Returns:
            List of retrieved documents
        """
        limit = limit or settings.retrieval_top_k
        
        try:
            logger.info(f"Searching {collection} with {strategy} strategy")
            
            if strategy == SearchStrategy.VECTOR:
                results = await self._vector_search(query, collection, limit, filters)
            elif strategy == SearchStrategy.KEYWORD:
                results = await self._keyword_search(query, collection, limit, filters)
            else:  # HYBRID
                results = await self._hybrid_search(query, collection, limit, filters)
            
            # Apply reranking if requested
            if rerank and len(results) > settings.rerank_top_k:
                results = await self._rerank(query, results)
            
            logger.info(f"Retrieved {len(results)} documents")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return []
    
    async def _vector_search(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Vector similarity search"""
        try:
            # Use FAISS or Qdrant based on config
            if self.vector_store_type == "faiss":
                results = await self.faiss.search(
                    collection_name=collection,
                    query=query,
                    limit=limit,
                    metadata_filter=filters
                )
            else:
                # Generate embedding
                query_vector = await get_embedding(query)
                
                # Search in Qdrant
                results = self.qdrant.search(
                    collection_name=collection,
                    query_vector=query_vector,
                    limit=limit,
                    filters=filters
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []
    
    async def _keyword_search(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Keyword-based search (BM25-like)
        
        Note: Qdrant doesn't have native BM25, so we use payload search
        with embedding as fallback
        """
        # For now, use vector search with high recall
        # In production, consider using Elasticsearch for keyword search
        return await self._vector_search(query, collection, limit * 2, filters)
    
    async def _hybrid_search(
        self,
        query: str,
        collection: str,
        limit: int,
        filters: Optional[Dict]
    ) -> List[Dict]:
        """Hybrid search using Reciprocal Rank Fusion (RRF)"""
        # Run both searches in parallel
        vector_task = self._vector_search(query, collection, limit, filters)
        keyword_task = self._keyword_search(query, collection, limit, filters)
        
        vector_results, keyword_results = await asyncio.gather(
            vector_task, keyword_task
        )
        
        # Apply RRF
        fused_results = self._reciprocal_rank_fusion(
            [vector_results, keyword_results],
            limit
        )
        
        return fused_results
    
    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Dict]],
        limit: int,
        k: int = 60
    ) -> List[Dict]:
        """Reciprocal Rank Fusion algorithm
        
        Args:
            result_lists: List of result lists from different strategies
            limit: Number of results to return
            k: RRF constant (default 60)
        
        Returns:
            Fused and ranked results
        """
        # Calculate RRF scores
        rrf_scores = {}
        doc_map = {}
        
        for results in result_lists:
            for rank, doc in enumerate(results, start=1):
                doc_id = doc["id"]
                score = 1.0 / (k + rank)
                
                if doc_id in rrf_scores:
                    rrf_scores[doc_id] += score
                else:
                    rrf_scores[doc_id] = score
                    doc_map[doc_id] = doc
        
        # Sort by RRF score
        sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
        
        # Return top results
        fused_results = []
        for doc_id in sorted_ids[:limit]:
            doc = doc_map[doc_id]
            doc["rrf_score"] = rrf_scores[doc_id]
            fused_results.append(doc)
        
        return fused_results
    
    async def _rerank(
        self,
        query: str,
        candidates: List[Dict],
        top_k: int = None
    ) -> List[Dict]:
        """Rerank candidates using cross-encoder
        
        Note: This is a placeholder. In production, use sentence-transformers
        cross-encoder model for better precision.
        """
        top_k = top_k or settings.rerank_top_k
        
        # TODO: Implement cross-encoder reranking
        # For now, return top candidates based on original scores
        logger.info(f"Reranking {len(candidates)} candidates to top {top_k}")
        
        # Sort by score
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("score", 0),
            reverse=True
        )
        
        return sorted_candidates[:top_k]


# Global instance
retrieval_pipeline = RetrievalPipeline()
