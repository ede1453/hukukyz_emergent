"""Agent state definitions for LangGraph"""

from typing import List, Dict, Optional, Annotated
from typing_extensions import TypedDict
from datetime import datetime
import operator


class AgentState(TypedDict):
    """Main state for HukukYZ agent workflow"""
    
    # ========== Input ==========
    query: str  # Original user query
    user_id: str  # User identifier
    session_id: str  # Session identifier
    
    # ========== Planning ==========
    plan: List[Dict]  # List of planned steps
    # Each step: {"step": int, "action": str, "tool": str, "params": dict}
    current_step_index: int  # Current step being executed
    
    # ========== Execution ==========
    history: Annotated[List[Dict], operator.add]  # Past step results
    # Each history item: {"step": int, "action": str, "result": any, "timestamp": str}
    current_findings: str  # Current step findings
    
    # ========== Context ==========
    hukuk_dali: List[str]  # Legal domains: ["ticaret", "borclar", ...]
    kaynak_tipi: List[str]  # Source types: ["kanun", "ictihat", ...]
    madde_refs: List[str]  # Article references: ["TTK m.11", "TBK m.1", ...]
    
    # ========== Retrieved Documents ==========
    retrieved_documents: Annotated[List[Dict], operator.add]  # All retrieved docs
    # Each doc: {"content": str, "metadata": dict, "score": float, "source": str}
    
    # ========== Control Flow ==========
    is_ambiguous: bool  # Query clarity flag
    needs_clarification: bool  # Requires user input
    clarification_question: Optional[str]  # Question to ask user
    should_continue: bool  # Continue to next step or finish
    
    # ========== Quality Control ==========
    verification_passed: bool  # Auditor verification result
    verification_feedback: Optional[str]  # Auditor feedback
    replan_count: int  # Number of replanning attempts
    
    # ========== Output ==========
    final_answer: str  # Synthesized final answer
    citations: List[Dict]  # Citations with sources
    # Each citation: {"source": str, "text": str, "relevance": float, "url": str}
    confidence: float  # Answer confidence score (0-1)
    reasoning: str  # Reasoning process summary
    
    # ========== Metadata ==========
    created_at: str  # Timestamp
    total_tokens: int  # Total tokens used
    agent_iterations: int  # Number of agent iterations
    errors: Annotated[List[str], operator.add]  # Error messages


class Step(TypedDict):
    """Individual step in the plan"""
    step: int
    action: str  # Action description
    tool: str  # Tool to use: "researcher", "web_scout", "analyst", etc.
    params: Dict  # Parameters for the tool
    justification: str  # Why this step is needed


class Citation(TypedDict):
    """Citation structure"""
    source: str  # e.g., "TTK m.11", "Yargıtay 11. HD, 2023/1234"
    text: str  # Cited text excerpt
    relevance: float  # Relevance score (0-1)
    url: Optional[str]  # URL if available
    doc_type: str  # "kanun", "ictihat", "akademik", etc.


class Document(TypedDict):
    """Retrieved document structure"""
    id: str
    content: str
    metadata: Dict
    score: float
    source: str  # Collection name


class VerificationResult(TypedDict):
    """Auditor verification result"""
    passed: bool
    faithfulness_score: float  # 0-1
    relevance_score: float  # 0-1
    consistency_score: float  # 0-1
    feedback: str
    issues: List[str]


# Helper function to create initial state
def create_initial_state(
    query: str,
    user_id: str,
    session_id: str
) -> AgentState:
    """Create initial agent state"""
    return AgentState(
        # Input
        query=query,
        user_id=user_id,
        session_id=session_id,
        
        # Planning
        plan=[],
        current_step_index=0,
        
        # Execution
        history=[],
        current_findings="",
        
        # Context
        hukuk_dali=[],
        kaynak_tipi=[],
        madde_refs=[],
        
        # Retrieved
        retrieved_documents=[],
        
        # Control
        is_ambiguous=False,
        needs_clarification=False,
        clarification_question=None,
        should_continue=True,
        
        # Quality
        verification_passed=True,
        verification_feedback=None,
        replan_count=0,
        
        # Output
        final_answer="",
        citations=[],
        confidence=0.0,
        reasoning="",
        
        # Metadata
        created_at=datetime.utcnow().isoformat(),
        total_tokens=0,
        agent_iterations=0,
        errors=[]
    )
