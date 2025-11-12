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
    """Process chat query using full agent workflow"""
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Import workflow here to avoid circular imports
        from backend.agents.workflow import execute_workflow
        
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
        
        # Build metadata
        metadata = {
            "hukuk_dali": final_state.get("hukuk_dali", []),
            "collections": final_state.get("collections", []),
            "documents_retrieved": len(final_state.get("retrieved_documents", [])),
            "plan_steps": len(final_state.get("plan", [])),
            "errors": final_state.get("errors", [])
        }
        
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
        
        return QueryResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata
        )
        
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
