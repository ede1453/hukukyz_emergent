"""LangGraph workflow for HukukYZ agent system"""

from typing import Dict, Literal
import logging
from langgraph.graph import StateGraph, END

from backend.agents.state import AgentState, create_initial_state
from backend.agents.meta_controller import meta_controller
from backend.agents.planner import planner_agent
from backend.agents.researcher import researcher_agent
from backend.agents.analyst import analyst_agent
from backend.agents.auditor import auditor_agent
from backend.agents.synthesizer import synthesizer_agent

logger = logging.getLogger(__name__)


# ========== Node Functions ==========

async def meta_controller_node(state: AgentState) -> Dict:
    """Meta-Controller: Route query to appropriate collections"""
    logger.info("[Node] Meta-Controller")
    routing = await meta_controller.analyze(state)
    return routing


async def planner_node(state: AgentState) -> Dict:
    """Planner: Create multi-step plan"""
    logger.info("[Node] Planner")
    plan_info = await planner_agent.create_plan(state)
    return plan_info


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
    
    # Execute research
    documents = await researcher_agent.research(
        query=query,
        collections=collections
    )
    
    return {
        "retrieved_documents": documents
    }


async def synthesizer_node(state: AgentState) -> Dict:
    """Synthesizer: Generate final answer"""
    logger.info("[Node] Synthesizer")
    
    query = state["query"]
    documents = state.get("retrieved_documents", [])
    
    # Synthesize answer
    synthesis = await synthesizer_agent.synthesize(
        query=query,
        documents=documents
    )
    
    return synthesis


# ========== Router Functions ==========

def should_continue(state: AgentState) -> Literal["synthesize", "end"]:
    """Decide if workflow should continue or end"""
    # Check if we have documents
    documents = state.get("retrieved_documents", [])
    
    if documents:
        return "synthesize"
    else:
        return "end"


# ========== Build Workflow ==========

def create_workflow():
    """Create LangGraph workflow"""
    
    # Create state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("meta_controller", meta_controller_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    # Add edges
    workflow.set_entry_point("meta_controller")
    workflow.add_edge("meta_controller", "planner")
    workflow.add_edge("planner", "researcher")
    
    # Conditional edge after researcher
    workflow.add_conditional_edges(
        "researcher",
        should_continue,
        {
            "synthesize": "synthesizer",
            "end": END
        }
    )
    
    # End after synthesizer
    workflow.add_edge("synthesizer", END)
    
    # Compile
    app = workflow.compile()
    
    logger.info("Workflow compiled successfully")
    return app


# ========== Workflow Execution ==========

async def execute_workflow(
    query: str,
    user_id: str,
    session_id: str
) -> Dict:
    """Execute complete agent workflow
    
    Args:
        query: User query
        user_id: User identifier
        session_id: Session identifier
    
    Returns:
        Final state with answer
    """
    try:
        logger.info(f"Executing workflow for query: {query[:100]}...")
        
        # Create initial state
        initial_state = create_initial_state(
            query=query,
            user_id=user_id,
            session_id=session_id
        )
        
        # Create and run workflow
        app = create_workflow()
        final_state = await app.ainvoke(initial_state)
        
        logger.info("Workflow execution completed")
        return final_state
        
    except Exception as e:
        logger.error(f"Workflow execution error: {e}", exc_info=True)
        
        # Return error state
        return {
            "final_answer": f"Bir hata oluştu: {str(e)}",
            "citations": [],
            "confidence": 0.0,
            "errors": [str(e)]
        }


# Global workflow app
workflow_app = None


def get_workflow_app():
    """Get or create workflow app (singleton)"""
    global workflow_app
    if workflow_app is None:
        workflow_app = create_workflow()
    return workflow_app
