"""
EngineIQ Agent Nodes

Implementation of all LangGraph nodes for query processing.
"""

import logging
import time
from typing import Dict, Any, List
from anthropic import Anthropic

from .state import AgentState

logger = logging.getLogger(__name__)


class AgentNodes:
    """
    Collection of all agent nodes for LangGraph.
    
    Each node is a function that:
    1. Takes AgentState as input
    2. Processes data using services
    3. Returns updated AgentState
    """
    
    def __init__(
        self,
        gemini_service,
        qdrant_service,
        anthropic_api_key: str = None
    ):
        """
        Initialize agent nodes with required services.
        
        Args:
            gemini_service: GeminiService for embeddings and understanding
            qdrant_service: QdrantService for search and indexing
            anthropic_api_key: Claude API key for response synthesis
        """
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.anthropic_client = Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None
        
        logger.info("AgentNodes initialized")
    
    # ==================== NODE 1: QUERY UNDERSTANDING ====================
    
    def query_understanding(self, state: AgentState) -> AgentState:
        """
        Node 1: Understand user query intent and extract entities.
        
        Uses GeminiService to analyze the query and extract:
        - Intent (search, question, command, clarification)
        - Entities and concepts
        - Keywords for searching
        - Needed data sources
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with intent, entities, keywords, sources_needed
        """
        logger.info(f"NODE: query_understanding - Query: {state['query']}")
        state['current_node'] = 'query_understanding'
        state['execution_path'].append('query_understanding')
        
        try:
            query = state['query']
            
            # Use Gemini to understand query
            result = self.gemini.understand_query(query)
            
            state['intent'] = result.get('intent', 'search')
            state['entities'] = result.get('entities', [])
            state['keywords'] = result.get('keywords', query.split())
            state['sources_needed'] = result.get('data_sources', [])
            
            logger.info(f"✓ Query understood: intent={state['intent']}, entities={state['entities']}")
        
        except Exception as e:
            logger.error(f"✗ Error in query_understanding: {e}")
            state['errors'].append(f"query_understanding: {str(e)}")
            # Set defaults
            state['intent'] = 'search'
            state['entities'] = []
            state['keywords'] = state['query'].split()
            state['sources_needed'] = []
        
        return state
    
    # ==================== NODE 2: EMBEDDING GENERATION ====================
    
    def embedding_generation(self, state: AgentState) -> AgentState:
        """
        Node 2: Generate embedding for the query.
        
        Uses GeminiService to create 768-dimensional embedding
        optimized for retrieval.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with query_embedding
        """
        logger.info("NODE: embedding_generation")
        state['current_node'] = 'embedding_generation'
        state['execution_path'].append('embedding_generation')
        
        try:
            query = state['query']
            
            # Generate embedding with RETRIEVAL_QUERY task type
            embedding = self.gemini.generate_embedding(query, task_type="RETRIEVAL_QUERY")
            
            state['query_embedding'] = embedding
            
            logger.info(f"✓ Generated embedding: {len(embedding)} dimensions")
        
        except Exception as e:
            logger.error(f"✗ Error in embedding_generation: {e}")
            state['errors'].append(f"embedding_generation: {str(e)}")
            # Set empty embedding as fallback
            state['query_embedding'] = [0.0] * 768
        
        return state
    
    # ==================== NODE 3: HYBRID SEARCH ====================
    
    def hybrid_search(self, state: AgentState) -> AgentState:
        """
        Node 3: Execute hybrid search (vector + keyword).
        
        Uses QdrantService to search knowledge_base collection
        with both semantic similarity and keyword matching.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with search_results, search_count
        """
        logger.info("NODE: hybrid_search")
        state['current_node'] = 'hybrid_search'
        state['execution_path'].append('hybrid_search')
        
        try:
            embedding = state['query_embedding']
            query = state['query']
            sources = state.get('sources_needed', [])
            
            # Build filter for sources if needed
            must_conditions = None
            if sources:
                from qdrant_client.models import FieldCondition, MatchAny
                must_conditions = [
                    FieldCondition(key="source", match=MatchAny(any=sources))
                ]
            
            # Execute hybrid search
            results = self.qdrant.hybrid_search(
                collection_name="knowledge_base",
                query_vector=embedding,
                must=must_conditions,
                limit=100
            )
            
            state['search_results'] = results
            state['search_count'] = len(results)
            
            logger.info(f"✓ Found {state['search_count']} results")
        
        except Exception as e:
            logger.error(f"✗ Error in hybrid_search: {e}")
            state['errors'].append(f"hybrid_search: {str(e)}")
            state['search_results'] = []
            state['search_count'] = 0
        
        return state
    
    # ==================== NODE 4: PERMISSION FILTER [HUMAN-IN-LOOP] ====================
    
    def permission_filter(self, state: AgentState) -> AgentState:
        """
        Node 4: Filter results by user permissions.
        
        HUMAN-IN-LOOP CHECKPOINT:
        - Checks if results contain sensitive content
        - If sensitive: Sets approval_required=True and pauses
        - Filters by user teams, location, and type
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with filtered_results, sensitive_results, approval_required
        """
        logger.info("NODE: permission_filter")
        state['current_node'] = 'permission_filter'
        state['execution_path'].append('permission_filter')
        
        try:
            results = state.get('search_results', [])
            user_id = state['user_id']
            user_teams = state['user_teams']
            user_location = state.get('user_location', 'US')
            user_type = state.get('user_type', 'employee')
            
            filtered = []
            sensitive = []
            
            for result in results:
                # Handle ScoredPoint objects
                payload = result.payload if hasattr(result, 'payload') else result.get('payload', {})
                permissions = payload.get('permissions', {})
                
                # Check sensitivity level
                sensitivity = permissions.get('sensitivity', 'public')
                
                # Check offshore restrictions
                offshore_restricted = permissions.get('offshore_restricted', False)
                if offshore_restricted and user_location != 'US':
                    sensitive.append({
                        'result': result,
                        'reason': 'offshore_restricted',
                        'sensitivity': sensitivity
                    })
                    continue
                
                # Check third-party restrictions
                third_party_restricted = permissions.get('third_party_restricted', False)
                if third_party_restricted and user_type in ['contractor', 'third_party']:
                    sensitive.append({
                        'result': result,
                        'reason': 'third_party_restricted',
                        'sensitivity': sensitivity
                    })
                    continue
                
                # Check sensitivity level
                if sensitivity in ['confidential', 'restricted']:
                    # Check if user has explicit access
                    allowed_users = permissions.get('users', [])
                    allowed_teams = permissions.get('teams', [])
                    
                    has_access = (
                        user_id in allowed_users or
                        any(team in user_teams for team in allowed_teams)
                    )
                    
                    if not has_access:
                        sensitive.append({
                            'result': result,
                            'reason': 'high_sensitivity',
                            'sensitivity': sensitivity
                        })
                        continue
                
                # Passed all checks
                filtered.append(result)
            
            state['filtered_results'] = filtered
            state['sensitive_results'] = sensitive
            state['filtered_count'] = len(filtered)
            
            # Determine if approval needed
            if sensitive:
                state['approval_required'] = True
                state['approval_status'] = 'pending'
                state['approval_reason'] = f"Found {len(sensitive)} sensitive results requiring approval"
                logger.warning(f"⚠️  HUMAN-IN-LOOP: {len(sensitive)} sensitive results require approval")
            else:
                state['approval_required'] = False
                state['approval_status'] = 'not_required'
            
            logger.info(f"✓ Filtered: {len(filtered)} accessible, {len(sensitive)} sensitive")
        
        except Exception as e:
            logger.error(f"✗ Error in permission_filter: {e}")
            state['errors'].append(f"permission_filter: {str(e)}")
            state['filtered_results'] = state.get('search_results', [])
            state['sensitive_results'] = []
            state['filtered_count'] = len(state['filtered_results'])
        
        return state
    
    # ==================== NODE 5: RERANK RESULTS ====================
    
    def rerank_results(self, state: AgentState) -> AgentState:
        """
        Node 5: Re-rank results by relevance using Gemini.
        
        Takes filtered results and re-ranks them based on
        semantic relevance to the query. Returns top 20.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with final_results, final_count
        """
        logger.info("NODE: rerank_results")
        state['current_node'] = 'rerank_results'
        state['execution_path'].append('rerank_results')
        
        try:
            results = state.get('filtered_results', [])
            query = state['query']
            
            # If no results, skip re-ranking
            if not results:
                state['final_results'] = []
                state['final_count'] = 0
                logger.info("No results to re-rank")
                return state
            
            # For now, simple re-ranking by score
            # In production, could use Gemini to re-rank based on content
            sorted_results = sorted(
                results,
                key=lambda x: x.score if hasattr(x, 'score') else x.get('score', 0),
                reverse=True
            )
            
            # Take top 20
            top_results = sorted_results[:20]
            
            state['final_results'] = top_results
            state['final_count'] = len(top_results)
            
            logger.info(f"✓ Re-ranked to top {state['final_count']} results")
        
        except Exception as e:
            logger.error(f"✗ Error in rerank_results: {e}")
            state['errors'].append(f"rerank_results: {str(e)}")
            state['final_results'] = state.get('filtered_results', [])[:20]
            state['final_count'] = len(state['final_results'])
        
        return state
    
    # ==================== NODE 6: RESPONSE SYNTHESIS ====================
    
    def response_synthesis(self, state: AgentState) -> AgentState:
        """
        Node 6: Synthesize final response using Claude.
        
        Uses Claude Sonnet 4.5 to generate a comprehensive answer
        based on the search results, with citations and related queries.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with response, citations, related_queries
        """
        logger.info("NODE: response_synthesis")
        state['current_node'] = 'response_synthesis'
        state['execution_path'].append('response_synthesis')
        
        try:
            query = state['query']
            results = state.get('final_results', [])
            
            if not results:
                state['response'] = "I couldn't find any relevant information for your query. This might indicate a knowledge gap."
                state['citations'] = []
                state['related_queries'] = []
                logger.info("No results to synthesize")
                return state
            
            # Build context from results
            context_parts = []
            citations = []
            
            for idx, result in enumerate(results[:10], 1):  # Use top 10 for context
                # Handle ScoredPoint objects
                payload = result.payload if hasattr(result, 'payload') else result.get('payload', {})
                title = payload.get('title', 'Untitled')
                content = payload.get('content', '')
                url = payload.get('url', '')
                source = payload.get('source', 'unknown')
                
                context_parts.append(f"[{idx}] {title}\nSource: {source}\n{content[:500]}")
                
                citations.append({
                    'number': idx,
                    'title': title,
                    'url': url,
                    'source': source
                })
            
            context = "\n\n".join(context_parts)
            
            # Create prompt for Claude
            prompt = f"""You are EngineIQ, an intelligent knowledge assistant. Answer the user's question based on the provided search results.

User Question: {query}

Search Results:
{context}

Instructions:
1. Provide a comprehensive answer based ONLY on the search results
2. Include relevant citations using [1], [2], etc.
3. If information is incomplete, acknowledge it
4. Suggest 2-3 related questions the user might ask
5. Be concise but thorough

Format your response as:

<answer>
[Your answer here with citations like [1], [2]]
</answer>

<related_questions>
- Question 1
- Question 2
- Question 3
</related_questions>
"""
            
            # Call Claude API if available
            if self.anthropic_client:
                try:
                    message = self.anthropic_client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=2048,
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    
                    response_text = message.content[0].text
                    
                    # Parse response
                    if '<answer>' in response_text and '</answer>' in response_text:
                        answer_start = response_text.find('<answer>') + 8
                        answer_end = response_text.find('</answer>')
                        answer = response_text[answer_start:answer_end].strip()
                    else:
                        answer = response_text
                    
                    if '<related_questions>' in response_text and '</related_questions>' in response_text:
                        rq_start = response_text.find('<related_questions>') + 19
                        rq_end = response_text.find('</related_questions>')
                        rq_text = response_text[rq_start:rq_end].strip()
                        related = [q.strip('- ').strip() for q in rq_text.split('\n') if q.strip()]
                    else:
                        related = []
                    
                    state['response'] = answer
                    state['related_queries'] = related
                
                except Exception as e:
                    logger.warning(f"Claude API call failed: {e}, using fallback")
                    state['response'] = self._fallback_response(query, results)
                    state['related_queries'] = []
            else:
                # Fallback if no Claude API
                state['response'] = self._fallback_response(query, results)
                state['related_queries'] = []
            
            state['citations'] = citations
            
            logger.info(f"✓ Synthesized response with {len(citations)} citations")
        
        except Exception as e:
            logger.error(f"✗ Error in response_synthesis: {e}")
            state['errors'].append(f"response_synthesis: {str(e)}")
            state['response'] = "I encountered an error generating the response."
            state['citations'] = []
            state['related_queries'] = []
        
        return state
    
    def _fallback_response(self, query: str, results: List[Dict]) -> str:
        """Generate simple fallback response without Claude"""
        if not results:
            return "No relevant information found."
        
        # Handle ScoredPoint objects
        first_result = results[0]
        if hasattr(first_result, 'payload'):
            top_result = first_result.payload
        else:
            top_result = first_result.get('payload', first_result)
            
        title = top_result.get('title', 'Untitled')
        content = top_result.get('content', '')[:500]
        
        return f"Based on '{title}': {content}... [1]"
    
    # ==================== NODE 7: FEEDBACK LEARNING ====================
    
    def feedback_learning(self, state: AgentState) -> AgentState:
        """
        Node 7: Save query and results for learning.
        
        Stores conversation in Qdrant conversations collection
        for analytics and continuous improvement.
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with feedback_saved=True
        """
        logger.info("NODE: feedback_learning")
        state['current_node'] = 'feedback_learning'
        state['execution_path'].append('feedback_learning')
        
        try:
            # Calculate response time
            if state['start_timestamp'] and not state['end_timestamp']:
                state['end_timestamp'] = int(time.time())
                state['response_time_ms'] = (state['end_timestamp'] - state['start_timestamp']) * 1000
            
            # Prepare conversation record
            conversation_id = state['conversation_id']
            embedding = state.get('query_embedding', [0.0] * 768)
            
            payload = {
                "id": conversation_id,
                "user_id": state['user_id'],
                "query": state['query'],
                "intent": state.get('intent'),
                "results_count": state.get('final_count', 0),
                "top_result_score": (
                    state['final_results'][0].score if hasattr(state['final_results'][0], 'score')
                    else state['final_results'][0].get('score', 0)
                ) if state.get('final_results') else 0,
                "sources_used": list(set([
                    (r.payload.get('source', 'unknown') if hasattr(r, 'payload') else r.get('payload', {}).get('source', 'unknown'))
                    for r in state.get('final_results', [])
                ])),
                "clicked_results": [],  # Would be updated with user interaction
                "user_rating": None,  # Would be set by user
                "timestamp": state['start_timestamp'],
                "response_time_ms": state.get('response_time_ms', 0),
                "triggered_approval": state.get('approval_required', False),
                "approval_granted": state.get('approval_status') == 'approved',
                "knowledge_gap_detected": state.get('knowledge_gap_detected', False),
            }
            
            # Save to Qdrant
            self.qdrant.index_document(
                collection_name="conversations",
                doc_id=conversation_id,
                vector=embedding,
                payload=payload
            )
            
            state['feedback_saved'] = True
            
            logger.info(f"✓ Saved conversation: {conversation_id}")
        
        except Exception as e:
            logger.error(f"✗ Error in feedback_learning: {e}")
            state['errors'].append(f"feedback_learning: {str(e)}")
            state['feedback_saved'] = False
        
        return state
    
    # ==================== NODE 8: KNOWLEDGE GAP DETECTION [HUMAN-IN-LOOP] ====================
    
    def knowledge_gap_detection(self, state: AgentState) -> AgentState:
        """
        Node 8: Detect knowledge gaps and suggest actions.
        
        HUMAN-IN-LOOP CHECKPOINT:
        - Analyzes if query reveals a knowledge gap
        - Criteria: Low result quality, repeated similar queries, no results
        - If gap detected: Sets gap_approval_required=True
        - Suggests documentation to create or expert to assign
        
        Args:
            state: Current agent state
        
        Returns:
            Updated state with knowledge_gap_detected, gap_suggestion
        """
        logger.info("NODE: knowledge_gap_detection")
        state['current_node'] = 'knowledge_gap_detection'
        state['execution_path'].append('knowledge_gap_detection')
        
        try:
            query = state['query']
            results = state.get('final_results', [])
            result_count = state.get('final_count', 0)
            
            # Detect gap conditions
            gap_detected = False
            gap_reason = None
            
            # Condition 1: No results found
            if result_count == 0:
                gap_detected = True
                gap_reason = "no_results_found"
            
            # Condition 2: Low quality results (all scores below threshold)
            elif results:
                avg_score = sum(
                    (r.score if hasattr(r, 'score') else r.get('score', 0))
                    for r in results
                ) / len(results)
                if avg_score < 0.4:
                    gap_detected = True
                    gap_reason = "low_quality_results"
            
            # Condition 3: Check for repeated queries (would need historical data)
            # For now, skip this check
            
            state['knowledge_gap_detected'] = gap_detected
            state['gap_reason'] = gap_reason
            
            if gap_detected:
                # Suggest action to fill gap
                entities = state.get('entities', [])
                keywords = state.get('keywords', [])
                
                suggestion = {
                    "gap_id": f"gap_{state['conversation_id']}",
                    "topic": " ".join(entities[:3]) if entities else query,
                    "query_pattern": query,
                    "priority": "high" if result_count == 0 else "medium",
                    "suggested_action": "create_documentation",
                    "suggested_content": {
                        "title": f"Documentation: {query}",
                        "topics": entities + keywords,
                        "questions_to_answer": [query],
                    },
                    "suggested_owner": None,  # Would be determined by expertise_map
                    "detected_at": int(time.time()),
                }
                
                state['gap_suggestion'] = suggestion
                state['gap_approval_required'] = True
                state['gap_approval_status'] = 'pending'
                
                logger.warning(f"⚠️  KNOWLEDGE GAP DETECTED: {gap_reason}")
                logger.warning(f"⚠️  HUMAN-IN-LOOP: Gap approval required")
            else:
                state['gap_approval_required'] = False
                state['gap_approval_status'] = 'not_required'
            
            logger.info(f"✓ Gap detection: gap_detected={gap_detected}")
        
        except Exception as e:
            logger.error(f"✗ Error in knowledge_gap_detection: {e}")
            state['errors'].append(f"knowledge_gap_detection: {str(e)}")
            state['knowledge_gap_detected'] = False
        
        return state
