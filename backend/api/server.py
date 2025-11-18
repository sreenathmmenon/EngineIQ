"""
EngineIQ API Server
Simple FastAPI server for demo presentation
"""

import os
import sys
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging

# Add parent directory to path FIRST
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load API key if not in environment
if not os.getenv("GEMINI_API_KEY"):
    # Check multiple locations for .env-droid
    env_locations = [
        os.path.join(os.path.dirname(__file__), "../..", ".env-droid"),  # Project root
        os.path.expanduser("~/.env-droid"),  # Home directory
    ]
    
    loaded = False
    for env_file in env_locations:
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.strip() and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.strip().split('=', 1)
                            if key == "GEMINI_API_KEY":
                                os.environ["GEMINI_API_KEY"] = value
                                print(f"✓ Loaded GEMINI_API_KEY from {env_file}")
                                loaded = True
                                break
            if loaded:
                break
    
    if not loaded:
        print(f"⚠️  Warning: No GEMINI_API_KEY in environment and no .env-droid file found")
else:
    print(f"✓ Using GEMINI_API_KEY from environment")

# Now import from backend
from backend.services.qdrant_service import QdrantService
from backend.services.gemini_service import GeminiService

# Import agent system
AGENT_AVAILABLE = False
try:
    from backend.agents.graph import create_agent_graph
    from backend.agents.state import create_initial_state
    AGENT_AVAILABLE = True
    logger.info("✓ Agent system loaded")
except Exception as e:
    logging.warning(f"Agent system not available: {e}")

# Import admin router
ADMIN_AVAILABLE = False
try:
    from backend.api.admin import router as admin_router
    ADMIN_AVAILABLE = True
except Exception as e:
    logging.warning(f"Admin API not available: {e}")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="EngineIQ API",
    description="AI-Powered Knowledge Intelligence Platform",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
qdrant = QdrantService()
try:
    gemini = GeminiService()
except Exception as e:
    logger.warning(f"GeminiService initialization failed: {e}")
    gemini = None


# Request/Response Models
class SearchRequest(BaseModel):
    query: str
    collection: str = "knowledge_base"
    limit: int = 5
    user_id: Optional[str] = None
    permission_level: str = "user"


class SearchResult(BaseModel):
    id: str
    title: str
    content: str
    score: float
    source: str
    metadata: Dict


class AgentInsights(BaseModel):
    """Agent execution insights for visualization"""
    agent_used: bool
    intent: Optional[str] = None
    execution_path: Optional[List[str]] = None
    execution_time_ms: Optional[int] = None
    documents_searched: Optional[int] = None
    documents_filtered: Optional[int] = None
    approval_required: Optional[bool] = None
    knowledge_gap_detected: Optional[bool] = None


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    agent_insights: Optional[AgentInsights] = None


class ExpertiseProfile(BaseModel):
    user_id: str
    name: str
    score: float
    expertise_areas: List[str]
    evidence_count: int


class KnowledgeGap(BaseModel):
    id: str
    topic: str
    search_count: int
    user_count: int
    avg_quality: float
    priority: str
    suggested_owner: Optional[str]


# Include admin router if available
if ADMIN_AVAILABLE:
    app.include_router(admin_router)
    logger.info("Admin API endpoints enabled")

# Serve static files and frontend
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def root():
    """Serve the demo UI"""
    index_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "service": "EngineIQ API",
        "status": "running",
        "version": "1.0.0",
        "docs": "/docs",
        "admin": "/admin.html"
    }


@app.get("/admin.html")
async def admin_page():
    """Serve the admin dashboard"""
    admin_path = os.path.join(os.path.dirname(__file__), "static", "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"error": "Admin dashboard not found"}

@app.get("/api/data-sources")
async def get_data_sources():
    """Get dynamic counts for all data sources"""
    try:
        import requests
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        
        # Get counts by content type
        base_url = "http://localhost:6333"
        
        def count_by_type(content_type):
            payload = {
                "filter": {
                    "must": [{"key": "content_type", "match": {"value": content_type}}]
                },
                "limit": 0
            }
            resp = requests.post(f"{base_url}/collections/knowledge_base/points/scroll", json=payload)
            return len(resp.json().get('result', {}).get('points', []))
        
        def count_by_source(source):
            payload = {
                "filter": {
                    "must": [{"key": "source", "match": {"value": source}}]
                },
                "limit": 0
            }
            resp = requests.post(f"{base_url}/collections/knowledge_base/points/scroll", json=payload)
            return len(resp.json().get('result', {}).get('points', []))
        
        # Count each type
        pdf_count = count_by_type("pdf")
        slack_count = count_by_source("Slack")
        github_count = count_by_source("GitHub")
        wiki_count = count_by_type("wiki")
        video_count = count_by_type("video")
        image_count = count_by_type("image")
        
        # Get total
        total_resp = requests.get(f"{base_url}/collections/knowledge_base")
        total_count = total_resp.json().get('result', {}).get('points_count', 0)
        
        return {
            "total": total_count,
            "sources": {
                "box": pdf_count,
                "slack": slack_count,
                "github": github_count,
                "wiki": wiki_count,
                "videos": video_count,
                "images": image_count
            }
        }
    except Exception as e:
        logger.error(f"Error getting data sources: {e}")
        return {
            "total": 0,
            "sources": {
                "box": 0,
                "slack": 0,
                "github": 0,
                "wiki": 0,
                "videos": 0,
                "images": 0
            }
        }


@app.get("/index-light.html")
async def light_theme():
    """Serve the light theme UI"""
    light_path = os.path.join(os.path.dirname(__file__), "static", "index-light.html")
    if os.path.exists(light_path):
        return FileResponse(light_path)
    return {
        "error": "Light theme not found"
    }


@app.get("/health")
async def health_check():
    """Check if services are healthy"""
    qdrant_healthy = qdrant.health_check()
    
    return {
        "qdrant": "healthy" if qdrant_healthy else "unhealthy",
        "gemini": "available" if gemini else "unavailable",
        "status": "healthy" if qdrant_healthy else "degraded"
    }


@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search for knowledge using intelligent agent workflow
    
    Demo Queries:
    - "How do I deploy hotfixes to production?"
    - "Who is the Kubernetes expert?"
    - "How do we rollback database migrations?"
    """
    import time
    start_time = time.time()
    
    try:
        # Use agent workflow if available
        if AGENT_AVAILABLE and gemini:
            logger.info(f"🤖 Using agent workflow for query: {request.query}")
            
            # Create agent graph
            graph = create_agent_graph(
                gemini_service=gemini,
                qdrant_service=qdrant,
                anthropic_api_key=None,  # Optional - for response synthesis
                enable_checkpoints=False  # Disable for demo (no pause for approval)
            )
            
            # Create initial state
            state = create_initial_state(
                query=request.query,
                user_id=request.user_id or "demo_user",
                user_teams=["engineering"],  # Default team
                user_location="US",
                user_type="employee"
            )
            
            # Execute agent workflow
            try:
                final_state = graph.invoke(state)
                
                # Get results from agent
                agent_results = final_state.get('final_results', [])
                
                # Format results with proper deduplication
                search_results = []
                seen_titles = set()  # Dedupe by title to avoid same document multiple times
                
                # Process ALL results for deduplication, then limit
                for result in agent_results:
                    # Check if result is a dict (from error handling) or ScoredPoint object
                    if isinstance(result, dict):
                        # Dict format (fallback)
                        content = result.get("payload", {}).get("raw_content", "")[:500]
                        doc_id = result.get("payload", {}).get("id", result.get("id"))
                        parent_id = result.get("payload", {}).get("parent_doc_id", doc_id)
                        url = result.get("payload", {}).get("url", "")
                        title = result.get("payload", {}).get("title", "Untitled")
                        score = result.get("score", 0.0)
                        payload = result.get("payload", {})
                        result_id = result.get("id", "")
                    else:
                        # ScoredPoint object (normal case)
                        content = result.payload.get("raw_content", "")[:500]
                        doc_id = result.payload.get("id", str(result.id))
                        parent_id = result.payload.get("parent_doc_id", doc_id)
                        url = result.payload.get("url", "")
                        title = result.payload.get("title", "Untitled")
                        score = result.score
                        payload = result.payload
                        result_id = str(result.id)
                    
                    # Use title as deduplication key (show each document only once)
                    if title in seen_titles:
                        continue
                    seen_titles.add(title)
                    
                    # Determine source
                    if "slack.com" in url:
                        source = "Slack"
                    elif "github.com" in url:
                        source = "GitHub"
                    elif "box.com" in url or payload.get("file_type"):
                        source = "Box"
                    else:
                        source = payload.get("source", "Knowledge Base")
                    
                    # Title formatting
                    if len(title) > 100:
                        title = title[:100] + "..."
                    
                    search_results.append(SearchResult(
                        id=result_id,
                        title=title,
                        content=content,
                        score=score,
                        source=source,
                        metadata=payload
                    ))
                    
                    # Stop if we have enough unique results
                    if len(search_results) >= request.limit:
                        break
                
                # Calculate execution time
                execution_time_ms = int((time.time() - start_time) * 1000)
                
                # Debug: Log state values
                logger.info(f"Agent state - search_count: {final_state.get('search_count')}, filtered_count: {final_state.get('filtered_count')}")
                logger.info(f"Agent state - final_count: {final_state.get('final_count')}, errors: {final_state.get('errors')}")
                
                # Create agent insights
                agent_insights = AgentInsights(
                    agent_used=True,
                    intent=final_state.get('intent', 'search'),
                    execution_path=final_state.get('execution_path', []),
                    execution_time_ms=execution_time_ms,
                    documents_searched=final_state.get('search_count', 0),
                    documents_filtered=final_state.get('filtered_count', 0),
                    approval_required=final_state.get('approval_required', False),
                    knowledge_gap_detected=final_state.get('knowledge_gap_detected', False)
                )
                
                logger.info(f"✓ Agent completed: {len(search_results)} results in {execution_time_ms}ms")
                
                return SearchResponse(
                    query=request.query,
                    results=search_results[:request.limit],  # Ensure we return exactly the limit
                    total=len(search_results),
                    agent_insights=agent_insights
                )
                
            except Exception as agent_error:
                logger.error(f"Agent workflow failed: {agent_error}")
                logger.info("Falling back to direct search")
                # Fall through to direct search below
        
        # Fallback: Direct search (no agent)
        logger.info(f"🔍 Using direct search for query: {request.query}")
        
        # Generate embedding
        if gemini:
            embedding = gemini.generate_embedding(request.query)
        else:
            import hashlib
            hash_val = int(hashlib.md5(request.query.encode()).hexdigest(), 16)
            embedding = [(hash_val % 1000) / 1000.0] * 768
        
        # Search in Qdrant
        results = qdrant.hybrid_search(
            collection_name=request.collection,
            query_vector=embedding,
            limit=request.limit * 2,
            must=None
        )
        
        # Format results and deduplicate
        search_results = []
        seen_ids = set()
        
        for result in results:
            content = result.payload.get("raw_content", "")[:500]
            doc_id = result.payload.get("id", result.id)
            parent_id = result.payload.get("parent_doc_id", doc_id)
            
            if parent_id in seen_ids:
                continue
            seen_ids.add(parent_id)
            
            url = result.payload.get("url", "")
            if "slack.com" in url:
                source = "Slack"
            elif "github.com" in url:
                source = "GitHub"
            elif "box.com" in url or result.payload.get("file_type"):
                source = "Box"
            else:
                source = result.payload.get("source", "Knowledge Base")
            
            title = result.payload.get("title", "Untitled")
            if len(title) > 100:
                title = title[:100] + "..."
            
            search_results.append(SearchResult(
                id=result.id,
                title=title,
                content=content,
                score=result.score,
                source=source,
                metadata=result.payload
            ))
            
            if len(search_results) >= request.limit:
                break
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        return SearchResponse(
            query=request.query,
            results=search_results[:request.limit],
            total=len(search_results),
            agent_insights=AgentInsights(
                agent_used=False,
                execution_time_ms=execution_time_ms
            )
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/expertise", response_model=List[ExpertiseProfile])
async def get_expertise(topic: Optional[str] = None, limit: int = 10):
    """
    Get expertise rankings
    
    Demo: GET /api/expertise?topic=kubernetes
    """
    try:
        # Generate embedding for topic
        if topic and gemini:
            embedding = gemini.generate_embedding(topic)
        else:
            # Get all profiles
            embedding = [0.5] * 768
        
        # Search expertise_map collection
        results = qdrant.hybrid_search(
            collection_name="expertise_map",
            query_vector=embedding,
            limit=limit
        )
        
        # Format results
        profiles = []
        for result in results:
            profiles.append(ExpertiseProfile(
                user_id=result.payload.get("user_id", ""),
                name=result.payload.get("name", "Unknown"),
                score=result.payload.get("score", 0.0),
                expertise_areas=result.payload.get("expertise_areas", []),
                evidence_count=result.payload.get("evidence_count", 0)
            ))
        
        return profiles
    
    except Exception as e:
        logger.error(f"Expertise error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge-gaps", response_model=List[KnowledgeGap])
async def get_knowledge_gaps(priority: Optional[str] = None):
    """
    Get detected knowledge gaps
    
    Demo: GET /api/knowledge-gaps?priority=high
    """
    try:
        # Get all knowledge gaps
        results = qdrant.client.scroll(
            collection_name="knowledge_gaps",
            limit=100
        )[0]
        
        # Format results
        gaps = []
        for point in results:
            if priority and point.payload.get("priority") != priority:
                continue
            
            # Extract user_count properly
            unique_users = point.payload.get("unique_users", [])
            user_count = len(unique_users) if isinstance(unique_users, list) else unique_users
            
            gaps.append(KnowledgeGap(
                id=point.payload.get("topic", "unknown"),
                topic=point.payload.get("topic", "Unknown"),
                search_count=point.payload.get("search_count", 0),
                user_count=user_count,
                avg_quality=point.payload.get("avg_result_quality", 0.0),
                priority=point.payload.get("priority", "medium"),
                suggested_owner=point.payload.get("suggested_owner")
            ))
        
        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda x: priority_order.get(x.priority, 3))
        
        return gaps
    
    except Exception as e:
        logger.error(f"Knowledge gaps error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/stats")
async def get_stats():
    """Get collection statistics"""
    try:
        import requests
        stats = {}
        
        # Get stats for each collection using direct HTTP (avoids pydantic issues)
        for collection in ["knowledge_base", "conversations", "expertise_map", "knowledge_gaps"]:
            try:
                response = requests.get(f"http://localhost:6333/collections/{collection}")
                data = response.json()
                points_count = data.get("result", {}).get("points_count", 0)
                stats[collection] = {
                    "points_count": points_count,
                    "status": "healthy"
                }
                logger.info(f"Stats: {collection} = {points_count} points")
            except Exception as e:
                logger.warning(f"Could not get stats for {collection}: {e}")
                stats[collection] = {
                    "points_count": 0,
                    "status": "not_found"
                }
        
        return stats
    
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*70)
    print("🚀 Starting EngineIQ API Server")
    print("="*70)
    print("\n📋 Demo Endpoints:")
    print("   • http://localhost:8000/docs - Interactive API docs")
    print("   • http://localhost:8000/health - Health check")
    print("   • POST http://localhost:8000/api/search - Search knowledge")
    print("   • GET http://localhost:8000/api/expertise - Get experts")
    print("   • GET http://localhost:8000/api/knowledge-gaps - Get gaps")
    print("\n🎯 Demo Queries:")
    print('   • "How do I deploy hotfixes to production?"')
    print('   • "Who is the Kubernetes expert?"')
    print('   • "How do we rollback database migrations?"')
    print("\n" + "="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
