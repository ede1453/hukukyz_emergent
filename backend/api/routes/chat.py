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
    """Process chat query
    
    This is a simplified implementation for Phase 1.
    Full agent workflow will be implemented in Phase 2.
    """
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        # Create initial state
        state = create_initial_state(
            query=request.query,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Step 1: Meta-Controller analysis
        routing_info = await meta_controller.analyze(state)
        state.update(routing_info)
        
        logger.info(f"Routing info: {routing_info}")
        
        # Step 2: Simple search (placeholder for full RAG pipeline)
        collections = routing_info.get("collections", [])
        
        if not collections:
            collections = ["ticaret_hukuku"]  # Default
        
        # For now, return a placeholder response
        # Full implementation will use agent workflow
        answer = f"""[Phase 1 Placeholder Response]

Sorgunuz analiz edildi:
- Hukuk Dalı: {', '.join(routing_info.get('hukuk_dali', []))}
- Koleksiyonlar: {', '.join(collections)}

Tam yanıt için agent sisteminin tamamlanması bekleniyor (Phase 2).

Şu an aktif:
✅ Meta-Controller (Task Routing)
✅ MCP Servers (Legal Documents, Document Processor, Web Search)
✅ MongoDB & Qdrant bağlantıları

Geliştirilmekte:
🔄 Full agent workflow
🔄 RAG pipeline
🔄 Multi-hop reasoning
"""
        
        # Save conversation to MongoDB
        conversations = get_conversations_collection()
        await conversations.insert_one({
            "session_id": request.session_id,
            "user_id": request.user_id,
            "query": request.query,
            "answer": answer,
            "metadata": routing_info,
            "timestamp": datetime.utcnow()
        })
        
        return QueryResponse(
            answer=answer,
            citations=[],
            confidence=0.8,
            reasoning=routing_info.get("reasoning", ""),
            metadata=routing_info
        )
        
    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
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
