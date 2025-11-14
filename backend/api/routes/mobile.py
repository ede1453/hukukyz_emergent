"""Mobile API routes - Optimized for mobile apps"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging

from backend.api.routes.auth import get_current_user
from backend.agents.workflow_optimized import execute_workflow
from backend.database.mongodb import mongodb_client
from backend.tools.citation_tracker import citation_tracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mobile", tags=["mobile"])


class MobileQueryRequest(BaseModel):
    """Mobile query request - simplified"""
    query: str
    include_deprecated: bool = False


class MobileQueryResponse(BaseModel):
    """Mobile-optimized response"""
    answer: str
    confidence: float
    citations: List[Dict]
    sources: List[str]
    query_id: str


@router.post("/query", response_model=MobileQueryResponse)
async def mobile_query(
    request: MobileQueryRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    """
    Mobile-optimized query endpoint
    
    Returns simplified response for mobile apps
    """
    try:
        user_id = current_user["email"] if current_user else "anonymous"
        session_id = f"mobile_{user_id}"
        
        # Execute workflow
        result = await execute_workflow(
            query=request.query,
            user_id=user_id,
            session_id=session_id,
            include_deprecated=request.include_deprecated
        )
        
        # Simplify response for mobile
        citations = result.get("citations", [])
        sources = list(set([c.get("source", "Unknown") for c in citations]))
        
        return MobileQueryResponse(
            answer=result.get("final_answer", ""),
            confidence=result.get("confidence", 0.0),
            citations=citations[:5],  # Limit to 5 for mobile
            sources=sources[:5],
            query_id=session_id
        )
        
    except Exception as e:
        logger.error(f"Mobile query error: {e}")
        raise HTTPException(status_code=500, detail="Query failed")


@router.get("/history")
async def get_mobile_history(
    limit: int = 20,
    current_user: dict = Depends(get_current_user)
):
    """Get user's query history"""
    try:
        db = mongodb_client.db
        
        history = await db.conversations.find(
            {"user_id": current_user["email"]},
            {"_id": 0}
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        return {
            "success": True,
            "history": history
        }
        
    except Exception as e:
        logger.error(f"History error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")


@router.get("/trending")
async def get_trending_articles(limit: int = 10):
    """Get trending articles - most cited recently"""
    try:
        stats = await citation_tracker.get_citation_stats()
        most_cited = await citation_tracker.get_most_cited(limit=limit)
        
        return {
            "success": True,
            "trending": [
                {
                    "reference": ref,
                    "citation_count": count,
                    "rank": i + 1
                }
                for i, (ref, count) in enumerate(most_cited)
            ],
            "total_articles": stats.get("unique_references", 0)
        }
        
    except Exception as e:
        logger.error(f"Trending error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending")


@router.get("/article/{reference}")
async def get_mobile_article(reference: str):
    """Get article content - mobile optimized"""
    try:
        from backend.api.routes.citations import get_article_content
        
        result = await get_article_content(reference)
        
        if not result.get("success"):
            return result
        
        # Simplify for mobile
        data = result["data"]
        
        return {
            "success": True,
            "article": {
                "reference": data["reference"],
                "law_code": data["law_code"],
                "article_no": data["article_no"],
                "title": data.get("title", ""),
                "content": data["content"],
                "status": data.get("status", "active")
            }
        }
        
    except Exception as e:
        logger.error(f"Article error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch article")


@router.get("/related/{reference}")
async def get_mobile_related(reference: str, limit: int = 5):
    """Get related articles - mobile optimized"""
    try:
        related = await citation_tracker.get_related_articles(reference, limit=limit)
        
        return {
            "success": True,
            "related": [
                {
                    "reference": ref,
                    "relationship": rel
                }
                for ref, rel in related
            ]
        }
        
    except Exception as e:
        logger.error(f"Related error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch related")


@router.get("/collections")
async def get_collections():
    """Get available legal collections"""
    return {
        "success": True,
        "collections": [
            {
                "id": "ticaret_hukuku",
                "name": "Ticaret Hukuku",
                "code": "TTK",
                "description": "Türk Ticaret Kanunu"
            },
            {
                "id": "borclar_hukuku",
                "name": "Borçlar Hukuku",
                "code": "TBK",
                "description": "Türk Borçlar Kanunu"
            },
            {
                "id": "medeni_hukuk",
                "name": "Medeni Hukuk",
                "code": "TMK",
                "description": "Türk Medeni Kanunu"
            },
            {
                "id": "icra_iflas",
                "name": "İcra ve İflas Hukuku",
                "code": "İİK",
                "description": "İcra ve İflas Kanunu"
            },
            {
                "id": "hmk",
                "name": "Hukuk Muhakemeleri",
                "code": "HMK",
                "description": "Hukuk Muhakemeleri Kanunu"
            }
        ]
    }


@router.get("/stats")
async def get_mobile_stats():
    """Get platform statistics"""
    try:
        citation_stats = await citation_tracker.get_citation_stats()
        
        return {
            "success": True,
            "stats": {
                "total_articles": citation_stats.get("unique_references", 0),
                "total_citations": citation_stats.get("total_citations", 0),
                "documents_tracked": citation_stats.get("documents_tracked", 0),
                "collections": 8
            }
        }
        
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {
            "success": True,
            "stats": {
                "total_articles": 0,
                "total_citations": 0,
                "documents_tracked": 0,
                "collections": 8
            }
        }


@router.get("/health")
async def mobile_health_check():
    """Health check for mobile apps"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "query": True,
            "history": True,
            "trending": True,
            "articles": True,
            "related": True,
            "auth": True
        }
    }
