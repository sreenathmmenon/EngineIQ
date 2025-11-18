"""
EngineIQ Agent State Definition

Defines the state structure for LangGraph agent execution.
"""

from typing import List, Dict, Optional, Any, TypedDict
from datetime import datetime


class AgentState(TypedDict):
    """
    State structure for EngineIQ agent graph.
    
    This state flows through all nodes in the LangGraph execution.
    Each node reads from and writes to this state.
    """
    
    # === INPUT ===
    query: str
    """User's search query (raw text)"""
    
    user_id: str
    """User identifier for permission checking"""
    
    user_teams: List[str]
    """Teams the user belongs to (for permission filtering)"""
    
    user_location: Optional[str]
    """User location (e.g., 'US', 'offshore') for offshore restrictions"""
    
    user_type: Optional[str]
    """User type (e.g., 'employee', 'contractor', 'third_party')"""
    
    # === QUERY UNDERSTANDING ===
    intent: Optional[str]
    """Query intent: search|question|command|clarification"""
    
    entities: Optional[List[str]]
    """Extracted entities and concepts from query"""
    
    keywords: Optional[List[str]]
    """Search keywords extracted from query"""
    
    sources_needed: Optional[List[str]]
    """Data sources to search (slack|github|box|confluence|etc)"""
    
    # === EMBEDDING ===
    query_embedding: Optional[List[float]]
    """768-dimensional Gemini embedding of the query"""
    
    # === SEARCH ===
    search_results: Optional[List[Dict[str, Any]]]
    """Raw search results from Qdrant (top 100)"""
    
    search_count: int
    """Number of results returned from search"""
    
    # === PERMISSION FILTERING ===
    filtered_results: Optional[List[Dict[str, Any]]]
    """Results after permission filtering"""
    
    sensitive_results: Optional[List[Dict[str, Any]]]
    """Flagged sensitive results requiring approval"""
    
    filtered_count: int
    """Number of results after filtering"""
    
    # === HUMAN-IN-LOOP: APPROVAL ===
    approval_required: bool
    """Whether human approval is needed for sensitive content"""
    
    approval_status: Optional[str]
    """Approval status: pending|approved|rejected|not_required"""
    
    approval_reason: Optional[str]
    """Reason approval is required"""
    
    approver_id: Optional[str]
    """Who approved/rejected the request"""
    
    approval_timestamp: Optional[int]
    """When approval was granted/rejected"""
    
    # === RE-RANKING ===
    final_results: Optional[List[Dict[str, Any]]]
    """Re-ranked top results (top 20)"""
    
    final_count: int
    """Number of final results"""
    
    # === RESPONSE SYNTHESIS ===
    response: Optional[str]
    """Final synthesized response from Claude"""
    
    citations: Optional[List[Dict[str, str]]]
    """Source citations included in response"""
    
    related_queries: Optional[List[str]]
    """Suggested related queries"""
    
    # === EXPERTISE ===
    expertise_suggestions: Optional[List[Dict[str, Any]]]
    """Suggested experts to contact"""
    
    # === KNOWLEDGE GAP DETECTION ===
    knowledge_gap_detected: bool
    """Whether a knowledge gap was detected"""
    
    gap_reason: Optional[str]
    """Why the gap was detected (low result quality, repeated searches, etc)"""
    
    gap_suggestion: Optional[Dict[str, Any]]
    """Suggested action to fill the gap"""
    
    gap_approval_required: bool
    """Whether human approval needed for gap suggestion"""
    
    gap_approval_status: Optional[str]
    """Gap approval status: pending|approved|rejected|not_required"""
    
    # === FEEDBACK & LEARNING ===
    conversation_id: Optional[str]
    """Unique ID for this query session"""
    
    feedback_saved: bool
    """Whether feedback was saved to conversations collection"""
    
    # === METADATA ===
    start_timestamp: Optional[int]
    """When query processing started (unix timestamp)"""
    
    end_timestamp: Optional[int]
    """When query processing completed"""
    
    response_time_ms: Optional[int]
    """Total response time in milliseconds"""
    
    errors: Optional[List[str]]
    """Any errors encountered during processing"""
    
    current_node: Optional[str]
    """Current node being executed (for debugging)"""
    
    execution_path: Optional[List[str]]
    """Sequence of nodes executed (for debugging)"""


def create_initial_state(
    query: str,
    user_id: str,
    user_teams: List[str] = None,
    user_location: str = "US",
    user_type: str = "employee"
) -> AgentState:
    """
    Create initial state for agent execution.
    
    Args:
        query: User's search query
        user_id: User identifier
        user_teams: Teams user belongs to (default: [])
        user_location: User location (default: "US")
        user_type: User type (default: "employee")
    
    Returns:
        AgentState: Initial state with query and user info
    """
    import time
    import uuid
    
    return AgentState(
        # Input
        query=query,
        user_id=user_id,
        user_teams=user_teams or [],
        user_location=user_location,
        user_type=user_type,
        
        # Query understanding
        intent=None,
        entities=None,
        keywords=None,
        sources_needed=None,
        
        # Embedding
        query_embedding=None,
        
        # Search
        search_results=None,
        search_count=0,
        
        # Filtering
        filtered_results=None,
        sensitive_results=None,
        filtered_count=0,
        
        # Approval
        approval_required=False,
        approval_status="not_required",
        approval_reason=None,
        approver_id=None,
        approval_timestamp=None,
        
        # Re-ranking
        final_results=None,
        final_count=0,
        
        # Response
        response=None,
        citations=None,
        related_queries=None,
        
        # Expertise
        expertise_suggestions=None,
        
        # Knowledge gap
        knowledge_gap_detected=False,
        gap_reason=None,
        gap_suggestion=None,
        gap_approval_required=False,
        gap_approval_status="not_required",
        
        # Feedback
        conversation_id=str(uuid.uuid4()),
        feedback_saved=False,
        
        # Metadata
        start_timestamp=int(time.time()),
        end_timestamp=None,
        response_time_ms=None,
        errors=[],
        current_node=None,
        execution_path=[],
    )
