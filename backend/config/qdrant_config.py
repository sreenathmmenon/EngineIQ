"""
EngineIQ Qdrant Configuration

Configuration settings for Qdrant vector database connection and collections.
"""

import os
from typing import Dict, List, Tuple
from qdrant_client.models import PayloadSchemaType


class QdrantConfig:
    """Configuration for Qdrant connection and collections"""

    # Connection settings
    QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

    # Embedding settings
    EMBEDDING_MODEL = "gemini-text-embedding-004"
    EMBEDDING_DIMENSION = 768

    # Performance settings
    DEFAULT_BATCH_SIZE = 100
    MAX_CONCURRENT_BATCHES = 5
    DEFAULT_SEGMENT_NUMBER = 2
    INDEXING_THRESHOLD = 20000
    MEMMAP_THRESHOLD = 50000

    # Search settings
    DEFAULT_SEARCH_LIMIT = 20
    DEFAULT_SCORE_THRESHOLD = 0.5
    HIGH_QUALITY_THRESHOLD = 0.7

    # Collection configurations
    COLLECTION_CONFIGS: Dict[str, Dict] = {
        "knowledge_base": {
            "description": "Primary search collection for all indexed content",
            "size": EMBEDDING_DIMENSION,
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
                ("owner", PayloadSchemaType.KEYWORD),
            ],
        },
        "conversations": {
            "description": "Query tracking for learning patterns",
            "size": EMBEDDING_DIMENSION,
            "indexes": [
                ("user_id", PayloadSchemaType.KEYWORD),
                ("timestamp", PayloadSchemaType.INTEGER),
                ("top_result_score", PayloadSchemaType.FLOAT),
                ("triggered_approval", PayloadSchemaType.BOOL),
            ],
        },
        "expertise_map": {
            "description": "Expert finding based on contributions",
            "size": EMBEDDING_DIMENSION,
            "indexes": [
                ("user_id", PayloadSchemaType.KEYWORD),
                ("expertise_score", PayloadSchemaType.FLOAT),
                ("tags", PayloadSchemaType.KEYWORD),
                ("last_contribution", PayloadSchemaType.INTEGER),
            ],
        },
        "knowledge_gaps": {
            "description": "Proactive gap detection",
            "size": EMBEDDING_DIMENSION,
            "indexes": [
                ("priority", PayloadSchemaType.KEYWORD),
                ("status", PayloadSchemaType.KEYWORD),
                ("search_count", PayloadSchemaType.INTEGER),
                ("avg_result_score", PayloadSchemaType.FLOAT),
            ],
        },
    }

    # Permission sensitivity levels
    SENSITIVITY_LEVELS = ["public", "internal", "confidential", "restricted"]

    # Knowledge gap detection thresholds
    GAP_MIN_SEARCH_COUNT = 10
    GAP_MAX_AVG_SCORE = 0.4
    GAP_DETECTION_WINDOW_DAYS = 7
    GAP_HIGH_PRIORITY_USER_COUNT = 5

    # Expertise score weights
    EXPERTISE_WEIGHTS = {
        "github_commits": 2.0,
        "slack_answers": 1.5,
        "confluence_authored": 3.0,
        "jira_resolved": 1.0,
        "code_reviews": 1.5,
    }

    # Recency multipliers for expertise
    RECENCY_MULTIPLIERS = {
        30: 1.0,   # Last 30 days: full weight
        90: 0.8,   # 30-90 days: 80%
        180: 0.5,  # 90-180 days: 50%
    }

    @classmethod
    def get_collection_names(cls) -> List[str]:
        """Get list of all collection names"""
        return list(cls.COLLECTION_CONFIGS.keys())

    @classmethod
    def get_collection_config(cls, collection_name: str) -> Dict:
        """Get configuration for a specific collection"""
        return cls.COLLECTION_CONFIGS.get(collection_name)

    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration settings"""
        if not cls.QDRANT_URL:
            raise ValueError("QDRANT_URL is required")

        if cls.EMBEDDING_DIMENSION != 768:
            raise ValueError("EMBEDDING_DIMENSION must be 768 for Gemini text-embedding-004")

        for collection_name, config in cls.COLLECTION_CONFIGS.items():
            if config["size"] != cls.EMBEDDING_DIMENSION:
                raise ValueError(
                    f"Collection {collection_name} size mismatch: "
                    f"{config['size']} != {cls.EMBEDDING_DIMENSION}"
                )

        return True


# Payload schemas for reference
KNOWLEDGE_BASE_PAYLOAD_SCHEMA = {
    "id": str,
    "source": str,  # slack|github|box|jira|confluence|drive|asana|notion
    "content_type": str,  # text|code|image|pdf|video|audio
    "file_type": str,  # doc|pdf|py|jpg|mp4|md|...
    "title": str,
    "content": str,  # Max 10k chars per chunk
    "url": str,
    "created_at": int,  # Unix timestamp
    "modified_at": int,
    "owner": str,
    "contributors": list,  # [str]
    "permissions": {
        "public": bool,
        "teams": list,  # [str]
        "users": list,  # [str]
        "sensitivity": str,  # public|internal|confidential|restricted
        "offshore_restricted": bool,
        "third_party_restricted": bool,
    },
    "metadata": dict,  # Source-specific metadata
    "tags": list,  # [str]
    "language": str,
    "embedding_model": str,
    "embedding_version": str,
    "chunk_index": int,
    "total_chunks": int,
}

CONVERSATIONS_PAYLOAD_SCHEMA = {
    "id": str,
    "user_id": str,
    "query": str,
    "results_count": int,
    "top_result_score": float,
    "sources_used": list,  # [str]
    "clicked_results": list,  # [str]
    "user_rating": int,  # 1-5 stars
    "timestamp": int,
    "response_time_ms": int,
    "triggered_approval": bool,
    "approval_granted": bool,
}

EXPERTISE_MAP_PAYLOAD_SCHEMA = {
    "id": str,
    "user_id": str,
    "user_name": str,
    "topic": str,
    "expertise_score": float,  # 0-100
    "evidence": list,  # List of contribution dicts
    "last_contribution": int,
    "contribution_count": int,
    "tags": list,  # [str]
    "trend": str,  # increasing|stable|decreasing
}

KNOWLEDGE_GAPS_PAYLOAD_SCHEMA = {
    "id": str,
    "topic": str,
    "query_patterns": list,  # [str]
    "query_count": int,
    "avg_result_quality": float,
    "first_detected": int,
    "last_query": int,
    "suggested_action": str,
    "suggested_owner": str,
    "status": str,  # detected|approved|in_progress|resolved
    "priority": str,  # low|medium|high|critical
    "related_docs": list,  # [str]
}
