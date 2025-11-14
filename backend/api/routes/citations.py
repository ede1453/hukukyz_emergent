"""Citation tracking API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
import logging

from backend.tools.citation_tracker import citation_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/citations", tags=["citations"])


@router.get("/stats")
async def get_citation_stats():
    """Get overall citation statistics
    
    Returns:
        Citation statistics including most cited articles
    """
    try:
        stats = await citation_tracker.get_citation_stats()
        return {
            "success": True,
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error getting citation stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/most-cited")
async def get_most_cited(limit: int = 10):
    """Get most cited articles
    
    Args:
        limit: Number of results (default: 10, max: 50)
    
    Returns:
        List of most cited articles with counts
    """
    try:
        if limit > 50:
            limit = 50
        
        most_cited = await citation_tracker.get_most_cited(limit=limit)
        
        return {
            "success": True,
            "data": [
                {
                    "reference": ref,
                    "citation_count": count
                }
                for ref, count in most_cited
            ]
        }
    except Exception as e:
        logger.error(f"Error getting most cited: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/related/{reference}")
async def get_related_articles(reference: str, limit: int = 5):
    """Get related articles for a reference
    
    Args:
        reference: Legal reference (e.g., "TTK m.11")
        limit: Number of results (default: 5, max: 20)
    
    Returns:
        List of related articles
    """
    try:
        if limit > 20:
            limit = 20
        
        related = await citation_tracker.get_related_articles(reference, limit=limit)
        
        return {
            "success": True,
            "data": [
                {
                    "reference": ref,
                    "relationship": rel
                }
                for ref, rel in related
            ]
        }
    except Exception as e:
        logger.error(f"Error getting related articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear")
async def clear_citations():
    """Clear all citation tracking data
    
    ⚠️ This will delete all tracked citations!
    
    Returns:
        Success message
    """
    try:
        await citation_tracker.clear()
        
        return {
            "success": True,
            "message": "All citation data cleared"
        }
    except Exception as e:
        logger.error(f"Error clearing citations: {e}")
        raise HTTPException(status_code=500, detail=str(e))
