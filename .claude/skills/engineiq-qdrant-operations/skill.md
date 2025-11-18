# EngineIQ Qdrant Operations Skill

**Purpose:** Master all Qdrant vector database operations for EngineIQ's knowledge intelligence platform.

**When to use:** When implementing search, indexing, recommendations, or any Qdrant database operations in EngineIQ.

---

## Overview

EngineIQ uses Qdrant as its vector database with 4 specialized collections:
1. **knowledge_base** - Primary search collection (all indexed content)
2. **conversations** - Query tracking for learning
3. **expertise_map** - Expert finding based on contributions
4. **knowledge_gaps** - Proactive gap detection

This skill covers all operations across these collections including hybrid search, batch indexing, permission filtering, and performance optimization.

---

## 1. Collection Schemas

### Collection 1: knowledge_base

**Purpose:** Primary search collection for all indexed content from all sources.

**Configuration:**
```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType, PayloadIndexInfo

collection_config = {
    "collection_name": "knowledge_base",
    "vectors_config": VectorParams(
        size=768,  # Gemini text-embedding-004
        distance=Distance.COSINE,
        on_disk=False  # Keep in memory for speed
    ),
    "optimizers_config": {
        "default_segment_number": 2,
        "indexing_threshold": 20000,
        "memmap_threshold": 50000
    },
    "replication_factor": 2  # High availability
}
```

**Payload Schema:**
```python
payload = {
    # Core fields
    "id": str,                      # Unique identifier
    "source": str,                  # slack|github|box|jira|confluence|drive|asana|notion
    "content_type": str,            # text|code|image|pdf|video|audio
    "file_type": str,               # doc|pdf|py|jpg|mp4|md|...
    "title": str,                   # Display title
    "content": str,                 # Extracted text (max 10k chars per chunk)
    "url": str,                     # Link back to source

    # Timestamps
    "created_at": int,              # Unix timestamp
    "modified_at": int,             # Unix timestamp

    # People
    "owner": str,                   # Primary author/owner
    "contributors": [str],          # All contributors

    # Permissions (CRITICAL for filtering)
    "permissions": {
        "public": bool,
        "teams": [str],
        "users": [str],
        "sensitivity": str,         # public|internal|confidential|restricted
        "offshore_restricted": bool,
        "third_party_restricted": bool
    },

    # Source-specific metadata
    "metadata": {
        "slack_channel": str,
        "slack_thread_ts": str,
        "github_repo": str,
        "github_path": str,
        "jira_project": str,
        "jira_issue_key": str,
        "box_folder_id": str,
        "drive_folder_id": str
    },

    # Extracted metadata
    "tags": [str],
    "language": str,                # en, es, fr, etc.

    # Embedding metadata
    "embedding_model": "gemini-text-embedding-004",
    "embedding_version": "v1",

    # Chunking (for large documents)
    "chunk_index": int,             # 0 if not chunked
    "total_chunks": int             # 1 if not chunked
}
```

**Indexed Fields (for hybrid search):**
```python
indexes = [
    PayloadIndexInfo(field_name="source", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="content_type", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="permissions.sensitivity", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="permissions.teams", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="permissions.public", field_schema=PayloadSchemaType.BOOL),
    PayloadIndexInfo(field_name="permissions.offshore_restricted", field_schema=PayloadSchemaType.BOOL),
    PayloadIndexInfo(field_name="permissions.third_party_restricted", field_schema=PayloadSchemaType.BOOL),
    PayloadIndexInfo(field_name="created_at", field_schema=PayloadSchemaType.INTEGER),
    PayloadIndexInfo(field_name="tags", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="owner", field_schema=PayloadSchemaType.KEYWORD),
]
```

**Creation:**
```python
client.create_collection(
    collection_name="knowledge_base",
    vectors_config=VectorParams(size=768, distance=Distance.COSINE, on_disk=False),
    optimizers_config=models.OptimizersConfigDiff(
        default_segment_number=2,
        indexing_threshold=20000
    ),
    replication_factor=2
)

# Create payload indexes
for index in indexes:
    client.create_payload_index(
        collection_name="knowledge_base",
        field_name=index.field_name,
        field_schema=index.field_schema
    )
```

---

### Collection 2: conversations

**Purpose:** Track user queries for learning patterns and detecting knowledge gaps.

**Configuration:**
```python
collection_config = {
    "collection_name": "conversations",
    "vectors_config": VectorParams(
        size=768,
        distance=Distance.COSINE,
        on_disk=False
    )
}
```

**Payload Schema:**
```python
payload = {
    "id": str,                      # uuid4
    "user_id": str,
    "query": str,                   # Original query text
    "query_embedding": [float],     # Store for similarity search
    "results_count": int,
    "top_result_score": float,      # Best match score (0-1)
    "clicked_results": [str],       # IDs of results user clicked
    "user_rating": int,             # 1-5 stars (optional)
    "timestamp": int,               # Unix timestamp
    "response_time_ms": int,        # Performance tracking
    "triggered_approval": bool,     # Did this trigger human-in-loop?
    "approval_granted": bool        # Was approval granted?
}
```

**Indexed Fields:**
```python
indexes = [
    PayloadIndexInfo(field_name="user_id", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="timestamp", field_schema=PayloadSchemaType.INTEGER),
    PayloadIndexInfo(field_name="top_result_score", field_schema=PayloadSchemaType.FLOAT)
]
```

---

### Collection 3: expertise_map

**Purpose:** Track who knows what based on contributions across all sources.

**Configuration:**
```python
collection_config = {
    "collection_name": "expertise_map",
    "vectors_config": VectorParams(
        size=768,
        distance=Distance.COSINE,
        on_disk=False
    )
}
```

**Payload Schema:**
```python
payload = {
    "id": str,                      # uuid4
    "user_id": str,
    "topic": str,                   # e.g., "kubernetes deployment"
    "topic_embedding": [float],     # 768-dim embedding of topic
    "expertise_score": float,       # 0-100 calculated score
    "evidence": [
        {
            "source": str,          # slack|github|jira|confluence
            "action": str,          # authored|reviewed|answered|commented
            "doc_id": str,
            "doc_title": str,
            "doc_url": str,
            "timestamp": int,
            "contribution_score": float
        }
    ],
    "last_contribution": int,       # Unix timestamp
    "contribution_count": int,
    "tags": [str]
}
```

**Expertise Score Calculation:**
```python
score = (
    (github_commits * 2.0) +
    (slack_answers * 1.5) +
    (confluence_authored * 3.0) +
    (jira_resolved * 1.0) +
    (code_reviews * 1.5)
) * recency_multiplier

# Recency multiplier: decay over time
recency_multiplier = 1.0 if days_since < 30 else 0.8 if days_since < 90 else 0.5
```

**Indexed Fields:**
```python
indexes = [
    PayloadIndexInfo(field_name="user_id", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="expertise_score", field_schema=PayloadSchemaType.FLOAT),
    PayloadIndexInfo(field_name="tags", field_schema=PayloadSchemaType.KEYWORD)
]
```

---

### Collection 4: knowledge_gaps

**Purpose:** Detect and track gaps in documentation proactively.

**Configuration:**
```python
collection_config = {
    "collection_name": "knowledge_gaps",
    "vectors_config": VectorParams(
        size=768,
        distance=Distance.COSINE,
        on_disk=False
    )
}
```

**Payload Schema:**
```python
payload = {
    "id": str,                      # hash(query_pattern)
    "query_pattern": str,           # Representative query
    "query_embedding": [float],     # 768-dim embedding
    "search_count": int,            # How many times searched
    "unique_users": [str],          # Users who searched
    "avg_result_score": float,      # Average quality of results
    "avg_user_rating": float,       # Average user satisfaction
    "first_detected": int,          # Unix timestamp
    "last_searched": int,           # Unix timestamp
    "priority": str,                # low|medium|high|critical
    "suggested_action": str,        # "Create documentation on..."
    "assigned_to": str,             # Expert to create doc
    "status": str,                  # detected|approved|in_progress|resolved
    "related_docs": [str]           # Existing similar docs
}
```

**Gap Detection Algorithm:**
```python
# Trigger conditions
if (
    gap.search_count >= 10 and              # Many searches
    gap.avg_result_score < 0.4 and          # Poor results
    (now - gap.first_detected) <= 7 * 86400 # Within 7 days
):
    priority = "high" if len(gap.unique_users) > 5 else "medium"
```

**Indexed Fields:**
```python
indexes = [
    PayloadIndexInfo(field_name="priority", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="status", field_schema=PayloadSchemaType.KEYWORD),
    PayloadIndexInfo(field_name="search_count", field_schema=PayloadSchemaType.INTEGER)
]
```

---

## 2. Hybrid Search Pattern

Hybrid search combines vector similarity with metadata filters for precise, permission-aware results.

### Basic Hybrid Search

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

# Search with source filter
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,  # 768-dim from Gemini
    query_filter=Filter(
        must=[
            FieldCondition(
                key="source",
                match=MatchValue(value="slack")
            )
        ]
    ),
    limit=20,
    with_payload=True,
    score_threshold=0.7
)
```

### Permission-Aware Search

```python
def search_with_permissions(
    client: QdrantClient,
    query_embedding: List[float],
    user: dict,
    limit: int = 20
) -> List[dict]:
    """Search with automatic permission filtering"""

    # Build permission filter
    must_conditions = []
    must_not_conditions = []

    # Either public OR user has access
    should_conditions = [
        FieldCondition(key="permissions.public", match=MatchValue(value=True))
    ]

    # User is in teams
    if user.get("teams"):
        should_conditions.append(
            FieldCondition(
                key="permissions.teams",
                match=MatchValue(any=user["teams"])
            )
        )

    # User is explicitly listed
    should_conditions.append(
        FieldCondition(
            key="permissions.users",
            match=MatchValue(any=[user["id"]])
        )
    )

    # User is owner
    should_conditions.append(
        FieldCondition(
            key="owner",
            match=MatchValue(value=user["id"])
        )
    )

    # Offshore restrictions
    if user.get("offshore"):
        must_not_conditions.append(
            FieldCondition(
                key="permissions.offshore_restricted",
                match=MatchValue(value=True)
            )
        )

    # Third-party restrictions
    if user.get("third_party"):
        must_not_conditions.append(
            FieldCondition(
                key="permissions.third_party_restricted",
                match=MatchValue(value=True)
            )
        )

    # Combine filters
    query_filter = Filter(
        should=should_conditions,
        must_not=must_not_conditions
    )

    # Search
    results = client.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=query_filter,
        limit=limit,
        with_payload=True,
        score_threshold=0.5
    )

    return results
```

### Multi-Condition Search

```python
# Complex query: Slack messages from last week about kubernetes
import time

one_week_ago = int(time.time()) - (7 * 86400)

results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(key="source", match=MatchValue(value="slack")),
            FieldCondition(key="created_at", range=models.Range(gte=one_week_ago)),
            FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
        ]
    ),
    limit=50,
    with_payload=True
)
```

### Search with Sensitivity Filtering

```python
# Only show public and internal content (hide confidential/restricted)
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="permissions.sensitivity",
                match=MatchValue(any=["public", "internal"])
            )
        ]
    ),
    limit=20,
    with_payload=True
)
```

---

## 3. Batch Indexing for Performance

Batch operations are critical for performance when indexing large amounts of content.

### Batch Upsert

```python
from qdrant_client.models import PointStruct

# Prepare batch of points
points = []

for item in content_items:
    points.append(
        PointStruct(
            id=item["id"],
            vector=item["embedding"],
            payload=item["payload"]
        )
    )

# Batch upsert (much faster than individual upserts)
client.upsert(
    collection_name="knowledge_base",
    points=points,
    wait=True  # Wait for indexing to complete
)
```

### Batch Upsert with Chunking

```python
def batch_upsert(
    client: QdrantClient,
    collection_name: str,
    points: List[PointStruct],
    batch_size: int = 100
):
    """Upsert points in batches"""
    total = len(points)

    for i in range(0, total, batch_size):
        batch = points[i:i + batch_size]

        client.upsert(
            collection_name=collection_name,
            points=batch,
            wait=True
        )

        print(f"✓ Indexed {min(i + batch_size, total)}/{total} points")
```

### Parallel Batch Indexing

```python
import asyncio
from qdrant_client import AsyncQdrantClient

async def parallel_batch_upsert(
    client: AsyncQdrantClient,
    collection_name: str,
    points: List[PointStruct],
    batch_size: int = 100,
    max_concurrent: int = 5
):
    """Upsert points in parallel batches"""

    # Split into batches
    batches = [
        points[i:i + batch_size]
        for i in range(0, len(points), batch_size)
    ]

    # Process batches with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)

    async def upsert_batch(batch, idx):
        async with semaphore:
            await client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True
            )
            print(f"✓ Batch {idx + 1}/{len(batches)} complete")

    await asyncio.gather(*[
        upsert_batch(batch, idx)
        for idx, batch in enumerate(batches)
    ])
```

---

## 4. Scroll API for Large Results

When you need to retrieve many results (>100), use the Scroll API instead of search.

### Basic Scroll

```python
# Get all Slack messages
offset = None
all_results = []

while True:
    result = client.scroll(
        collection_name="knowledge_base",
        scroll_filter=Filter(
            must=[
                FieldCondition(key="source", match=MatchValue(value="slack"))
            ]
        ),
        limit=100,
        offset=offset,
        with_payload=True,
        with_vectors=False  # Don't fetch vectors (faster)
    )

    points, offset = result
    all_results.extend(points)

    if offset is None:  # No more results
        break

print(f"Retrieved {len(all_results)} Slack messages")
```

### Scroll with Processing

```python
def process_all_points(
    client: QdrantClient,
    collection_name: str,
    filter_condition: Filter,
    process_fn: callable
):
    """Process all matching points without loading into memory"""

    offset = None
    total_processed = 0

    while True:
        result = client.scroll(
            collection_name=collection_name,
            scroll_filter=filter_condition,
            limit=100,
            offset=offset,
            with_payload=True
        )

        points, offset = result

        # Process batch
        for point in points:
            process_fn(point)
            total_processed += 1

        print(f"Processed {total_processed} points...")

        if offset is None:
            break

    return total_processed

# Example: Find all documents by a user
total = process_all_points(
    client,
    "knowledge_base",
    Filter(must=[FieldCondition(key="owner", match=MatchValue(value="user_123"))]),
    lambda point: print(point.payload["title"])
)
```

---

## 5. Recommendation Engine

Find similar documents based on vector similarity.

### Find Similar Documents

```python
def find_similar_documents(
    client: QdrantClient,
    document_id: str,
    limit: int = 10
) -> List[dict]:
    """Find documents similar to a given document"""

    # Get the document
    doc = client.retrieve(
        collection_name="knowledge_base",
        ids=[document_id],
        with_vectors=True
    )[0]

    # Search for similar documents
    results = client.search(
        collection_name="knowledge_base",
        query_vector=doc.vector,
        query_filter=Filter(
            must_not=[
                FieldCondition(key="id", match=MatchValue(value=document_id))
            ]
        ),
        limit=limit,
        with_payload=True,
        score_threshold=0.7
    )

    return results
```

### Recommend Based on User History

```python
def recommend_for_user(
    client: QdrantClient,
    user_id: str,
    limit: int = 10
) -> List[dict]:
    """Recommend documents based on user's query history"""

    # Get user's recent queries
    recent_queries = client.scroll(
        collection_name="conversations",
        scroll_filter=Filter(
            must=[FieldCondition(key="user_id", match=MatchValue(value=user_id))]
        ),
        limit=10,
        with_payload=True
    )[0]

    if not recent_queries:
        return []

    # Average embedding of recent queries
    query_embeddings = [q.payload["query_embedding"] for q in recent_queries]
    avg_embedding = [
        sum(emb[i] for emb in query_embeddings) / len(query_embeddings)
        for i in range(768)
    ]

    # Search for relevant documents
    results = client.search(
        collection_name="knowledge_base",
        query_vector=avg_embedding,
        limit=limit,
        with_payload=True,
        score_threshold=0.6
    )

    return results
```

### Find Similar Experts

```python
def find_experts_for_topic(
    client: QdrantClient,
    topic_embedding: List[float],
    limit: int = 5
) -> List[dict]:
    """Find experts for a given topic"""

    results = client.search(
        collection_name="expertise_map",
        query_vector=topic_embedding,
        limit=limit,
        with_payload=True,
        score_threshold=0.6
    )

    # Aggregate by user_id
    experts = {}
    for result in results:
        user_id = result.payload["user_id"]
        score = result.payload["expertise_score"]

        if user_id not in experts:
            experts[user_id] = {
                "user_id": user_id,
                "total_score": 0,
                "evidence": []
            }

        experts[user_id]["total_score"] += score
        experts[user_id]["evidence"].extend(result.payload["evidence"])

    # Sort by total score
    ranked_experts = sorted(
        experts.values(),
        key=lambda x: x["total_score"],
        reverse=True
    )

    return ranked_experts[:limit]
```

---

## 6. Performance Optimization

### Use Payload Indexes

Always index fields you'll filter on:

```python
# Create indexes for frequently filtered fields
indexes = ["source", "content_type", "permissions.sensitivity", "created_at", "tags"]

for field in indexes:
    client.create_payload_index(
        collection_name="knowledge_base",
        field_name=field,
        field_schema=PayloadSchemaType.KEYWORD  # or INTEGER, FLOAT
    )
```

### Optimize Vector Configuration

```python
# For speed: Keep in memory
vectors_config = VectorParams(
    size=768,
    distance=Distance.COSINE,
    on_disk=False  # In-memory (faster)
)

# For large collections: Use disk
vectors_config = VectorParams(
    size=768,
    distance=Distance.COSINE,
    on_disk=True  # On disk (saves memory)
)
```

### Adjust HNSW Parameters

```python
from qdrant_client.models import HnswConfigDiff

# For better recall (slower indexing)
client.update_collection(
    collection_name="knowledge_base",
    hnsw_config=HnswConfigDiff(
        m=32,  # Higher = better recall (default: 16)
        ef_construct=200  # Higher = better index quality (default: 100)
    )
)

# For faster search
client.update_collection(
    collection_name="knowledge_base",
    hnsw_config=HnswConfigDiff(
        ef=128  # Higher = better recall at search time (default: 64)
    )
)
```

### Use Score Threshold

```python
# Don't return low-quality results
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    limit=50,
    score_threshold=0.7  # Only results with >70% similarity
)
```

### Disable Unnecessary Features

```python
# Don't fetch vectors if you don't need them
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    limit=20,
    with_vectors=False  # Faster
)

# Don't fetch full payload if you only need specific fields
results = client.search(
    collection_name="knowledge_base",
    query_vector=query_embedding,
    limit=20,
    with_payload=["title", "url", "source"]  # Only these fields
)
```

---

## 7. Error Handling

### Connection Errors

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def search_with_retry(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float]
):
    """Search with automatic retry on failure"""
    try:
        return client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=20
        )
    except Exception as e:
        print(f"Search failed: {e}. Retrying...")
        raise
```

### Handle Collection Not Found

```python
from qdrant_client.http.exceptions import UnexpectedResponse

def safe_search(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float]
):
    """Search with collection existence check"""
    try:
        # Check if collection exists
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]

        if collection_name not in collection_names:
            print(f"Collection '{collection_name}' not found. Creating...")
            create_collection(client, collection_name)

        return client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=20
        )

    except UnexpectedResponse as e:
        print(f"Qdrant error: {e}")
        return []
```

### Batch Operation Errors

```python
def safe_batch_upsert(
    client: QdrantClient,
    collection_name: str,
    points: List[PointStruct],
    batch_size: int = 100
):
    """Batch upsert with per-batch error handling"""

    total = len(points)
    successful = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch = points[i:i + batch_size]

        try:
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True
            )
            successful += len(batch)
            print(f"✓ Batch {i//batch_size + 1} success ({successful}/{total})")

        except Exception as e:
            failed += len(batch)
            print(f"✗ Batch {i//batch_size + 1} failed: {e}")

            # Try individual points in failed batch
            for point in batch:
                try:
                    client.upsert(
                        collection_name=collection_name,
                        points=[point],
                        wait=True
                    )
                    successful += 1
                    failed -= 1
                except Exception as e2:
                    print(f"  ✗ Point {point.id} failed: {e2}")

    print(f"\nResults: {successful} successful, {failed} failed")
    return successful, failed
```

---

## 8. Complete QdrantService Class

Here's a complete service wrapper that implements all operations:

```python
from typing import List, Dict, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, Range, HnswConfigDiff,
    PayloadSchemaType, PayloadIndexInfo, OptimizersConfigDiff
)
import uuid


class QdrantService:
    """Complete Qdrant service for EngineIQ"""

    def __init__(self, url: str, api_key: Optional[str] = None):
        self.client = QdrantClient(url=url, api_key=api_key)
        self.collection_configs = {
            "knowledge_base": {
                "size": 768,
                "indexes": [
                    ("source", PayloadSchemaType.KEYWORD),
                    ("content_type", PayloadSchemaType.KEYWORD),
                    ("permissions.sensitivity", PayloadSchemaType.KEYWORD),
                    ("permissions.teams", PayloadSchemaType.KEYWORD),
                    ("permissions.public", PayloadSchemaType.BOOL),
                    ("permissions.offshore_restricted", PayloadSchemaType.BOOL),
                    ("permissions.third_party_restricted", PayloadSchemaType.BOOL),
                    ("created_at", PayloadSchemaType.INTEGER),
                    ("tags", PayloadSchemaType.KEYWORD),
                    ("owner", PayloadSchemaType.KEYWORD)
                ]
            },
            "conversations": {
                "size": 768,
                "indexes": [
                    ("user_id", PayloadSchemaType.KEYWORD),
                    ("timestamp", PayloadSchemaType.INTEGER),
                    ("top_result_score", PayloadSchemaType.FLOAT)
                ]
            },
            "expertise_map": {
                "size": 768,
                "indexes": [
                    ("user_id", PayloadSchemaType.KEYWORD),
                    ("expertise_score", PayloadSchemaType.FLOAT),
                    ("tags", PayloadSchemaType.KEYWORD)
                ]
            },
            "knowledge_gaps": {
                "size": 768,
                "indexes": [
                    ("priority", PayloadSchemaType.KEYWORD),
                    ("status", PayloadSchemaType.KEYWORD),
                    ("search_count", PayloadSchemaType.INTEGER)
                ]
            }
        }

    def initialize_collections(self):
        """Create all collections with proper configuration"""
        for collection_name, config in self.collection_configs.items():
            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=Distance.COSINE,
                    on_disk=False
                ),
                optimizers_config=OptimizersConfigDiff(
                    default_segment_number=2,
                    indexing_threshold=20000
                ),
                replication_factor=2
            )

            # Create payload indexes
            for field_name, field_schema in config["indexes"]:
                self.client.create_payload_index(
                    collection_name=collection_name,
                    field_name=field_name,
                    field_schema=field_schema
                )

            print(f"✓ Created collection: {collection_name}")

    def upsert(
        self,
        collection_name: str,
        points: List[PointStruct],
        batch_size: int = 100
    ):
        """Batch upsert with chunking"""
        total = len(points)

        for i in range(0, total, batch_size):
            batch = points[i:i + batch_size]
            self.client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True
            )

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 20,
        score_threshold: float = 0.5,
        query_filter: Optional[Filter] = None,
        with_payload: Union[bool, List[str]] = True,
        with_vectors: bool = False
    ):
        """Search with filters"""
        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def search_with_permissions(
        self,
        query_vector: List[float],
        user: dict,
        limit: int = 20,
        additional_filters: Optional[List[FieldCondition]] = None
    ):
        """Permission-aware search"""
        should_conditions = [
            FieldCondition(key="permissions.public", match=MatchValue(value=True))
        ]

        if user.get("teams"):
            should_conditions.append(
                FieldCondition(
                    key="permissions.teams",
                    match=MatchValue(any=user["teams"])
                )
            )

        should_conditions.append(
            FieldCondition(
                key="permissions.users",
                match=MatchValue(any=[user["id"]])
            )
        )

        should_conditions.append(
            FieldCondition(key="owner", match=MatchValue(value=user["id"]))
        )

        must_not_conditions = []
        if user.get("offshore"):
            must_not_conditions.append(
                FieldCondition(
                    key="permissions.offshore_restricted",
                    match=MatchValue(value=True)
                )
            )

        if user.get("third_party"):
            must_not_conditions.append(
                FieldCondition(
                    key="permissions.third_party_restricted",
                    match=MatchValue(value=True)
                )
            )

        must_conditions = additional_filters or []

        query_filter = Filter(
            must=must_conditions,
            should=should_conditions,
            must_not=must_not_conditions
        )

        return self.search(
            collection_name="knowledge_base",
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit
        )

    def scroll(
        self,
        collection_name: str,
        scroll_filter: Optional[Filter] = None,
        limit: int = 100,
        offset: Optional[str] = None,
        with_payload: bool = True,
        with_vectors: bool = False
    ):
        """Scroll through results"""
        return self.client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def retrieve(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False
    ):
        """Retrieve specific points by ID"""
        return self.client.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def delete(
        self,
        collection_name: str,
        points_selector: Union[List[str], Filter]
    ):
        """Delete points by IDs or filter"""
        self.client.delete(
            collection_name=collection_name,
            points_selector=points_selector
        )
```

---

## Summary

This skill covers all Qdrant operations needed for EngineIQ:
- ✅ 4 collection schemas with proper indexing
- ✅ Hybrid search (vector + metadata)
- ✅ Batch operations for performance
- ✅ Permission-aware filtering
- ✅ Scroll API for large results
- ✅ Recommendations and similarity search
- ✅ Performance optimization
- ✅ Comprehensive error handling

See `examples/` for complete working code.
