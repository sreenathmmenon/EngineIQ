"""
EngineIQ Qdrant Service - Complete Implementation

Provides all Qdrant operations for EngineIQ with proper error handling,
performance optimization, and permission-aware filtering.
"""

from typing import List, Dict, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
    HnswConfigDiff,
    PayloadSchemaType,
    OptimizersConfigDiff,
)
from tenacity import retry, stop_after_attempt, wait_exponential
import uuid
import time
import logging
from datetime import datetime

from ..config.qdrant_config import QdrantConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QdrantService:
    """
    Complete Qdrant service for EngineIQ.

    Handles all operations across 4 collections:
    - knowledge_base: Primary search collection
    - conversations: Query tracking
    - expertise_map: Expert finding
    - knowledge_gaps: Gap detection
    """

    def __init__(
        self,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[QdrantConfig] = None,
    ):
        """
        Initialize Qdrant service.

        Args:
            url: Qdrant server URL (defaults to config)
            api_key: API key for Qdrant Cloud (defaults to config)
            config: QdrantConfig instance (optional)
        """
        self.config = config or QdrantConfig()
        self.url = url or self.config.QDRANT_URL
        self.api_key = api_key or self.config.QDRANT_API_KEY

        self.client = QdrantClient(url=self.url, api_key=self.api_key)
        logger.info(f"Initialized QdrantService connected to {self.url}")

    def initialize_collections(self, recreate: bool = False):
        """
        Create all EngineIQ collections with proper configuration.

        Args:
            recreate: If True, delete existing collections and recreate
        """
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        for collection_name, config in self.config.COLLECTION_CONFIGS.items():
            if collection_name in collection_names:
                if recreate:
                    logger.info(f"Deleting existing collection: {collection_name}")
                    self.client.delete_collection(collection_name)
                else:
                    logger.info(f"✓ Collection already exists: {collection_name}")
                    continue

            # Create collection
            logger.info(f"Creating collection: {collection_name}")
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=config["size"],
                    distance=Distance.COSINE,
                    on_disk=False,
                ),
                optimizers_config=OptimizersConfigDiff(
                    default_segment_number=self.config.DEFAULT_SEGMENT_NUMBER,
                    indexing_threshold=self.config.INDEXING_THRESHOLD,
                    memmap_threshold=self.config.MEMMAP_THRESHOLD,
                ),
                replication_factor=2 if "cloud" in self.url else 1,
            )

            # Create payload indexes
            for field_name, field_schema in config["indexes"]:
                try:
                    self.client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_schema,
                    )
                    logger.info(f"  ✓ Created index: {field_name}")
                except Exception as e:
                    logger.warning(f"  Could not create index {field_name}: {e}")

            logger.info(f"✓ Created collection: {collection_name}")

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def index_document(
        self, collection_name: str, doc_id: str, vector: List[float], payload: Dict
    ) -> bool:
        """
        Index a single document.

        Args:
            collection_name: Target collection
            doc_id: Unique document ID
            vector: 768-dim embedding vector
            payload: Document metadata

        Returns:
            bool: True if successful
        """
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[
                    PointStruct(
                        id=doc_id,
                        vector=vector,
                        payload=payload,
                    )
                ],
                wait=True,
            )
            return True
        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    def batch_index(
        self,
        collection_name: str,
        points: List[Union[PointStruct, Dict]],
        batch_size: Optional[int] = None,
        show_progress: bool = True,
    ) -> int:
        """
        Batch index with automatic chunking and retry.

        Args:
            collection_name: Target collection
            points: List of PointStruct or dicts with id, vector, payload
            batch_size: Points per batch (defaults to config)
            show_progress: Print progress

        Returns:
            int: Number of points indexed
        """
        batch_size = batch_size or self.config.DEFAULT_BATCH_SIZE

        # Convert dicts to PointStruct if needed
        if points and isinstance(points[0], dict):
            points = [
                PointStruct(
                    id=p.get("id", str(uuid.uuid4())),
                    vector=p["vector"],
                    payload=p["payload"],
                )
                for p in points
            ]

        total = len(points)
        indexed = 0

        for i in range(0, total, batch_size):
            batch = points[i : i + batch_size]

            try:
                self.client.upsert(
                    collection_name=collection_name, points=batch, wait=True
                )

                indexed += len(batch)

                if show_progress:
                    logger.info(f"  ✓ Indexed {indexed}/{total} points")

            except Exception as e:
                logger.error(f"Batch indexing failed at {i}-{i+batch_size}: {e}")
                raise

        return indexed

    def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        must: Optional[List[FieldCondition]] = None,
        should: Optional[List[FieldCondition]] = None,
        must_not: Optional[List[FieldCondition]] = None,
        limit: Optional[int] = None,
        score_threshold: Optional[float] = None,
        with_payload: Union[bool, List[str]] = True,
        with_vectors: bool = False,
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
            with_payload: Return payloads
            with_vectors: Return vectors

        Returns:
            List of results

        Example:
            results = service.hybrid_search(
                "knowledge_base",
                query_embedding,
                must=[
                    FieldCondition(key="source", match=MatchValue(value="slack")),
                    FieldCondition(key="created_at", range=Range(gte=one_week_ago))
                ],
                limit=50
            )
        """
        limit = limit or self.config.DEFAULT_SEARCH_LIMIT
        score_threshold = score_threshold or self.config.DEFAULT_SCORE_THRESHOLD

        query_filter = Filter(
            must=must or [], should=should or [], must_not=must_not or []
        )

        return self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

    def filter_by_permissions(
        self,
        query_vector: List[float],
        user: Dict,
        additional_filters: Optional[List[FieldCondition]] = None,
        limit: Optional[int] = None,
        score_threshold: Optional[float] = None,
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
            additional_filters: Extra filters (source, date, etc.)
            limit: Maximum results
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
            results = service.filter_by_permissions(embedding, user, limit=10)
        """
        limit = limit or self.config.DEFAULT_SEARCH_LIMIT
        score_threshold = score_threshold or self.config.DEFAULT_SCORE_THRESHOLD

        # Build "should" conditions (OR logic - user has access if any match)
        should_conditions = [
            FieldCondition(key="permissions.public", match=MatchValue(value=True))
        ]

        if user.get("teams"):
            should_conditions.append(
                FieldCondition(
                    key="permissions.teams", match=MatchValue(any=user["teams"])
                )
            )

        should_conditions.append(
            FieldCondition(
                key="permissions.users", match=MatchValue(any=[user["id"]])
            )
        )

        should_conditions.append(
            FieldCondition(key="owner", match=MatchValue(value=user["id"]))
        )

        # Build "must_not" conditions (restrictions)
        must_not_conditions = []

        if user.get("offshore"):
            must_not_conditions.append(
                FieldCondition(
                    key="permissions.offshore_restricted", match=MatchValue(value=True)
                )
            )

        if user.get("third_party"):
            must_not_conditions.append(
                FieldCondition(
                    key="permissions.third_party_restricted",
                    match=MatchValue(value=True),
                )
            )

        # Build "must" conditions (additional filters)
        must_conditions = additional_filters or []

        return self.hybrid_search(
            collection_name="knowledge_base",
            query_vector=query_vector,
            must=must_conditions,
            should=should_conditions,
            must_not=must_not_conditions,
            limit=limit,
            score_threshold=score_threshold,
        )

    def get_similar_documents(
        self,
        document_id: str,
        limit: int = 10,
        score_threshold: Optional[float] = None,
        user: Optional[Dict] = None,
    ) -> List:
        """
        Find documents similar to a given document.

        Args:
            document_id: ID of reference document
            limit: Maximum similar documents
            score_threshold: Minimum similarity
            user: Optional user dict for permission filtering

        Returns:
            List of similar documents
        """
        score_threshold = score_threshold or self.config.HIGH_QUALITY_THRESHOLD

        # Get the document with its vector
        try:
            doc = self.client.retrieve(
                collection_name="knowledge_base",
                ids=[document_id],
                with_vectors=True,
            )
        except Exception as e:
            logger.error(f"Failed to retrieve document {document_id}: {e}")
            return []

        if not doc:
            logger.warning(f"Document not found: {document_id}")
            return []

        # Build exclusion filter
        must_not = [FieldCondition(key="id", match=MatchValue(value=document_id))]

        # If user provided, apply permission filtering
        if user:
            return self.filter_by_permissions(
                query_vector=doc[0].vector,
                user=user,
                additional_filters=[],
                limit=limit,
                score_threshold=score_threshold,
            )
        else:
            return self.hybrid_search(
                collection_name="knowledge_base",
                query_vector=doc[0].vector,
                must_not=must_not,
                limit=limit,
                score_threshold=score_threshold,
            )

    def get_expertise_data(
        self,
        topic_embedding: List[float],
        limit: int = 5,
        score_threshold: float = 0.6,
    ) -> List[Dict]:
        """
        Find experts for a topic based on expertise_map.

        Args:
            topic_embedding: 768-dim embedding of topic
            limit: Maximum experts to return
            score_threshold: Minimum expertise similarity

        Returns:
            List of experts with aggregated scores and evidence
        """
        # Search expertise_map
        results = self.client.search(
            collection_name="expertise_map",
            query_vector=topic_embedding,
            limit=limit * 2,
            score_threshold=score_threshold,
        )

        # Aggregate by user_id
        experts = {}
        for result in results:
            user_id = result.payload["user_id"]
            score = result.payload["expertise_score"]

            if user_id not in experts:
                experts[user_id] = {
                    "user_id": user_id,
                    "user_name": result.payload.get("user_name", user_id),
                    "total_score": 0,
                    "evidence": [],
                    "topics": [],
                }

            experts[user_id]["total_score"] += score
            experts[user_id]["evidence"].extend(result.payload.get("evidence", []))
            experts[user_id]["topics"].append(result.payload.get("topic"))

        # Sort by total score
        ranked_experts = sorted(
            experts.values(), key=lambda x: x["total_score"], reverse=True
        )

        return ranked_experts[:limit]

    def detect_knowledge_gaps(
        self,
        query_embedding: List[float],
        query_text: str,
        user_id: str,
        result_score: float,
    ) -> Optional[str]:
        """
        Check if query represents a knowledge gap and update gap tracking.

        Args:
            query_embedding: 768-dim query embedding
            query_text: Original query text
            user_id: User who made the query
            result_score: Quality of results (0-1)

        Returns:
            Gap ID if gap detected/updated, None otherwise
        """
        # Search for similar queries in conversations
        similar_queries = self.client.search(
            collection_name="conversations",
            query_vector=query_embedding,
            limit=20,
            score_threshold=0.8,
        )

        # If sufficient similar queries with low result quality
        if len(similar_queries) >= self.config.GAP_MIN_SEARCH_COUNT:
            scores = [q.payload.get("top_result_score", 0) for q in similar_queries]
            avg_score = sum(scores) / len(scores) if scores else 0

            if avg_score < self.config.GAP_MAX_AVG_SCORE:
                # This is a knowledge gap
                gap_id = f"gap_{abs(hash(query_text)) % 10**9}"

                # Check if gap already exists
                try:
                    existing = self.client.retrieve(
                        collection_name="knowledge_gaps", ids=[gap_id]
                    )
                except:
                    existing = []

                now = int(time.time())

                if existing:
                    # Update existing gap
                    gap_data = existing[0].payload
                    gap_data["query_count"] += 1
                    gap_data["query_patterns"].append(query_text)
                    gap_data["last_query"] = now

                    # Recalculate priority
                    unique_users = len(
                        set(gap_data.get("unique_users", []) + [user_id])
                    )
                    if unique_users > self.config.GAP_HIGH_PRIORITY_USER_COUNT:
                        gap_data["priority"] = "high"
                else:
                    # Create new gap
                    unique_users = list(
                        set([q.payload["user_id"] for q in similar_queries])
                    )
                    gap_data = {
                        "topic": query_text,
                        "query_patterns": [query_text],
                        "query_count": len(similar_queries),
                        "unique_users": unique_users,
                        "avg_result_quality": avg_score,
                        "first_detected": now,
                        "last_query": now,
                        "priority": (
                            "high"
                            if len(unique_users)
                            > self.config.GAP_HIGH_PRIORITY_USER_COUNT
                            else "medium"
                        ),
                        "suggested_action": f"Create documentation on: {query_text}",
                        "suggested_owner": None,
                        "status": "detected",
                        "related_docs": [],
                    }

                # Upsert gap
                self.client.upsert(
                    collection_name="knowledge_gaps",
                    points=[
                        PointStruct(
                            id=gap_id, vector=query_embedding, payload=gap_data
                        )
                    ],
                    wait=True,
                )

                logger.info(f"Knowledge gap detected/updated: {gap_id}")
                return gap_id

        return None

    def scroll_all(
        self,
        collection_name: str,
        scroll_filter: Optional[Filter] = None,
        batch_size: int = 100,
        process_fn: Optional[callable] = None,
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
        """
        offset = None
        all_points = [] if process_fn is None else None
        total_processed = 0

        while True:
            points, offset = self.client.scroll(
                collection_name=collection_name,
                scroll_filter=scroll_filter,
                limit=batch_size,
                offset=offset,
            )

            if process_fn:
                for point in points:
                    process_fn(point)
                    total_processed += 1
            else:
                all_points.extend(points)

            if offset is None:
                break

        if process_fn:
            logger.info(f"Processed {total_processed} points")

        return all_points

    def retrieve(
        self,
        collection_name: str,
        ids: List[str],
        with_payload: bool = True,
        with_vectors: bool = False,
    ) -> List:
        """Retrieve specific points by ID"""
        return self.client.retrieve(
            collection_name=collection_name,
            ids=ids,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

    def delete(
        self, collection_name: str, points_selector: Union[List[str], Filter]
    ):
        """
        Delete points by IDs or filter.

        Args:
            collection_name: Collection name
            points_selector: List of IDs or Filter
        """
        self.client.delete(
            collection_name=collection_name, points_selector=points_selector
        )

    def get_collection_stats(self, collection_name: str) -> Dict:
        """Get statistics for a collection"""
        try:
            info = self.client.get_collection(collection_name)

            return {
                "name": collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "indexed_vectors_count": info.indexed_vectors_count,
                "status": info.status,
            }
        except Exception as e:
            logger.error(f"Failed to get stats for {collection_name}: {e}")
            return {
                "name": collection_name,
                "error": str(e),
            }

    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            collections = self.client.get_collections()
            logger.info(f"Health check passed: {len(collections.collections)} collections")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def log_conversation(
        self,
        user_id: str,
        query: str,
        query_embedding: List[float],
        results: List,
        response_time_ms: int,
        clicked_results: Optional[List[str]] = None,
        user_rating: Optional[int] = None,
        triggered_approval: bool = False,
        approval_granted: Optional[bool] = None,
    ) -> str:
        """
        Log a conversation for tracking and gap detection.

        Args:
            user_id: User who made the query
            query: Query text
            query_embedding: Query embedding vector
            results: Search results
            response_time_ms: Response time in milliseconds
            clicked_results: List of clicked result IDs
            user_rating: User rating (1-5)
            triggered_approval: Did this trigger human-in-loop?
            approval_granted: Was approval granted?

        Returns:
            Conversation ID
        """
        conversation_id = str(uuid.uuid4())

        # Extract sources from results
        sources_used = list(set([r.payload.get("source") for r in results if r.payload]))

        # Get top result score
        top_result_score = results[0].score if results else 0.0

        payload = {
            "user_id": user_id,
            "query": query,
            "results_count": len(results),
            "top_result_score": top_result_score,
            "sources_used": sources_used,
            "clicked_results": clicked_results or [],
            "user_rating": user_rating,
            "timestamp": int(time.time()),
            "response_time_ms": response_time_ms,
            "triggered_approval": triggered_approval,
            "approval_granted": approval_granted,
        }

        self.client.upsert(
            collection_name="conversations",
            points=[
                PointStruct(
                    id=conversation_id, vector=query_embedding, payload=payload
                )
            ],
            wait=True,
        )

        # Check for knowledge gaps
        self.detect_knowledge_gaps(
            query_embedding=query_embedding,
            query_text=query,
            user_id=user_id,
            result_score=top_result_score,
        )

        return conversation_id


# Example usage
if __name__ == "__main__":
    # Initialize service
    service = QdrantService()

    # Create all collections
    service.initialize_collections()

    # Check health
    if service.health_check():
        print("✓ Qdrant service is healthy")

    # Get stats for all collections
    for collection in QdrantConfig.get_collection_names():
        stats = service.get_collection_stats(collection)
        print(f"\n{collection}:")
        print(f"  Points: {stats.get('points_count', 'N/A')}")
        print(f"  Status: {stats.get('status', 'N/A')}")
