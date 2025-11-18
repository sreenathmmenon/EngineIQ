# EngineIQ Backend - Qdrant Foundation

Complete Qdrant vector database integration for EngineIQ's AI-powered knowledge intelligence platform.

## Overview

This backend provides:
- **4 Specialized Qdrant Collections** for different data types
- **QdrantService** class with all core operations
- **Permission-aware search** with automatic filtering
- **Batch indexing** for performance
- **Knowledge gap detection** for proactive insights
- **Expert finding** based on contributions
- **Comprehensive test suite** with mocks

## Architecture

```
backend/
├── config/
│   ├── __init__.py
│   └── qdrant_config.py          # Configuration and schemas
├── services/
│   ├── __init__.py
│   └── qdrant_service.py         # Main service class
├── tests/
│   ├── __init__.py
│   └── test_qdrant_service.py    # Comprehensive tests
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Collections

### 1. knowledge_base
Primary search collection for all indexed content from all sources.

**Vector:** 768-dim (Gemini text-embedding-004)  
**Indexed Fields:** source, content_type, permissions, created_at, tags, owner

**Use Cases:**
- Hybrid search with filters
- Permission-aware search
- Document recommendations

### 2. conversations
Query tracking for learning patterns and gap detection.

**Vector:** 768-dim query embeddings  
**Indexed Fields:** user_id, timestamp, top_result_score, triggered_approval

**Use Cases:**
- Track user queries
- Analyze search patterns
- Detect knowledge gaps

### 3. expertise_map
Expert finding based on contributions across all sources.

**Vector:** 768-dim topic embeddings  
**Indexed Fields:** user_id, expertise_score, tags, last_contribution

**Use Cases:**
- Find experts for topics
- Track contributor expertise
- Route questions to experts

### 4. knowledge_gaps
Proactive gap detection for missing documentation.

**Vector:** 768-dim query pattern embeddings  
**Indexed Fields:** priority, status, search_count, avg_result_score

**Use Cases:**
- Detect documentation gaps
- Prioritize content creation
- Track gap resolution

## Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Required environment variables:
- `QDRANT_URL`: Qdrant server URL (default: http://localhost:6333)
- `QDRANT_API_KEY`: API key for Qdrant Cloud (optional for local)

### 3. Start Qdrant (Local Development)

```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or using Docker Compose (add to docker-compose.yml)
services:
  qdrant:
    image: qdrant/qdrant
    ports:
      - "6333:6333"
    volumes:
      - ./qdrant_storage:/qdrant/storage
```

### 4. Initialize Collections

```python
from backend.services import QdrantService

# Initialize service
service = QdrantService()

# Create all collections
service.initialize_collections()

# Verify health
if service.health_check():
    print("✓ Qdrant is ready!")
```

## Usage Examples

### Index Documents

```python
from backend.services import QdrantService

service = QdrantService()

# Index single document
service.index_document(
    collection_name="knowledge_base",
    doc_id="slack_C123_1234567890",
    vector=embedding_vector,  # 768-dim from Gemini
    payload={
        "source": "slack",
        "content_type": "text",
        "title": "Deployment Discussion",
        "content": "How do we deploy to production?",
        "url": "https://workspace.slack.com/...",
        "created_at": 1699564800,
        "owner": "alice",
        "permissions": {
            "public": False,
            "teams": ["engineering"],
            "users": [],
            "sensitivity": "internal",
            "offshore_restricted": False,
            "third_party_restricted": False
        },
        "tags": ["deployment", "production"]
    }
)

# Batch index multiple documents
points = [
    {
        "id": f"doc_{i}",
        "vector": get_embedding(doc["content"]),
        "payload": doc
    }
    for i, doc in enumerate(documents)
]

service.batch_index(
    collection_name="knowledge_base",
    points=points,
    batch_size=100
)
```

### Search with Permissions

```python
# Define user
user = {
    "id": "user_123",
    "teams": ["engineering", "product"],
    "offshore": False,
    "third_party": False
}

# Search with automatic permission filtering
results = service.filter_by_permissions(
    query_vector=query_embedding,
    user=user,
    limit=20,
    score_threshold=0.7
)

for result in results:
    print(f"Score: {result.score:.2f}")
    print(f"Title: {result.payload['title']}")
    print(f"Source: {result.payload['source']}")
```

### Hybrid Search

```python
import time
from qdrant_client.models import FieldCondition, MatchValue, Range

# Search Slack messages from last week about kubernetes
one_week_ago = int(time.time()) - (7 * 86400)

results = service.hybrid_search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    must=[
        FieldCondition(key="source", match=MatchValue(value="slack")),
        FieldCondition(key="created_at", range=Range(gte=one_week_ago)),
        FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
    ],
    limit=50,
    score_threshold=0.6
)
```

### Find Similar Documents

```python
# Get documents similar to a specific document
similar_docs = service.get_similar_documents(
    document_id="slack_C123_1234567890",
    limit=10,
    score_threshold=0.75
)

for doc in similar_docs:
    print(f"Similar: {doc.payload['title']} (score: {doc.score:.2f})")
```

### Find Experts

```python
# Find experts for a topic
experts = service.get_expertise_data(
    topic_embedding=get_embedding("kubernetes deployment"),
    limit=5,
    score_threshold=0.6
)

for expert in experts:
    print(f"Expert: {expert['user_name']}")
    print(f"  Total Score: {expert['total_score']:.1f}")
    print(f"  Evidence: {len(expert['evidence'])} contributions")
```

### Log Conversations

```python
# Log a user query for gap detection
conversation_id = service.log_conversation(
    user_id="user_123",
    query="How do I deploy to production?",
    query_embedding=query_embedding,
    results=search_results,
    response_time_ms=250,
    clicked_results=["doc_1", "doc_5"],
    user_rating=4,
    triggered_approval=False
)
```

### Detect Knowledge Gaps

```python
# Manually check for gaps
gap_id = service.detect_knowledge_gaps(
    query_embedding=query_embedding,
    query_text="How to deploy to production?",
    user_id="user_123",
    result_score=0.3  # Low quality results
)

if gap_id:
    print(f"Knowledge gap detected: {gap_id}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
pytest backend/tests/

# Run specific test file
pytest backend/tests/test_qdrant_service.py

# Run with coverage
pytest backend/tests/ --cov=backend --cov-report=html

# Run specific test
pytest backend/tests/test_qdrant_service.py::TestQdrantService::test_filter_by_permissions
```

## Configuration

All configuration is centralized in `config/qdrant_config.py`:

```python
from backend.config import QdrantConfig

# Access configuration
print(QdrantConfig.EMBEDDING_DIMENSION)  # 768
print(QdrantConfig.DEFAULT_BATCH_SIZE)   # 100
print(QdrantConfig.GAP_MIN_SEARCH_COUNT) # 10

# Get collection names
collections = QdrantConfig.get_collection_names()
# ['knowledge_base', 'conversations', 'expertise_map', 'knowledge_gaps']

# Get collection config
kb_config = QdrantConfig.get_collection_config('knowledge_base')
print(kb_config['size'])  # 768
print(kb_config['indexes'])  # List of indexed fields
```

## Payload Schemas

### knowledge_base
```python
{
    "id": str,
    "source": str,  # slack|github|box|jira|confluence|drive|asana|notion
    "content_type": str,  # text|code|image|pdf|video|audio
    "file_type": str,
    "title": str,
    "content": str,
    "url": str,
    "created_at": int,  # Unix timestamp
    "modified_at": int,
    "owner": str,
    "contributors": [str],
    "permissions": {
        "public": bool,
        "teams": [str],
        "users": [str],
        "sensitivity": str,  # public|internal|confidential|restricted
        "offshore_restricted": bool,
        "third_party_restricted": bool
    },
    "metadata": {},  # Source-specific
    "tags": [str],
    "language": str,
    "embedding_model": "gemini-text-embedding-004",
    "embedding_version": "v1",
    "chunk_index": int,
    "total_chunks": int
}
```

### conversations
```python
{
    "user_id": str,
    "query": str,
    "results_count": int,
    "top_result_score": float,
    "sources_used": [str],
    "clicked_results": [str],
    "user_rating": int,  # 1-5
    "timestamp": int,
    "response_time_ms": int,
    "triggered_approval": bool,
    "approval_granted": bool
}
```

### expertise_map
```python
{
    "user_id": str,
    "user_name": str,
    "topic": str,
    "expertise_score": float,  # 0-100
    "evidence": [
        {
            "source": str,
            "action": str,
            "doc_id": str,
            "doc_title": str,
            "timestamp": int,
            "contribution_score": float
        }
    ],
    "last_contribution": int,
    "contribution_count": int,
    "tags": [str],
    "trend": str  # increasing|stable|decreasing
}
```

### knowledge_gaps
```python
{
    "topic": str,
    "query_patterns": [str],
    "query_count": int,
    "avg_result_quality": float,
    "first_detected": int,
    "last_query": int,
    "suggested_action": str,
    "suggested_owner": str,
    "status": str,  # detected|approved|in_progress|resolved
    "priority": str,  # low|medium|high|critical
    "related_docs": [str]
}
```

## API Reference

### QdrantService Methods

#### Collection Management
- `initialize_collections(recreate=False)` - Create all collections
- `get_collection_stats(collection_name)` - Get collection statistics
- `health_check()` - Check Qdrant health

#### Indexing Operations
- `index_document(collection, doc_id, vector, payload)` - Index single document
- `batch_index(collection, points, batch_size)` - Batch index documents

#### Search Operations
- `hybrid_search(collection, query_vector, must, should, must_not, limit)` - Hybrid search
- `filter_by_permissions(query_vector, user, filters, limit)` - Permission-aware search
- `get_similar_documents(doc_id, limit, user)` - Find similar documents

#### Intelligence Operations
- `get_expertise_data(topic_embedding, limit)` - Find experts
- `detect_knowledge_gaps(query_embedding, query_text, user_id, score)` - Detect gaps
- `log_conversation(user_id, query, embedding, results, ...)` - Log query

#### Utility Operations
- `scroll_all(collection, filter, batch_size, process_fn)` - Scroll all results
- `retrieve(collection, ids)` - Get specific points
- `delete(collection, points_selector)` - Delete points

## Performance Tips

1. **Batch Operations**: Always use `batch_index()` instead of individual `index_document()` calls
2. **Score Threshold**: Set appropriate thresholds to reduce low-quality results
3. **Payload Fields**: Only fetch fields you need using `with_payload=["field1", "field2"]`
4. **Indexes**: All frequently filtered fields are pre-indexed for fast queries
5. **Connection Pooling**: Service reuses the same client connection

## Error Handling

The service includes automatic retry logic with exponential backoff:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def index_document(...):
    # Automatically retries on failure
    pass
```

## Next Steps

1. **Deploy Qdrant**: Set up Qdrant Cloud or self-hosted instance
2. **Create Connectors**: Build data source connectors using `engineiq-connector-builder` skill
3. **Generate Demo Data**: Use `engineiq-demo-data` skill for realistic test data
4. **Build Agent System**: Integrate with LLM agent for intelligent search
5. **Add Frontend**: Create React UI for search and insights

## Resources

- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Gemini Embeddings](https://ai.google.dev/tutorials/embeddings_quickstart)
- [EngineIQ Skills](.claude/skills/)

## Support

For issues or questions:
1. Check the test suite for usage examples
2. Review the skill documentation in `.claude/skills/engineiq-qdrant-operations/`
3. Consult the example files in `.claude/skills/engineiq-qdrant-operations/examples/`
