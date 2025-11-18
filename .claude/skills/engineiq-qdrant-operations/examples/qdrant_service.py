"""
EngineIQ Qdrant Service - Complete Implementation

Provides all Qdrant operations for EngineIQ with proper error handling,
performance optimization, and permission-aware filtering.
"""

from typing import List, Dict, Optional, Union
from qdrant_client import QdrantClient, AsyncQdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter,
    FieldCondition, MatchValue, Range, HnswConfigDiff,
    PayloadSchemaType, PayloadIndexInfo, OptimizersConfigDiff
)
from tenacity import retry, stop_after_attempt, wait_exponential
import uuid
import time


class QdrantService:
    """
    Complete Qdrant service for EngineIQ.

    Handles all operations across 4 collections:
    - knowledge_base: Primary search collection
    - conversations: Query tracking
    - expertise_map: Expert finding
    - knowledge_gaps: Gap detection
    """

    def __init__(self, url: str, api_key: Optional[str] = None):
        """
        Initialize Qdrant service.

        Args:
            url: Qdrant server URL
            api_key: API key for Qdrant Cloud (optional)
        """
        self.client = QdrantClient(url=url, api_key=api_key)

        # Collection configurations
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

    def initialize_collections(self, recreate: bool = False):
        """
        Create all EngineIQ collections with proper configuration.

        Args:
            recreate: If True, delete existing collections and recreate
        """
        for collection_name, config in self.collection_configs.items():
            # Check if collection exists
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if collection_name in collection_names:
                if recreate:
                    print(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    print(f"✓ Collection already exists: {collection_name}")
                    continue

            # Create collection
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=Distance.COSINE,
                    on_disk=False  # Keep in memory for speed
                ),
                optimizers_config=OptimizersConfigDiff(
                    default_segment_number=2,
                    indexing_threshold=20000,
                    memmap_threshold=50000
                ),
                replication_factor=2 if "cloud" in self.client._client._base_url else 1
            )

            # Create payload indexes
            for field_name, field_schema in config["indexes"]:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_schema
                    )
                except Exception as e:
                    print(f"  Warning: Could not create index {field_name}: {e}")

            print(f"✓ Created collection: {collection_name}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def upsert(
        self,
        collection_name: str,
        points: List[Union[PointStruct, Dict]],
        batch_size: int = 100,
        show_progress: bool = True
    ) -> int:
        """
        Batch upsert with automatic chunking and retry.

        Args:
            collection_name: Target collection
            points: List of PointStruct or dicts with id, vector, payload
            batch_size: Points per batch (default: 100)
            show_progress: Print progress (default: True)

        Returns:
            int: Number of points indexed
        """
        # Convert dicts to PointStruct if needed
        if points and isinstance(points[0], dict):
            points = [
                PointStruct(
                    id=p.get("id", str(uuid.uuid4())),
                    vector=p["vector"],
                    payload=p["payload"]
                )
                for p in points
            ]

        total = len(points)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = points[i:i + batch_size]

            self.client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True
            )

            indexed += len(batch)

            if show_progress:
                print(f"  ✓ Indexed {indexed}/{total} points")

        return indexed

    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 20,
        score_threshold: float = 0.5,
        query_filter: Optional[Filter] = None,
        with_payload: Union[bool, List[str]] = True,
        with_vectors: bool = False
    ) -> List:
        """
        Vector similarity search with optional filters.

        Args:
            collection_name: Collection to search
            query_vector: 768-dim embedding vector
            limit: Maximum results (default: 20)
            score_threshold: Minimum similarity score (default: 0.5)
            query_filter: Metadata filters (optional)
            with_payload: Return payload (True/False/list of fields)
            with_vectors: Return vectors (default: False)

        Returns:
            List of search results with scores and payloads
        """
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
        additional_filters: Optional[List[FieldCondition]] = None,
        score_threshold: float = 0.5
    ) -> List:
        """
        Permission-aware search for knowledge_base.

        Automatically filters results based on user permissions:
        - Public documents
        - User's teams
        - Documents user owns
        - Offshore restrictions
        - Third-party restrictions

        Args:
            query_vector: 768-dim query embedding
            user: User dict with id, teams, offshore, third_party
            limit: Maximum results
            additional_filters: Extra filters (source, date, etc.)
            score_threshold: Minimum similarity score

        Returns:
            List of permitted search results

        Example:
            user = {
                "id": "user_123",
                "teams": ["engineering", "product"],
                "offshore": False,
                "third_party": False
            }
            results = service.search_with_permissions(embedding, user, limit=10)
        """
        # Build "should" conditions (OR logic - user has access if any match)
        should_conditions = [
            # Public documents
            FieldCondition(
                key="permissions.public",
                match=MatchValue(value=True)
            )
        ]

        # User is in teams
        if user.get("teams"):
            should_conditions.append(
                FieldCondition(
                    key="permissions.teams",
                    match=MatchValue(any=user["teams"])
                )
            )

        # User explicitly listed
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

        # Build "must_not" conditions (restrictions)
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

        # Build "must" conditions (additional filters)
        must_conditions = additional_filters or []

        # Combine into filter
        query_filter = Filter(
            must=must_conditions,
            should=should_conditions,
            must_not=must_not_conditions
        )

        return self.search(
            collection_name="knowledge_base",
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )

    def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        must: Optional[List[FieldCondition]] = None,
        should: Optional[List[FieldCondition]] = None,
        must_not: Optional[List[FieldCondition]] = None,
        limit: int = 20,
        score_threshold: float = 0.5
    ) -> List:
        """
        Hybrid search combining vector similarity and metadata filters.

        Args:
            collection_name: Collection to search
            query_vector: 768-dim embedding
            must: Conditions that MUST match (AND logic)
            should: Conditions that SHOULD match (OR logic)
            must_not: Conditions that MUST NOT match
            limit: Maximum results
            score_threshold: Minimum similarity

        Returns:
            List of results

        Example:
            # Search for Slack messages from last week about kubernetes
            import time
            one_week_ago = int(time.time()) - (7 * 86400)

            results = service.hybrid_search(
                "knowledge_base",
                query_embedding,
                must=[
                    FieldCondition(key="source", match=MatchValue(value="slack")),
                    FieldCondition(key="created_at", range=Range(gte=one_week_ago)),
                    FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
                ],
                limit=50
            )
        """
        query_filter = Filter(
            must=must or [],
            should=should or [],
            must_not=must_not or []
        )

        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold
        )

    def scroll(
        self,
        collection_name: str,
        scroll_filter: Optional[Filter] = None,
        limit: int = 100,
        offset: Optional[str] = None,
        with_payload: Union[bool, List[str]] = True,
        with_vectors: bool = False
    ):
        """
        Scroll through large result sets.

        Use this instead of search when you need >100 results.

        Args:
            collection_name: Collection to scroll
            scroll_filter: Filter conditions
            limit: Points per page (default: 100)
            offset: Pagination offset (None for first page)
            with_payload: Return payloads
            with_vectors: Return vectors

        Returns:
            Tuple of (points, next_offset)

        Example:
            # Get all Slack messages
            offset = None
            all_messages = []

            while True:
                points, offset = service.scroll(
                    "knowledge_base",
                    scroll_filter=Filter(
                        must=[FieldCondition(key="source", match=MatchValue(value="slack"))]
                    ),
                    limit=100,
                    offset=offset
                )

                all_messages.extend(points)

                if offset is None:
                    break
        """
        return self.client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

    def scroll_all(
        self,
        collection_name: str,
        scroll_filter: Optional[Filter] = None,
        batch_size: int = 100,
        process_fn: Optional[callable] = None
    ) -> List:
        """
        Scroll through all matching points.

        Args:
            collection_name: Collection to scroll
            scroll_filter: Filter conditions
            batch_size: Points per batch
            process_fn: Optional function to process each point

        Returns:
            List of all points (if process_fn is None)

        Example:
            # Count all GitHub code files
            count = 0
            service.scroll_all(
                "knowledge_base",
                scroll_filter=Filter(must=[
                    FieldCondition(key="source", match=MatchValue(value="github")),
                    FieldCondition(key="content_type", match=MatchValue(value="code"))
                ]),
                process_fn=lambda p: count += 1
            )
        """
        offset = None
        all_points = [] if process_fn is None else None

        while True:
            points, offset = self.scroll(
                collection_name=collection_name,
                scroll_filter=scroll_filter,
                limit=batch_size,
                offset=offset
            )

            if process_fn:
                for point in points:
                    process_fn(point)
            else:
                all_points.extend(points)

            if offset is None:
                break

        return all_points

    def retrieve(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List:
        """
        Retrieve specific points by ID.

        Args:
            collection_name: Collection name
            ids: List of point IDs
            with_payload: Return payloads
            with_vectors: Return vectors

        Returns:
            List of points
        """
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
        """
        Delete points by IDs or filter.

        Args:
            collection_name: Collection name
            points_selector: List of IDs or Filter

        Example:
            # Delete by IDs
            service.delete("knowledge_base", ["id1", "id2", "id3"])

            # Delete by filter
            service.delete(
                "knowledge_base",
                Filter(must=[FieldCondition(key="source", match=MatchValue(value="slack"))])
            )
        """
        self.client.delete(
            collection_name=collection_name,
            points_selector=points_selector
        )

    def find_similar_documents(
        self,
        document_id: str,
        limit: int = 10,
        score_threshold: float = 0.7
    ) -> List:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of reference document
            limit: Maximum similar documents
            score_threshold: Minimum similarity

        Returns:
            List of similar documents

        Example:
            similar = service.find_similar_documents("slack_C123_1234567890", limit=5)
        """
        # Get the document with its vector
        doc = self.retrieve(
            collection_name="knowledge_base",
            ids=[document_id],
            with_vectors=True
        )

        if not doc:
            return []

        # Search for similar documents (exclude the original)
        return self.search(
            collection_name="knowledge_base",
            query_vector=doc[0].vector,
            query_filter=Filter(
                must_not=[
                    FieldCondition(key="id", match=MatchValue(value=document_id))
                ]
            ),
            limit=limit,
            score_threshold=score_threshold
        )

    def find_experts(
        self,
        topic_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.6
    ) -> List[Dict]:
        """
        Find experts for a topic based on expertise_map.

        Args:
            topic_embedding: 768-dim embedding of topic
            limit: Maximum experts to return
            score_threshold: Minimum expertise score

        Returns:
            List of experts with aggregated scores and evidence

        Example:
            experts = service.find_experts(kubernetes_embedding, limit=3)
            # Returns: [
            #   {
            #     "user_id": "alice",
            #     "total_score": 87.5,
            #     "evidence": [...]
            #   },
            #   ...
            # ]
        """
        # Search expertise_map
        results = self.search(
            collection_name="expertise_map",
            query_vector=topic_embedding,
            limit=limit * 2,  # Get more results for aggregation
            score_threshold=score_threshold
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

    def detect_knowledge_gap(
        self,
        query_embedding: List[float],
        query_text: str,
        user_id: str
    ) -> Optional[str]:
        """
        Check if query represents a knowledge gap and update gap tracking.

        Args:
            query_embedding: 768-dim query embedding
            query_text: Original query text
            user_id: User who made the query

        Returns:
            Gap ID if gap detected/updated, None otherwise
        """
        # Search for similar queries in conversations
        similar_queries = self.search(
            collection_name="conversations",
            query_vector=query_embedding,
            limit=20,
            score_threshold=0.8  # Very similar queries
        )

        # If 10+ similar queries with low result quality
        if len(similar_queries) >= 10:
            avg_score = sum(
                q.payload["top_result_score"] for q in similar_queries
            ) / len(similar_queries)

            if avg_score < 0.4:  # Poor results
                # This is a knowledge gap
                gap_id = f"gap_{hash(query_text)}"

                # Check if gap already exists
                existing = self.retrieve(
                    collection_name="knowledge_gaps",
                    ids=[gap_id]
                )

                if existing:
                    # Update existing gap
                    gap_data = existing[0].payload
                    gap_data["search_count"] += 1
                    gap_data["unique_users"].append(user_id)
                    gap_data["unique_users"] = list(set(gap_data["unique_users"]))
                    gap_data["last_searched"] = int(time.time())
                else:
                    # Create new gap
                    gap_data = {
                        "query_pattern": query_text,
                        "search_count": len(similar_queries),
                        "unique_users": list(set([q.payload["user_id"] for q in similar_queries])),
                        "avg_result_score": avg_score,
                        "first_detected": int(time.time()),
                        "last_searched": int(time.time()),
                        "priority": "high" if len(similar_queries) > 15 else "medium",
                        "suggested_action": f"Create documentation on: {query_text}",
                        "status": "detected",
                        "related_docs": []
                    }

                # Upsert gap
                self.upsert(
                    collection_name="knowledge_gaps",
                    points=[{
                        "id": gap_id,
                        "vector": query_embedding,
                        "payload": gap_data
                    }],
                    show_progress=False
                )

                return gap_id

        return None

    def get_collection_stats(self, collection_name: str) -> Dict:
        """
        Get statistics for a collection.

        Args:
            collection_name: Collection name

        Returns:
            Dict with collection stats
        """
        info = self.client.get_collection(collection_name)

        return {
            "name": collection_name,
            "points_count": info.points_count,
            "vectors_count": info.vectors_count,
            "indexed_vectors_count": info.indexed_vectors_count,
            "status": info.status
        }

    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            collections = self.client.get_collections()
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Initialize service
    service = QdrantService(
        url="http://localhost:6333",  # or Qdrant Cloud URL
        api_key=None  # Add API key for Qdrant Cloud
    )

    # Create all collections
    service.initialize_collections()

    # Check stats
    for collection in ["knowledge_base", "conversations", "expertise_map", "knowledge_gaps"]:
        stats = service.get_collection_stats(collection)
        print(f"\n{collection}:")
        print(f"  Points: {stats['points_count']}")
        print(f"  Status: {stats['status']}")
