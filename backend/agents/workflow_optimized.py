"""Optimized LangGraph workflow for HukukYZ agent system

Improvements:
- Conditional analyst execution (only for complex queries)
- Performance tracking for each agent
- Better error handling
- Configurable workflow paths
"""

from typing import Dict, Literal
import logging
import time
from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState, create_initial_state
from backend.agents.meta_controller import meta_controller
from backend.agents.planner import planner_agent
from backend.agents.researcher import researcher_agent
from backend.agents.analyst import analyst_agent
from backend.agents.auditor import auditor_agent
from backend.agents.synthesizer import synthesizer_agent

logger = logging.getLogger(__name__)


# ========== Performance Tracking ==========

def track_performance(func):
    """Decorator to track agent performance"""
    async def wrapper(state: AgentState):
        start_time = time.time()
        try:
            result = await func(state)
            elapsed = time.time() - start_time
            
            # Add timing to state
            timings = state.get("agent_timings", {})
            timings[func.__name__] = round(elapsed, 2)
            result["agent_timings"] = timings
            
            logger.info(f"{func.__name__} completed in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"{func.__name__} failed after {elapsed:.2f}s: {e}")
            raise
    return wrapper


# ========== Node Functions ==========

@track_performance
async def meta_controller_node(state: AgentState) -> Dict:
    """Meta-Controller: Route query to appropriate collections"""
    logger.info("[Node] Meta-Controller")
    routing = await meta_controller.analyze(state)
    return routing


@track_performance
async def planner_node(state: AgentState) -> Dict:
    """Planner: Create multi-step plan"""
    logger.info("[Node] Planner")
    plan_info = await planner_agent.create_plan(state)
    return plan_info


@track_performance
async def researcher_node(state: AgentState) -> Dict:
    """Researcher: Execute document retrieval"""
    logger.info("[Node] Researcher")
    
    query = state["query"]
    collections = state.get("collections", [])
    
    # Use plan if available
    plan = state.get("plan", [])
    current_step_index = state.get("current_step_index", 0)
    
    if plan and current_step_index < len(plan):
        current_step = plan[current_step_index]
        if current_step["tool"] == "researcher":
            params = current_step.get("params", {})
            query = params.get("query", query)
            collections = [params.get("collection")] if "collection" in params else collections
    
    # Execute research with deprecated flag from state
    include_deprecated = state.get("include_deprecated", False)
    documents = await researcher_agent.research(
        query=query,
        collections=collections,
        include_deprecated=include_deprecated
    )
    
    return {
        "retrieved_documents": documents
    }


@track_performance
async def analyst_node(state: AgentState) -> Dict:
    """Analyst: Analyze and cross-reference documents (conditional)"""
    logger.info("[Node] Analyst")
    
    documents = state.get("retrieved_documents", [])
    
    # Perform legal analysis
    analysis = await analyst_agent.analyze(
        documents=documents,
        analysis_type="comprehensive"
    )
    
    return {
        "analysis_results": analysis
    }


@track_performance
async def synthesizer_node(state: AgentState) -> Dict:
    """Synthesizer: Generate final answer"""
    logger.info("[Node] Synthesizer")
    
    query = state["query"]
    documents = state.get("retrieved_documents", [])
    analysis = state.get("analysis_results", {})
    
    # Synthesize answer (with analysis if available)
    synthesis = await synthesizer_agent.synthesize(
        query=query,
        documents=documents,
        analysis=analysis if analysis else None
    )
    
    return synthesis


@track_performance
async def auditor_node(state: AgentState) -> Dict:
    """Auditor: Quality control on answer"""
    logger.info("[Node] Auditor")
    
    query = state["query"]
    answer = state.get("answer", "")
    sources = state.get("retrieved_documents", [])
    
    # Audit the answer
    audit = await auditor_agent.audit(
        query=query,
        answer=answer,
        sources=sources
    )
    
    # Update confidence based on audit
    if audit.get("should_improve", False):
        logger.warning(f"Auditor suggests improvements: {audit.get('issues', [])}")
    
    return {
        "audit_results": audit,
        "confidence": audit.get("final_score", state.get("confidence", 0.5))
    }


# ========== Router Functions ==========

def should_analyze(state: AgentState) -> Literal["analyst", "synthesizer"]:
    """Decide if analyst should be used
    
    Analyst is used when:
    - Many documents retrieved (>5)
    - Query is complex (contains multiple keywords)
    - Multiple collections involved
    """
    documents = state.get("retrieved_documents", [])
    collections = state.get("collections", [])
    query = state.get("query", "")
    
    # Use analyst for complex scenarios
    use_analyst = (
        len(documents) > 5 or
        len(collections) > 1 or
        len(query.split()) > 10
    )
    
    if use_analyst:
        logger.info("✅ Using Analyst (complex query)")
        return "analyst"
    else:
        logger.info("⏭️  Skipping Analyst (simple query)")
        return "synthesizer"


def should_continue(state: AgentState) -> Literal["synthesizer", "end"]:
    """Decide if workflow should continue or end"""
    documents = state.get("retrieved_documents", [])
    
    if documents:
        return "synthesizer"
    else:
        return "end"


# ========== Build Optimized Workflow ==========

def create_workflow():
    """Create optimized LangGraph workflow"""
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("meta_controller", meta_controller_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("auditor", auditor_node)
    
    # Add edges - Optimized workflow with conditional analyst
    workflow.set_entry_point("meta_controller")
    workflow.add_edge("meta_controller", "planner")
    workflow.add_edge("planner", "researcher")
    
    # Conditional: Use analyst only for complex queries
    workflow.add_conditional_edges(
        "researcher",
        should_analyze,
        {
            "analyst": "analyst",
            "synthesizer": "synthesizer"
        }
    )
    
    workflow.add_edge("analyst", "synthesizer")
    workflow.add_edge("synthesizer", "auditor")
    workflow.add_edge("auditor", END)
    
    # Compile
    app = workflow.compile()
    
    logger.info("✅ Optimized workflow compiled successfully")
    return app


# ========== Workflow Execution ==========

async def execute_workflow(
    query: str,
    user_id: str,
    session_id: str,
    include_deprecated: bool = False
) -> Dict:
    """Execute optimized agent workflow
    
    Args:
        query: User query
        user_id: User identifier
        session_id: Session identifier
        include_deprecated: Include deprecated document versions
    
    Returns:
        Final state with answer and performance metrics
    """
    try:
        workflow_start = time.time()
        logger.info(f"🚀 Executing optimized workflow for query: {query[:100]}...")
        
        # Create initial state
        initial_state = create_initial_state(
            query=query,
            user_id=user_id,
            session_id=session_id,
            include_deprecated=include_deprecated
        )
        
        # Create and run workflow
        app = create_workflow()
        final_state = await app.ainvoke(initial_state)
        
        workflow_elapsed = time.time() - workflow_start
        logger.info(f"✅ Workflow completed in {workflow_elapsed:.2f}s")
        
        # Add total workflow time
        final_state["total_workflow_time"] = round(workflow_elapsed, 2)
        
        # Log performance metrics
        timings = final_state.get("agent_timings", {})
        logger.info(f"📊 Agent timings: {timings}")
        
        return final_state
        
    except Exception as e:
        logger.error(f"❌ Workflow execution failed: {e}", exc_info=True)
        
        # Return error state
        return {
            "query": query,
            "answer": "Üzgünüm, sorgunuzu işlerken bir hata oluştu. Lütfen tekrar deneyin.",
            "confidence": 0.0,
            "citations": [],
            "errors": [str(e)]
        }
