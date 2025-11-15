"""Chat API routes"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import logging

from backend.agents.state import create_initial_state, AgentState
from backend.agents.workflow_optimized import execute_workflow
from backend.mcp.client.mcp_client import mcp_client
from backend.database.mongodb import get_conversations_collection
from backend.api.routes.auth import get_current_user
from backend.api.routes.credits import deduct_credits, calculate_token_cost, get_user_credits
from backend.middleware.rate_limiter import check_rate_limit

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = "default"
    user_id: Optional[str] = None
    include_deprecated: Optional[bool] = False


class QueryResponse(BaseModel):
    answer: str
    citations: List[str] = []
    confidence: float = 0.0
    metadata: dict = {}


class HealthResponse(BaseModel):
    status: str
    database: dict
    qdrant: dict
    endpoints: dict


@router.post("/query", response_model=QueryResponse)
async def chat_query(request: QueryRequest, current_user: dict = Depends(get_current_user)):
    """Process chat query using full agent workflow with caching and credits"""
    import time
    start_time = time.time()
    
    try:
        logger.info(f"Received query from {current_user['email']}: {request.query[:100]}...")
        
        # Admin users have unlimited credits, skip credit check
        is_admin = current_user.get("role") == "admin"
        
        # Check rate limiting
        await check_rate_limit(None, current_user["email"], current_user.get("role", "avukat"))
        
        if not is_admin:
            # Check credit balance before processing (only for non-admin users)
            current_balance = await get_user_credits(current_user["email"])
            MIN_REQUIRED_CREDITS = 0.01  # Minimum credits to process query
            
            if current_balance < MIN_REQUIRED_CREDITS:
                raise HTTPException(
                    status_code=402,
                    detail=f"Yetersiz kredi. Mevcut bakiye: {current_balance:.2f}. Lütfen kredi yükleyin."
                )
        
        # Create initial state
        initial_state = create_initial_state(
            query=request.query,
            session_id=request.session_id,
            user_id=current_user["email"],
            include_deprecated=request.include_deprecated
        )
        
        # Execute workflow
        final_state = await optimized_workflow.ainvoke(initial_state)
        
        # Extract response fields
        answer = final_state.get("final_answer", "Cevap oluşturulamadı")
        citations = final_state.get("citations", [])
        confidence = final_state.get("confidence", 0.0)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Build metadata (include performance metrics if available)
        metadata = {
            "hukuk_dali": final_state.get("hukuk_dali", []),
            "collections": final_state.get("collections", []),
            "documents_retrieved": len(final_state.get("retrieved_documents", [])),
            "plan_steps": len(final_state.get("plan", [])),
            "errors": final_state.get("errors", []),
            "response_time_seconds": round(response_time, 2)
        }
        
        # Add performance metrics if using optimized workflow
        if "agent_timings" in final_state:
            metadata["agent_timings"] = final_state["agent_timings"]
            metadata["total_workflow_time"] = final_state.get("total_workflow_time", 0)
        
        # Calculate token usage and cost - IMPROVED ESTIMATION
        # More accurate token estimation
        estimated_input_tokens = len(request.query.split()) * 1.5  # Words to tokens ratio
        estimated_output_tokens = len(answer.split()) * 1.5
        
        # Add context tokens (retrieved documents)
        context_length = sum(len(doc.get("text", "").split()) for doc in final_state.get("retrieved_documents", []))
        estimated_input_tokens += context_length * 1.3
        
        credit_cost = 0.0
        
        # Only deduct credits for non-admin users
        if not is_admin:
            credit_cost = calculate_token_cost(
                int(estimated_input_tokens),
                int(estimated_output_tokens)
            )
            
            # Deduct credits
            try:
                await deduct_credits(
                    current_user["email"],
                    credit_cost,
                    "Chat query",
                    {
                        "query": request.query[:100],
                        "input_tokens": int(estimated_input_tokens),
                        "output_tokens": int(estimated_output_tokens),
                        "session_id": request.session_id
                    }
                )
                logger.info(f"Deducted {credit_cost:.4f} credits from {current_user['email']}")
            except HTTPException as credit_error:
                # If deduction fails mid-query, log it but don't fail the response
                logger.error(f"Credit deduction failed: {credit_error.detail}")
        else:
            logger.info(f"Admin user {current_user['email']} - unlimited credits")
        
        # Add credit info to metadata
        metadata["credits_used"] = credit_cost
        metadata["is_admin"] = is_admin
        metadata["input_tokens"] = int(estimated_input_tokens)
        metadata["output_tokens"] = int(estimated_output_tokens)
        if not is_admin:
            metadata["remaining_balance"] = await get_user_credits(current_user["email"])
        else:
            metadata["remaining_balance"] = "unlimited"
        
        # Save conversation to MongoDB
        conversations = get_conversations_collection()
        await conversations.insert_one({
            "session_id": request.session_id,
            "user_id": current_user["email"],
            "user_role": current_user.get("role", "avukat"),
            "query": request.query,
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
            "metadata": metadata,
            "credits_used": credit_cost,
            "response_time": response_time,
            "timestamp": datetime.utcnow()
        })
        
        logger.info(f"Query processed successfully. Time: {response_time:.2f}s, Confidence: {confidence:.2f}, Credits: {credit_cost:.4f}")
        
        return QueryResponse(
            answer=answer,
            citations=citations,
            confidence=confidence,
            metadata=metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/rate-limit-status")
async def get_rate_limit_status(current_user: dict = Depends(get_current_user)):
    """Get current rate limit status"""
    from backend.middleware.rate_limiter import rate_limiter
    
    info = await rate_limiter.get_rate_limit_info(
        current_user["email"],
        current_user.get("role", "avukat")
    )
    
    return {
        "success": True,
        "user": current_user["email"],
        "role": current_user.get("role", "avukat"),
        "rate_limit": info
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    from backend.database.mongodb import mongodb_client
    from backend.database.qdrant_client import qdrant_manager
    
    db_status = "unknown"
    try:
        await mongodb_client.db.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    qdrant_status = "unknown"
    try:
        qdrant_manager.client.get_collections()
        qdrant_status = "connected"
    except Exception as e:
        qdrant_status = f"error: {str(e)}"
    
    return HealthResponse(
        status="healthy",
        database={"status": db_status},
        qdrant={"status": qdrant_status},
        endpoints={
            "query": "/query",
            "sessions": "/sessions",
            "history": "/history/{session_id}",
            "health": "/health"
        }
    )


@router.get("/sessions")
async def get_user_sessions(current_user: dict = Depends(get_current_user), limit: int = 50):
    """Get all chat sessions for current user"""
    try:
        conversations = get_conversations_collection()
        
        # Get unique sessions with latest message for CURRENT USER ONLY
        pipeline = [
            {"$match": {"user_id": current_user["email"]}},  # IMPORTANT: Filter by user
            {"$sort": {"timestamp": -1}},
            {"$group": {
                "_id": "$session_id",
                "last_message": {"$first": "$$ROOT"},
                "message_count": {"$sum": 1}
            }},
            {"$sort": {"last_message.timestamp": -1}},
            {"$limit": limit}
        ]
        
        sessions = await conversations.aggregate(pipeline).to_list(limit)
        
        # Format response
        formatted_sessions = []
        for session in sessions:
            msg = session["last_message"]
            formatted_sessions.append({
                "session_id": session["_id"],
                "last_query": msg.get("query", "")[:100],
                "last_timestamp": msg.get("timestamp"),
                "message_count": session["message_count"],
                "total_credits_used": 0
            })
        
        return {
            "success": True,
            "sessions": formatted_sessions,
            "total": len(formatted_sessions)
        }
        
    except Exception as e:
        logger.error(f"Get sessions error: {e}")
        raise HTTPException(status_code=500, detail="Oturum geçmişi alınamadı")


@router.get("/history/{session_id}")
async def get_chat_history(session_id: str, current_user: dict = Depends(get_current_user), limit: int = 50):
    """Get conversation history for a session"""
    try:
        conversations = get_conversations_collection()
        
        # Verify user owns this session
        first_msg = await conversations.find_one(
            {"session_id": session_id},
            {"_id": 0, "user_id": 1}
        )
        
        if not first_msg or first_msg.get("user_id") != current_user["email"]:
            raise HTTPException(status_code=403, detail="Bu oturuma erişim yetkiniz yok")
        
        # Retrieve conversation history
        history = await conversations.find(
            {"session_id": session_id},
            {"_id": 0}
        ).sort("timestamp", 1).limit(limit).to_list(limit)
        
        return {
            "success": True,
            "session_id": session_id,
            "history": history,
            "count": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Geçmiş alınamadı")


@router.delete("/history/{session_id}")
async def delete_chat_history(session_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a chat session"""
    try:
        conversations = get_conversations_collection()
        
        # Delete only if user owns it
        result = await conversations.delete_many({
            "session_id": session_id,
            "user_id": current_user["email"]
        })
        
        return {
            "success": True,
            "deleted_count": result.deleted_count
        }
        
    except Exception as e:
        logger.error(f"Delete history error: {e}")
        raise HTTPException(status_code=500, detail="Geçmiş silinemedi")
