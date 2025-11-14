"""Chat API routes"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
import logging
import uuid
from datetime import datetime

from backend.agents.state import create_initial_state, AgentState
from backend.agents.meta_controller import meta_controller
from backend.mcp.client.mcp_client import mcp_client
from backend.database.mongodb import get_conversations_collection

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models
class QueryRequest(BaseModel):
    """Chat query request"""
    query: str = Field(description="User query")
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    include_deprecated: bool = Field(
        default=False,
        description="Include deprecated/outdated document versions in search results"
    )


class QueryResponse(BaseModel):
    """Chat query response"""
    answer: str
    citations: List[Dict] = []
    confidence: float = 0.0
    reasoning: str = ""
    metadata: Dict = {}


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    mcp_servers: Dict
    timestamp: str


@router.post("/query", response_model=QueryResponse)
async def chat_query(request: QueryRequest):
    """Process chat query using full agent workflow with caching"""
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Import cache and config
        from backend.config import settings
        from backend.core.cache import cache_manager
        
        # Check cache first
        cached_result = await cache_manager.get_query_cache(request.query)
        if cached_result:
            logger.info("✅ Returning cached result")
            return QueryResponse(**cached_result)
        
        # Cache miss - execute workflow
        if settings.use_optimized_workflow:
            from backend.agents.workflow_optimized import execute_workflow
            logger.info("Using optimized workflow")
        else:
            from backend.agents.workflow import execute_workflow
            logger.info("Using standard workflow")
        
        # Execute full agent workflow
        final_state = await execute_workflow(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Extract response fields
        answer = final_state.get("final_answer", "Bir hata oluştu.")
        citations = final_state.get("citations", [])
        confidence = final_state.get("confidence", 0.0)
        reasoning = final_state.get("reasoning", "")
        
        # Build metadata (include performance metrics if available)
        metadata = {
            "hukuk_dali": final_state.get("hukuk_dali", []),
            "collections": final_state.get("collections", []),
            "documents_retrieved": len(final_state.get("retrieved_documents", [])),
            "plan_steps": len(final_state.get("plan", [])),
            "errors": final_state.get("errors", [])
        }
        
        # Add performance metrics if using optimized workflow
        if "agent_timings" in final_state:
            metadata["agent_timings"] = final_state["agent_timings"]
            metadata["total_workflow_time"] = final_state.get("total_workflow_time", 0)
        
        # Save conversation to MongoDB
        conversations = get_conversations_collection()
        await conversations.insert_one({
            "session_id": request.session_id,
            "user_id": request.user_id,
            "query": request.query,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "metadata": metadata,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(f"Query processed successfully. Confidence: {confidence:.2f}")
        
        response = QueryResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata
        )
        
        # Cache the result
        await cache_manager.set_query_cache(
            request.query,
            response.model_dump(),
            collections=metadata.get("collections", [])
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
async def get_conversation_history(session_id: str, limit: int = 20):
    """Get conversation history for a session"""
    try:
        conversations = get_conversations_collection()
        
        # Get conversations for this session, sorted by timestamp
        history = await conversations.find(
            {"session_id": session_id},
            {"_id": 0}  # Exclude MongoDB _id
        ).sort("timestamp", -1).limit(limit).to_list(limit)
        
        # Reverse to get chronological order
        history.reverse()
        
        return {
            "session_id": session_id,
            "count": len(history),
            "conversations": history
        }
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history/{session_id}")
async def clear_conversation_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        conversations = get_conversations_collection()
        result = await conversations.delete_many({"session_id": session_id})
        
        return {
            "session_id": session_id,
            "deleted_count": result.deleted_count,
            "status": "cleared"
        }
        
    except Exception as e:
        logger.error(f"History clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cache/stats")
async def cache_stats():
    """Get cache statistics"""
    try:
        from backend.core.cache import cache_manager
        stats = await cache_manager.get_stats()
        return {
            "cache": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Cache stats error: {e}")
        return {
            "cache": {"connected": False, "error": str(e)},
            "message": "Failed to retrieve cache stats"
        }


@router.post("/cache/clear")
async def clear_cache():
    """Clear all cache"""
    try:
        from backend.core.cache import cache_manager
        await cache_manager.clear_all()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/citations/stats")
async def citation_stats():
    """Get citation statistics"""
    try:
        from backend.tools.citation_tracker import citation_tracker
        stats = citation_tracker.get_citation_stats()
        return {
            "success": True,
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Citation stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/citations/most-cited")
async def most_cited_articles(limit: int = 10):
    """Get most cited articles"""
    try:
        from backend.tools.citation_tracker import citation_tracker
        most_cited = citation_tracker.get_most_cited(limit)
        return {
            "success": True,
            "most_cited": [
                {"reference": ref, "count": count}
                for ref, count in most_cited
            ]
        }
    except Exception as e:
        logger.error(f"Most cited error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Check health of chat service and MCP servers"""
    try:
        # Initialize MCP client if needed
        await mcp_client.initialize()
        
        # Get MCP server health
        mcp_health = await mcp_client.health_check()
        
        return HealthResponse(
            status="healthy",
            mcp_servers=mcp_health,
            timestamp=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/mcp/servers")
async def list_mcp_servers():
    """List all MCP servers"""
    await mcp_client.initialize()
    return {
        "servers": mcp_client.list_servers()
    }


@router.get("/mcp/tools")
async def list_mcp_tools(server: Optional[str] = None):
    """List MCP tools"""
    await mcp_client.initialize()
    return {
        "tools": mcp_client.list_tools(server)
    }
