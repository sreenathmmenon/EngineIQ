# EngineIQ Qdrant Operations Skill

A comprehensive skill for all Qdrant vector database operations in EngineIQ's knowledge intelligence platform.

## What This Skill Teaches

This skill provides everything you need for Qdrant operations:
- ✅ 4 specialized collections with exact schemas
- ✅ Hybrid search (vector similarity + metadata filters)
- ✅ Batch indexing with performance optimization
- ✅ Permission-aware filtering for security
- ✅ Scroll API for large result sets
- ✅ Recommendation engine (similar documents)
- ✅ Expert finding based on contributions
- ✅ Knowledge gap detection
- ✅ Complete error handling

## Quick Start

### 1. Read the Main Skill Documentation
Start with `skill.md` for complete Qdrant patterns.

### 2. Review Example Implementations
- `examples/qdrant_service.py` - Complete service wrapper
- `examples/search_examples.py` - All search patterns
- `examples/indexing_examples.py` - Batch indexing patterns

### 3. Initialize Collections
```python
from qdrant_service import QdrantService

service = QdrantService(url="http://localhost:6333")
service.initialize_collections()
```

## File Structure

```
engineiq-qdrant-operations/
├── README.md                       # This file
├── skill.md                        # Complete documentation
└── examples/
    ├── qdrant_service.py          # Service wrapper class
    ├── search_examples.py         # Search patterns
    └── indexing_examples.py       # Indexing patterns
```

## Core Concepts

### 1. Four Collections

**knowledge_base** - Primary search collection
- All indexed content from all sources
- 768-dim vectors from Gemini text-embedding-004
- Extensive payload with permissions, metadata, tags
- Indexed fields for hybrid search

**conversations** - Query tracking
- Track user queries and results
- Learn from click patterns
- Detect knowledge gaps

**expertise_map** - Expert finding
- Track who knows what based on contributions
- Evidence from Slack, GitHub, Jira, Confluence
- Weighted scoring by action type

**knowledge_gaps** - Gap detection
- Detect frequently searched but poorly answered queries
- Proactive documentation suggestions
- Priority-based action items

### 2. Hybrid Search

Combines vector similarity with metadata filters:

```python
# Search for recent Slack messages about kubernetes
results = service.hybrid_search(
    collection_name="knowledge_base",
    query_vector=embedding,
    must=[
        FieldCondition(key="source", match=MatchValue(value="slack")),
        FieldCondition(key="created_at", range=Range(gte=one_week_ago)),
        FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
    ],
    limit=20
)
```

### 3. Permission-Aware Filtering

Automatically filter results based on user permissions:

```python
user = {
    "id": "user_123",
    "teams": ["engineering"],
    "offshore": False,
    "third_party": False
}

results = service.search_with_permissions(
    query_vector=embedding,
    user=user,
    limit=20
)
```

Filters apply:
- ✅ Public documents
- ✅ User's teams
- ✅ Documents user owns
- ✅ Offshore restrictions
- ✅ Third-party access control

### 4. Batch Operations

Efficient bulk indexing:

```python
# Index 1000 documents efficiently
points = [create_point(doc) for doc in documents]

service.upsert(
    collection_name="knowledge_base",
    points=points,
    batch_size=100  # Auto-chunking
)
```

### 5. Scroll API

For large result sets (>100):

```python
offset = None
all_results = []

while True:
    points, offset = service.scroll(
        collection_name="knowledge_base",
        scroll_filter=filter,
        limit=100,
        offset=offset
    )

    all_results.extend(points)

    if offset is None:
        break
```

## Common Operations

### Initialize All Collections

```python
service = QdrantService(url="http://localhost:6333")
service.initialize_collections()
```

### Index a Document

```python
from qdrant_client.models import PointStruct

point = PointStruct(
    id="unique_id",
    vector=embedding,  # 768-dim from Gemini
    payload={
        "source": "slack",
        "content_type": "text",
        "title": "Document title",
        "content": "Full text content",
        "url": "https://...",
        "created_at": int(time.time()),
        "modified_at": int(time.time()),
        "owner": "user_id",
        "contributors": ["user1", "user2"],
        "permissions": {
            "public": False,
            "teams": ["engineering"],
            "users": [],
            "sensitivity": "internal",
            "offshore_restricted": False,
            "third_party_restricted": False
        },
        "metadata": {},
        "tags": ["tag1", "tag2"],
        "language": "en",
        "embedding_model": "gemini-text-embedding-004",
        "embedding_version": "v1",
        "chunk_index": 0,
        "total_chunks": 1
    }
)

service.upsert("knowledge_base", [point])
```

### Basic Search

```python
results = service.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    limit=20,
    score_threshold=0.7
)
```

### Hybrid Search with Filters

```python
results = service.hybrid_search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    must=[
        FieldCondition(key="source", match=MatchValue(value="github")),
        FieldCondition(key="content_type", match=MatchValue(value="code"))
    ],
    limit=20
)
```

### Find Similar Documents

```python
similar = service.find_similar_documents(
    document_id="slack_C123_1234567890",
    limit=5
)
```

### Find Experts

```python
experts = service.find_experts(
    topic_embedding=kubernetes_embedding,
    limit=5
)
```

### Track Query

```python
service.upsert(
    collection_name="conversations",
    points=[{
        "id": f"conv_{timestamp}_{user_id}",
        "vector": query_embedding,
        "payload": {
            "user_id": user_id,
            "query": query_text,
            "results_count": len(results),
            "top_result_score": results[0].score if results else 0,
            "timestamp": int(time.time()),
            "response_time_ms": response_time
        }
    }]
)
```

## Collection Schemas

### knowledge_base Payload

```python
{
    "id": str,
    "source": str,  # slack|github|box|jira|confluence|drive
    "content_type": str,  # text|code|image|pdf|video|audio
    "file_type": str,
    "title": str,
    "content": str,
    "url": str,
    "created_at": int,
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

### expertise_map Payload

```python
{
    "id": str,
    "user_id": str,
    "topic": str,
    "expertise_score": float,
    "evidence": [
        {
            "source": str,
            "action": str,  # authored|reviewed|answered|commented
            "doc_id": str,
            "doc_title": str,
            "doc_url": str,
            "timestamp": int,
            "contribution_score": float
        }
    ],
    "last_contribution": int,
    "contribution_count": int,
    "tags": [str]
}
```

### knowledge_gaps Payload

```python
{
    "id": str,
    "query_pattern": str,
    "search_count": int,
    "unique_users": [str],
    "avg_result_score": float,
    "first_detected": int,
    "last_searched": int,
    "priority": str,  # low|medium|high|critical
    "suggested_action": str,
    "assigned_to": str,
    "status": str,  # detected|approved|in_progress|resolved
    "related_docs": [str]
}
```

## Performance Guidelines

### Targets
- **Search**: <500ms for hybrid queries
- **Indexing**: <100ms per document (with batching)
- **Batch**: 1000 documents in <10 seconds

### Optimization Tips

1. **Use Payload Indexes**
   ```python
   # Always index fields you filter on
   service.client.create_payload_index(
       collection_name="knowledge_base",
       field_name="source",
       field_schema=PayloadSchemaType.KEYWORD
   )
   ```

2. **Batch Operations**
   ```python
   # Good: Batch 100 at a time
   service.upsert("knowledge_base", points, batch_size=100)

   # Bad: One at a time
   for point in points:
       service.upsert("knowledge_base", [point])
   ```

3. **Use Score Threshold**
   ```python
   # Filter out low-quality results
   results = service.search(..., score_threshold=0.7)
   ```

4. **Limit Payload**
   ```python
   # Only fetch needed fields
   results = service.search(..., with_payload=["title", "url"])
   ```

5. **Avoid Fetching Vectors**
   ```python
   # Vectors are large, don't fetch unless needed
   results = service.search(..., with_vectors=False)
   ```

## Error Handling

The service includes automatic retry logic:

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def upsert(...):
    # Automatically retries on failure
```

Handle collection not found:

```python
try:
    results = service.search("knowledge_base", embedding)
except Exception as e:
    print(f"Search failed: {e}")
    # Fallback or error handling
```

## Testing Your Integration

### Unit Tests
```python
def test_search():
    service = QdrantService("http://localhost:6333")
    results = service.search("knowledge_base", [0.1] * 768, limit=10)
    assert len(results) > 0
```

### Integration Tests
```python
def test_full_flow():
    service = QdrantService("http://localhost:6333")

    # Index
    service.upsert("knowledge_base", [test_point])

    # Search
    results = service.search("knowledge_base", test_embedding)

    # Verify
    assert any(r.id == test_point.id for r in results)
```

## Troubleshooting

### Issue: Search returns no results
- ✅ Check collection exists
- ✅ Verify embeddings are 768-dim
- ✅ Lower score_threshold
- ✅ Check filters aren't too restrictive

### Issue: Slow search performance
- ✅ Create payload indexes for filtered fields
- ✅ Use score_threshold to limit results
- ✅ Don't fetch vectors unless needed
- ✅ Limit payload to required fields

### Issue: Permission filtering not working
- ✅ Verify user object has required fields (id, teams, offshore, third_party)
- ✅ Check permissions structure in indexed documents
- ✅ Ensure payload indexes created for permission fields

## Advanced Features

### Recommendations
```python
similar = service.find_similar_documents("doc_id", limit=5)
```

### Expert Finding
```python
experts = service.find_experts(topic_embedding, limit=3)
```

### Knowledge Gap Detection
```python
gap_id = service.detect_knowledge_gap(
    query_embedding,
    query_text,
    user_id
)
```

### Scroll All Results
```python
all_points = service.scroll_all(
    "knowledge_base",
    scroll_filter=filter,
    batch_size=100
)
```

## Resources

- **Main Build Plan**: `../../../BUILD_PLAN.md`
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **Collection Schemas**: `skill.md` Section 1
- **Search Patterns**: `examples/search_examples.py`
- **Indexing Patterns**: `examples/indexing_examples.py`

## Questions?

Common questions are answered in `skill.md`. For specific issues:
- Check example files in `examples/`
- Review Qdrant documentation
- Verify collection schemas match specification

---

**Ready to use Qdrant in EngineIQ?** Start with `skill.md` for complete patterns! 🚀
