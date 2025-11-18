"""
EngineIQ Qdrant Quick Start Example

Run this script to:
1. Initialize all Qdrant collections
2. Index sample documents
3. Perform example searches
4. Verify the setup
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.qdrant_service import QdrantService
from config.qdrant_config import QdrantConfig
import random


def generate_mock_embedding(seed=None):
    """Generate a mock 768-dim embedding for testing"""
    if seed:
        random.seed(seed)
    return [random.random() for _ in range(768)]


def main():
    print("=" * 60)
    print("EngineIQ Qdrant Quick Start")
    print("=" * 60)

    # Step 1: Initialize service
    print("\n1. Initializing Qdrant service...")
    try:
        service = QdrantService()
        print("   ✓ Service initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize service: {e}")
        print("\nMake sure Qdrant is running:")
        print("  docker run -p 6333:6333 qdrant/qdrant")
        return

    # Step 2: Health check
    print("\n2. Checking Qdrant health...")
    if service.health_check():
        print("   ✓ Qdrant is healthy")
    else:
        print("   ✗ Qdrant health check failed")
        return

    # Step 3: Initialize collections
    print("\n3. Initializing collections...")
    try:
        service.initialize_collections()
        print("   ✓ All collections initialized")
    except Exception as e:
        print(f"   ✗ Failed to initialize collections: {e}")
        return

    # Step 4: Get collection stats
    print("\n4. Collection statistics:")
    for collection_name in QdrantConfig.get_collection_names():
        stats = service.get_collection_stats(collection_name)
        print(f"   {collection_name}:")
        print(f"     Points: {stats.get('points_count', 0)}")
        print(f"     Status: {stats.get('status', 'unknown')}")

    # Step 5: Index sample documents
    print("\n5. Indexing sample documents...")
    sample_docs = [
        {
            "id": "slack_deploy_1",
            "vector": generate_mock_embedding(1),
            "payload": {
                "source": "slack",
                "content_type": "text",
                "title": "Production Deployment Discussion",
                "content": "How do we deploy our application to production?",
                "url": "https://workspace.slack.com/archives/C123/p1234567890",
                "created_at": 1699564800,
                "modified_at": 1699564800,
                "owner": "alice",
                "contributors": ["alice", "bob"],
                "permissions": {
                    "public": False,
                    "teams": ["engineering"],
                    "users": [],
                    "sensitivity": "internal",
                    "offshore_restricted": False,
                    "third_party_restricted": False,
                },
                "metadata": {
                    "slack_channel": "engineering",
                    "slack_thread_ts": "1234567890.123456",
                },
                "tags": ["deployment", "production", "devops"],
                "language": "en",
                "embedding_model": "gemini-text-embedding-004",
                "embedding_version": "v1",
                "chunk_index": 0,
                "total_chunks": 1,
            },
        },
        {
            "id": "github_readme_1",
            "vector": generate_mock_embedding(2),
            "payload": {
                "source": "github",
                "content_type": "code",
                "file_type": "md",
                "title": "README.md",
                "content": "# Deployment Guide\n\nSteps to deploy:\n1. Build\n2. Test\n3. Deploy",
                "url": "https://github.com/company/repo/blob/main/README.md",
                "created_at": 1699564800,
                "modified_at": 1699564800,
                "owner": "bob",
                "contributors": ["bob", "charlie"],
                "permissions": {
                    "public": False,
                    "teams": ["engineering", "devops"],
                    "users": [],
                    "sensitivity": "internal",
                    "offshore_restricted": False,
                    "third_party_restricted": False,
                },
                "metadata": {
                    "github_repo": "company/repo",
                    "github_path": "README.md",
                },
                "tags": ["documentation", "deployment"],
                "language": "en",
                "embedding_model": "gemini-text-embedding-004",
                "embedding_version": "v1",
                "chunk_index": 0,
                "total_chunks": 1,
            },
        },
        {
            "id": "confluence_kb_1",
            "vector": generate_mock_embedding(3),
            "payload": {
                "source": "confluence",
                "content_type": "text",
                "title": "Kubernetes Deployment Best Practices",
                "content": "Best practices for deploying to Kubernetes clusters...",
                "url": "https://company.atlassian.net/wiki/spaces/ENG/pages/123",
                "created_at": 1699564800,
                "modified_at": 1699564800,
                "owner": "alice",
                "contributors": ["alice", "bob", "charlie"],
                "permissions": {
                    "public": False,
                    "teams": ["engineering", "devops", "product"],
                    "users": [],
                    "sensitivity": "internal",
                    "offshore_restricted": False,
                    "third_party_restricted": False,
                },
                "metadata": {},
                "tags": ["kubernetes", "deployment", "best-practices"],
                "language": "en",
                "embedding_model": "gemini-text-embedding-004",
                "embedding_version": "v1",
                "chunk_index": 0,
                "total_chunks": 1,
            },
        },
    ]

    try:
        indexed = service.batch_index(
            collection_name="knowledge_base", points=sample_docs, show_progress=False
        )
        print(f"   ✓ Indexed {indexed} sample documents")
    except Exception as e:
        print(f"   ✗ Failed to index documents: {e}")
        return

    # Step 6: Perform sample searches
    print("\n6. Performing sample searches...")

    # Basic search
    print("\n   a) Basic hybrid search for 'deployment':")
    try:
        results = service.hybrid_search(
            collection_name="knowledge_base",
            query_vector=generate_mock_embedding(1),
            limit=3,
            score_threshold=0.0,  # Low threshold for demo
        )
        print(f"      Found {len(results)} results")
        for result in results:
            print(f"      - {result.payload['title']} (score: {result.score:.2f})")
    except Exception as e:
        print(f"      ✗ Search failed: {e}")

    # Permission-aware search
    print("\n   b) Permission-aware search (engineering team):")
    user = {
        "id": "alice",
        "teams": ["engineering"],
        "offshore": False,
        "third_party": False,
    }
    try:
        results = service.filter_by_permissions(
            query_vector=generate_mock_embedding(1), user=user, limit=3, score_threshold=0.0
        )
        print(f"      Found {len(results)} accessible results")
        for result in results:
            print(f"      - {result.payload['title']}")
    except Exception as e:
        print(f"      ✗ Search failed: {e}")

    # Similar documents
    print("\n   c) Finding similar documents:")
    try:
        similar = service.get_similar_documents(
            document_id="slack_deploy_1", limit=2, score_threshold=0.0
        )
        print(f"      Found {len(similar)} similar documents")
        for doc in similar:
            print(f"      - {doc.payload['title']} (score: {doc.score:.2f})")
    except Exception as e:
        print(f"      ✗ Search failed: {e}")

    # Step 7: Log a conversation
    print("\n7. Logging sample conversation...")
    try:
        conversation_id = service.log_conversation(
            user_id="alice",
            query="How to deploy to production?",
            query_embedding=generate_mock_embedding(1),
            results=results,
            response_time_ms=250,
            clicked_results=["slack_deploy_1"],
            user_rating=4,
        )
        print(f"   ✓ Logged conversation: {conversation_id}")
    except Exception as e:
        print(f"   ✗ Failed to log conversation: {e}")

    # Step 8: Final stats
    print("\n8. Final statistics:")
    for collection_name in QdrantConfig.get_collection_names():
        stats = service.get_collection_stats(collection_name)
        print(f"   {collection_name}: {stats.get('points_count', 0)} points")

    print("\n" + "=" * 60)
    print("✓ Quick start completed successfully!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the indexed data in Qdrant UI: http://localhost:6333/dashboard")
    print("2. Run tests: pytest backend/tests/")
    print("3. Build connectors using engineiq-connector-builder skill")
    print("4. Generate demo data using engineiq-demo-data skill")


if __name__ == "__main__":
    main()
