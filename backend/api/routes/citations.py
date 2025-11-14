"""Citation tracking API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict
import logging

from backend.tools.citation_tracker import citation_tracker
from backend.database.qdrant_client import qdrant_manager
from backend.tools.legal_parser import LegalParser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/citations", tags=["citations"])
legal_parser = LegalParser()


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


@router.get("/article/{reference}")
async def get_article_content(reference: str):
    """Get article content by reference
    
    Args:
        reference: Legal reference (e.g., "TTK m.365")
    
    Returns:
        Article content and metadata
    """
    try:
        # Parse the reference to extract law code and article number
        refs = legal_parser.parse(reference)
        
        if not refs:
            return {
                "success": False,
                "error": "Geçersiz referans formatı"
            }
        
        ref = refs[0]
        law_code = ref.kanun_kodu
        article_no = ref.madde_no
        
        # Map law codes to collections
        collection_map = {
            "TTK": "ticaret_hukuku",
            "TBK": "borclar_hukuku",
            "İİK": "icra_iflas",
            "HMK": "hmk",
            "TMK": "medeni_hukuk"
        }
        
        collection = collection_map.get(law_code)
        
        if not collection:
            return {
                "success": False,
                "error": f"'{law_code}' koleksiyonu bulunamadı"
            }
        
        # Search in Qdrant by doc_id or madde_no
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        await qdrant_manager.initialize()
        
        # Try to find by madde_no
        filter_obj = Filter(
            must=[
                FieldCondition(key="madde_no", match=MatchValue(value=str(article_no)))
            ]
        )
        
        results = qdrant_manager.client.scroll(
            collection_name=collection,
            scroll_filter=filter_obj,
            limit=1,
            with_payload=True
        )
        
        if results and results[0]:
            doc = results[0][0]
            payload = doc.payload
            
            return {
                "success": True,
                "data": {
                    "reference": reference,
                    "law_code": law_code,
                    "article_no": article_no,
                    "title": payload.get("title", ""),
                    "content": payload.get("content", payload.get("text", "")),
                    "doc_type": payload.get("doc_type", ""),
                    "kaynak": payload.get("kaynak", ""),
                    "hukuk_dali": payload.get("hukuk_dali", ""),
                    "status": payload.get("status", "active")
                }
            }
        else:
            return {
                "success": False,
                "error": f"'{reference}' içeriği bulunamadı"
            }
            
    except Exception as e:
        logger.error(f"Error getting article content: {e}")
        return {
            "success": False,
            "error": str(e)
        }


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
