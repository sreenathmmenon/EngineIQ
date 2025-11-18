"""
EngineIQ Agent Graph

LangGraph orchestration connecting all nodes with conditional edges
and human-in-the-loop checkpoints.
"""

import logging
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import AgentState
from .nodes import AgentNodes

logger = logging.getLogger(__name__)


def create_agent_graph(
    gemini_service,
    qdrant_service,
    anthropic_api_key: str = None,
    enable_checkpoints: bool = True
) -> StateGraph:
    """
    Create the EngineIQ agent graph with all nodes and edges.
    
    Graph Flow:
    1. query_understanding → Extract intent, entities, keywords
    2. embedding_generation → Generate query embedding
    3. hybrid_search → Search knowledge_base
    4. permission_filter → Filter by permissions [CHECKPOINT]
       - If sensitive → wait for approval
       - If approved → continue
       - If rejected → end
    5. rerank_results → Re-rank by relevance
    6. response_synthesis → Generate response with Claude
    7. feedback_learning → Save conversation
    8. knowledge_gap_detection → Check for gaps [CHECKPOINT]
       - If gap → wait for approval
       - Continue regardless
    
    Args:
        gemini_service: GeminiService instance
        qdrant_service: QdrantService instance
        anthropic_api_key: Claude API key
        enable_checkpoints: Enable state persistence for human-in-loop
    
    Returns:
        Compiled StateGraph ready for execution
    """
    
    # Initialize nodes
    nodes = AgentNodes(
        gemini_service=gemini_service,
        qdrant_service=qdrant_service,
        anthropic_api_key=anthropic_api_key
    )
    
    # Create graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("query_understanding", nodes.query_understanding)
    workflow.add_node("embedding_generation", nodes.embedding_generation)
    workflow.add_node("hybrid_search", nodes.hybrid_search)
    workflow.add_node("permission_filter", nodes.permission_filter)
    workflow.add_node("rerank_results", nodes.rerank_results)
    workflow.add_node("response_synthesis", nodes.response_synthesis)
    workflow.add_node("feedback_learning", nodes.feedback_learning)
    workflow.add_node("knowledge_gap_detection", nodes.knowledge_gap_detection)
    
    # Add special nodes for human approval
    workflow.add_node("wait_for_approval", wait_for_approval)
    workflow.add_node("wait_for_gap_approval", wait_for_gap_approval)
    workflow.add_node("approval_rejected", approval_rejected)
    
    # Set entry point
    workflow.set_entry_point("query_understanding")
    
    # Add sequential edges
    workflow.add_edge("query_understanding", "embedding_generation")
    workflow.add_edge("embedding_generation", "hybrid_search")
    workflow.add_edge("hybrid_search", "permission_filter")
    
    # Conditional edge after permission_filter
    workflow.add_conditional_edges(
        "permission_filter",
        route_after_permission_filter,
        {
            "wait_approval": "wait_for_approval",
            "continue": "rerank_results",
        }
    )
    
    # Conditional edge after approval wait
    workflow.add_conditional_edges(
        "wait_for_approval",
        route_after_approval,
        {
            "approved": "rerank_results",
            "rejected": "approval_rejected",
            "pending": "wait_for_approval",  # Loop back if still pending
        }
    )
    
    # After approval rejected, end
    workflow.add_edge("approval_rejected", END)
    
    # Continue after re-ranking
    workflow.add_edge("rerank_results", "response_synthesis")
    workflow.add_edge("response_synthesis", "feedback_learning")
    workflow.add_edge("feedback_learning", "knowledge_gap_detection")
    
    # Conditional edge after knowledge gap detection
    workflow.add_conditional_edges(
        "knowledge_gap_detection",
        route_after_gap_detection,
        {
            "wait_gap_approval": "wait_for_gap_approval",
            "end": END,
        }
    )
    
    # After gap approval, end (gap handling is async)
    workflow.add_edge("wait_for_gap_approval", END)
    
    # Compile graph
    if enable_checkpoints:
        # Use memory saver for checkpointing (enables human-in-loop)
        memory = MemorySaver()
        graph = workflow.compile(checkpointer=memory)
    else:
        graph = workflow.compile()
    
    logger.info("✓ Agent graph compiled successfully")
    
    return graph


# ==================== ROUTING FUNCTIONS ====================

def route_after_permission_filter(
    state: AgentState
) -> Literal["wait_approval", "continue"]:
    """
    Route after permission filtering.
    
    If sensitive content requires approval, pause and wait.
    Otherwise, continue to re-ranking.
    """
    if state.get('approval_required', False):
        if state.get('approval_status') == 'pending':
            logger.info("→ Routing to wait_for_approval")
            return "wait_approval"
    
    logger.info("→ Routing to continue (rerank_results)")
    return "continue"


def route_after_approval(
    state: AgentState
) -> Literal["approved", "rejected", "pending"]:
    """
    Route after approval wait.
    
    Check approval status and route accordingly.
    """
    status = state.get('approval_status', 'pending')
    
    if status == 'approved':
        logger.info("→ Approval granted, continuing")
        return "approved"
    elif status == 'rejected':
        logger.info("→ Approval rejected, ending")
        return "rejected"
    else:
        logger.info("→ Still pending, waiting")
        return "pending"


def route_after_gap_detection(
    state: AgentState
) -> Literal["wait_gap_approval", "end"]:
    """
    Route after knowledge gap detection.
    
    If gap detected and approval needed, wait.
    Otherwise, end the execution.
    """
    if state.get('gap_approval_required', False):
        if state.get('gap_approval_status') == 'pending':
            logger.info("→ Routing to wait_for_gap_approval")
            return "wait_gap_approval"
    
    logger.info("→ Routing to end")
    return "end"


# ==================== SPECIAL NODES ====================

def wait_for_approval(state: AgentState) -> AgentState:
    """
    Special node: Wait for human approval of sensitive content.
    
    This node pauses execution until approval_status changes
    from 'pending' to 'approved' or 'rejected'.
    
    In production, this would:
    1. Send notification to approver
    2. Create approval UI
    3. Wait for response
    4. Update state when approved/rejected
    """
    logger.info("⏸️  PAUSED: Waiting for human approval of sensitive content")
    
    state['current_node'] = 'wait_for_approval'
    state['execution_path'].append('wait_for_approval')
    
    # In a real system, this would trigger an async approval workflow
    # For now, we just log and return the state
    # The approval status would be updated externally
    
    sensitive_count = len(state.get('sensitive_results', []))
    logger.warning(f"⏸️  {sensitive_count} sensitive results awaiting approval")
    logger.warning(f"⏸️  Reason: {state.get('approval_reason')}")
    logger.warning(f"⏸️  User: {state['user_id']}")
    
    return state


def wait_for_gap_approval(state: AgentState) -> AgentState:
    """
    Special node: Wait for human approval of knowledge gap suggestion.
    
    This node pauses execution until gap_approval_status changes.
    
    In production, this would:
    1. Send notification to knowledge manager
    2. Present gap suggestion with context
    3. Wait for approval to create documentation
    4. Assign to expert if approved
    """
    logger.info("⏸️  PAUSED: Waiting for knowledge gap approval")
    
    state['current_node'] = 'wait_for_gap_approval'
    state['execution_path'].append('wait_for_gap_approval')
    
    gap = state.get('gap_suggestion', {})
    logger.warning(f"⏸️  Knowledge gap detected: {state.get('gap_reason')}")
    logger.warning(f"⏸️  Topic: {gap.get('topic')}")
    logger.warning(f"⏸️  Priority: {gap.get('priority')}")
    logger.warning(f"⏸️  Suggested action: {gap.get('suggested_action')}")
    
    return state


def approval_rejected(state: AgentState) -> AgentState:
    """
    Special node: Handle approval rejection.
    
    When sensitive content access is rejected, provide
    appropriate message to user.
    """
    logger.info("❌ Approval rejected")
    
    state['current_node'] = 'approval_rejected'
    state['execution_path'].append('approval_rejected')
    
    state['response'] = (
        "Access to some results was denied due to permissions. "
        "Please contact your administrator if you believe you should have access."
    )
    state['final_results'] = []
    state['final_count'] = 0
    state['citations'] = []
    
    return state


# ==================== HELPER FUNCTIONS ====================

def execute_query(
    graph,
    query: str,
    user_id: str,
    user_teams: list = None,
    user_location: str = "US",
    user_type: str = "employee",
    thread_id: str = None
) -> Dict[str, Any]:
    """
    Execute a query through the agent graph.
    
    Args:
        graph: Compiled LangGraph
        query: User's search query
        user_id: User identifier
        user_teams: User's teams
        user_location: User location
        user_type: User type
        thread_id: Thread ID for checkpoint continuation
    
    Returns:
        Final state after execution
    """
    from .state import create_initial_state
    
    # Create initial state
    initial_state = create_initial_state(
        query=query,
        user_id=user_id,
        user_teams=user_teams or [],
        user_location=user_location,
        user_type=user_type
    )
    
    # Execute graph
    config = {"configurable": {"thread_id": thread_id}} if thread_id else {}
    
    try:
        # Run graph
        final_state = graph.invoke(initial_state, config=config)
        return final_state
    
    except Exception as e:
        logger.error(f"Graph execution failed: {e}")
        initial_state['errors'].append(f"graph_execution: {str(e)}")
        initial_state['response'] = "An error occurred processing your query."
        return initial_state


def resume_after_approval(
    graph,
    thread_id: str,
    approval_status: str,
    approver_id: str
) -> Dict[str, Any]:
    """
    Resume execution after human approval.
    
    Args:
        graph: Compiled LangGraph with checkpointer
        thread_id: Thread ID to resume
        approval_status: 'approved' or 'rejected'
        approver_id: Who approved/rejected
    
    Returns:
        Updated final state
    """
    import time
    
    # Get current state
    config = {"configurable": {"thread_id": thread_id}}
    current_state = graph.get_state(config)
    
    if not current_state:
        raise ValueError(f"No state found for thread_id: {thread_id}")
    
    # Update approval status
    state = current_state.values
    state['approval_status'] = approval_status
    state['approver_id'] = approver_id
    state['approval_timestamp'] = int(time.time())
    
    # Resume execution
    final_state = graph.invoke(state, config=config)
    
    return final_state


def resume_after_gap_approval(
    graph,
    thread_id: str,
    gap_approval_status: str,
    approver_id: str
) -> Dict[str, Any]:
    """
    Resume execution after knowledge gap approval.
    
    Args:
        graph: Compiled LangGraph with checkpointer
        thread_id: Thread ID to resume
        gap_approval_status: 'approved' or 'rejected'
        approver_id: Who approved/rejected
    
    Returns:
        Updated final state
    """
    import time
    
    # Get current state
    config = {"configurable": {"thread_id": thread_id}}
    current_state = graph.get_state(config)
    
    if not current_state:
        raise ValueError(f"No state found for thread_id: {thread_id}")
    
    # Update gap approval status
    state = current_state.values
    state['gap_approval_status'] = gap_approval_status
    state['approver_id'] = approver_id
    
    # Resume execution
    final_state = graph.invoke(state, config=config)
    
    return final_state
