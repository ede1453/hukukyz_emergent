"""Embedding generation utilities"""

import asyncio
from typing import List, Union
import logging
from openai import AsyncOpenAI
import hashlib
import json

from backend.config import settings

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = AsyncOpenAI(api_key=settings.openai_api_key)

# Simple in-memory cache (in production, use Redis)
_embedding_cache = {}


def _get_cache_key(text: str) -> str:
    """Generate cache key for text"""
    return hashlib.md5(text.encode()).hexdigest()


async def get_embedding(
    text: str,
    model: str = None,
    use_cache: bool = True
) -> List[float]:
    """Generate embedding for text
    
    Args:
        text: Input text
        model: Embedding model (default from settings)
        use_cache: Use cache (default True)
    
    Returns:
        Embedding vector
    """
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")
    
    model = model or settings.embedding_model
    
    # Check cache
    if use_cache:
        cache_key = _get_cache_key(f"{model}:{text}")
        if cache_key in _embedding_cache:
            logger.debug(f"Cache hit for embedding")
            return _embedding_cache[cache_key]
    
    try:
        # Generate embedding
        response = await client.embeddings.create(
            input=text,
            model=model
        )
        
        embedding = response.data[0].embedding
        
        # Cache result
        if use_cache:
            _embedding_cache[cache_key] = embedding
        
        logger.debug(f"Generated embedding: {len(embedding)} dimensions")
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        raise


async def get_embeddings_batch(
    texts: List[str],
    model: str = None,
    batch_size: int = 100
) -> List[List[float]]:
    """Generate embeddings for multiple texts
    
    Args:
        texts: List of texts
        model: Embedding model
        batch_size: Batch size for API calls
    
    Returns:
        List of embedding vectors
    """
    model = model or settings.embedding_model
    embeddings = []
    
    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        
        try:
            response = await client.embeddings.create(
                input=batch,
                model=model
            )
            
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated embeddings for batch {i//batch_size + 1}")
            
        except Exception as e:
            logger.error(f"Batch embedding error: {e}")
            # Return None for failed items
            embeddings.extend([None] * len(batch))
    
    return embeddings


def clear_embedding_cache():
    """Clear embedding cache"""
    global _embedding_cache
    _embedding_cache = {}
    logger.info("Embedding cache cleared")


class EmbeddingService:
    """Service for generating embeddings"""
    
    async def embed_single(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for single text"""
        return await get_embedding(text, use_cache=use_cache)
    
    async def embed_batch(
        self, 
        texts: List[str], 
        batch_size: int = 100
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return await get_embeddings_batch(texts, batch_size=batch_size)
    
    def clear_cache(self):
        """Clear embedding cache"""
        clear_embedding_cache()


# Global service instance
embedding_service = EmbeddingService()
