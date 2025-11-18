"""
EngineIQ Qdrant Indexing Examples

Demonstrates batch indexing, performance optimization, and error handling.
"""

from qdrant_service import QdrantService
from qdrant_client.models import PointStruct
import time
import asyncio
from typing import List


def example_single_document(service: QdrantService):
    """Example: Index a single document"""
    print("\n=== Index Single Document ===")

    # Prepare document
    document = {
        "id": "slack_C123_1234567890",
        "vector": [0.1] * 768,  # From Gemini
        "payload": {
            "source": "slack",
            "content_type": "text",
            "file_type": "md",
            "title": "#engineering - alice",
            "content": "How do we deploy to production?",
            "url": "https://workspace.slack.com/archives/C123/p1234567890",
            "created_at": int(time.time()),
            "modified_at": int(time.time()),
            "owner": "alice",
            "contributors": ["alice", "bob"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {
                "slack_channel": "engineering",
                "slack_thread_ts": None
            },
            "tags": ["deployment", "production"],
            "language": "en",
            "embedding_model": "gemini-text-embedding-004",
            "embedding_version": "v1",
            "chunk_index": 0,
            "total_chunks": 1
        }
    }

    # Index
    service.upsert(
        collection_name="knowledge_base",
        points=[document],
        show_progress=True
    )

    print("✓ Document indexed successfully")


def example_batch_indexing(service: QdrantService):
    """Example: Batch index multiple documents"""
    print("\n=== Batch Indexing (100 documents) ===")

    # Create 100 test documents
    points = []
    for i in range(100):
        points.append(
            PointStruct(
                id=f"test_doc_{i}",
                vector=[0.1 + (i * 0.001)] * 768,  # Slightly different embeddings
                payload={
                    "source": "slack" if i % 2 == 0 else "github",
                    "content_type": "text",
                    "file_type": "md",
                    "title": f"Test Document {i}",
                    "content": f"This is test document number {i}",
                    "url": f"https://example.com/doc_{i}",
                    "created_at": int(time.time()) - (i * 3600),  # Spread over time
                    "modified_at": int(time.time()),
                    "owner": f"user_{i % 10}",
                    "contributors": [f"user_{i % 10}"],
                    "permissions": {
                        "public": i % 3 == 0,  # Every 3rd doc is public
                        "teams": ["engineering"] if i % 2 == 0 else ["product"],
                        "users": [],
                        "sensitivity": "public" if i % 3 == 0 else "internal",
                        "offshore_restricted": i % 5 == 0,  # Every 5th doc
                        "third_party_restricted": i % 7 == 0  # Every 7th doc
                    },
                    "metadata": {},
                    "tags": ["test", f"category_{i % 5}"],
                    "language": "en",
                    "embedding_model": "gemini-text-embedding-004",
                    "embedding_version": "v1",
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            )
        )

    # Batch index with timing
    start = time.time()

    service.upsert(
        collection_name="knowledge_base",
        points=points,
        batch_size=50,  # 50 points per batch
        show_progress=True
    )

    elapsed = time.time() - start
    print(f"\n✓ Indexed {len(points)} documents in {elapsed:.2f}s")
    print(f"  Average: {elapsed/len(points)*1000:.1f}ms per document")


def example_chunked_document(service: QdrantService):
    """Example: Index a large document split into chunks"""
    print("\n=== Index Chunked Document ===")

    # Simulate a long document split into 3 chunks
    base_id = "confluence_page_12345"
    document_title = "Kubernetes Deployment Guide"

    chunks = [
        "Introduction to Kubernetes deployments. This guide covers...",
        "Step 1: Create deployment manifest. Step 2: Apply to cluster...",
        "Troubleshooting common issues. If pods are not starting..."
    ]

    points = []
    for idx, chunk_content in enumerate(chunks):
        points.append(
            PointStruct(
                id=f"{base_id}_chunk_{idx}",
                vector=[0.2 + (idx * 0.01)] * 768,  # Different embedding per chunk
                payload={
                    "source": "confluence",
                    "content_type": "text",
                    "file_type": "html",
                    "title": document_title,
                    "content": chunk_content,
                    "url": f"https://wiki.company.com/pages/{base_id}",
                    "created_at": int(time.time()),
                    "modified_at": int(time.time()),
                    "owner": "alice",
                    "contributors": ["alice", "bob"],
                    "permissions": {
                        "public": True,
                        "teams": [],
                        "users": [],
                        "sensitivity": "public",
                        "offshore_restricted": False,
                        "third_party_restricted": False
                    },
                    "metadata": {
                        "confluence_space": "Engineering",
                        "confluence_page_id": "12345"
                    },
                    "tags": ["kubernetes", "deployment", "guide"],
                    "language": "en",
                    "embedding_model": "gemini-text-embedding-004",
                    "embedding_version": "v1",
                    "chunk_index": idx,
                    "total_chunks": len(chunks)
                }
            )
        )

    service.upsert(
        collection_name="knowledge_base",
        points=points,
        show_progress=True
    )

    print(f"✓ Indexed chunked document: {len(chunks)} chunks")


def example_code_file(service: QdrantService):
    """Example: Index a code file with semantic understanding"""
    print("\n=== Index Code File ===")

    code_content = '''
def deploy_to_production(app_name: str, version: str):
    """Deploy application to production cluster"""
    validate_version(version)
    build_docker_image(app_name, version)
    push_to_registry(app_name, version)
    update_kubernetes_deployment(app_name, version)
    run_health_checks()
    '''

    # In real usage, this would come from Gemini code analysis
    semantic_description = "Function to deploy applications to production. Validates version, builds Docker image, pushes to registry, updates Kubernetes deployment, and runs health checks."

    document = PointStruct(
        id="github_company/backend_abc123",
        vector=[0.3] * 768,  # From Gemini
        payload={
            "source": "github",
            "content_type": "code",
            "file_type": "py",
            "title": "company/backend/deployment/deploy.py",
            "content": f"{semantic_description}\n\nCode:\n{code_content}",
            "url": "https://github.com/company/backend/blob/main/deployment/deploy.py",
            "created_at": int(time.time()) - 86400,
            "modified_at": int(time.time()),
            "owner": "alice",
            "contributors": ["alice", "bob", "charlie"],
            "permissions": {
                "public": False,
                "teams": ["engineering"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": True  # Code is sensitive
            },
            "metadata": {
                "github_repo": "company/backend",
                "github_path": "deployment/deploy.py",
                "github_branch": "main",
                "github_language": "Python"
            },
            "tags": ["deployment", "kubernetes", "docker", "production"],
            "language": "python",
            "embedding_model": "gemini-text-embedding-004",
            "embedding_version": "v1",
            "chunk_index": 0,
            "total_chunks": 1
        }
    )

    service.upsert(
        collection_name="knowledge_base",
        points=[document],
        show_progress=True
    )

    print("✓ Code file indexed with semantic understanding")


def example_multimodal_image(service: QdrantService):
    """Example: Index an image (architecture diagram)"""
    print("\n=== Index Image (Architecture Diagram) ===")

    # In real usage, this would come from Gemini Vision
    image_description = "Kubernetes architecture diagram showing: API server, etcd cluster, scheduler, controller manager, worker nodes with kubelet and kube-proxy, and pod deployments. Load balancer routes traffic to ingress controller."

    document = PointStruct(
        id="box_file_architecture_diagram_png",
        vector=[0.4] * 768,  # From Gemini Vision
        payload={
            "source": "box",
            "content_type": "image",
            "file_type": "png",
            "title": "Kubernetes Architecture Diagram.png",
            "content": image_description,  # Semantic description
            "url": "https://app.box.com/file/123456789",
            "created_at": int(time.time()) - 7200,
            "modified_at": int(time.time()),
            "owner": "bob",
            "contributors": ["bob"],
            "permissions": {
                "public": False,
                "teams": ["engineering", "product"],
                "users": [],
                "sensitivity": "internal",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {
                "box_folder_id": "987654321",
                "box_folder_path": "/Engineering/Architecture"
            },
            "tags": ["kubernetes", "architecture", "diagram"],
            "language": "en",
            "embedding_model": "gemini-text-embedding-004",
            "embedding_version": "v1",
            "chunk_index": 0,
            "total_chunks": 1
        }
    )

    service.upsert(
        collection_name="knowledge_base",
        points=[document],
        show_progress=True
    )

    print("✓ Image indexed with visual understanding")


def example_expertise_tracking(service: QdrantService):
    """Example: Track expertise for a user"""
    print("\n=== Track User Expertise ===")

    # When indexing a document, also track contributor expertise
    expertise_entry = PointStruct(
        id="expertise_alice_kubernetes_123",
        vector=[0.5] * 768,  # Topic embedding for "kubernetes deployment"
        payload={
            "user_id": "alice",
            "topic": "kubernetes deployment",
            "expertise_score": 15.0,  # Calculated based on contribution type
            "evidence": [
                {
                    "source": "github",
                    "action": "authored",
                    "doc_id": "github_company/backend_abc123",
                    "doc_title": "deployment/deploy.py",
                    "doc_url": "https://github.com/company/backend/blob/main/deployment/deploy.py",
                    "timestamp": int(time.time()),
                    "contribution_score": 2.0  # Code authoring = 2.0
                },
                {
                    "source": "slack",
                    "action": "answered",
                    "doc_id": "slack_C123_1234567890",
                    "doc_title": "#engineering - How to deploy?",
                    "doc_url": "https://workspace.slack.com/archives/C123/p1234567890",
                    "timestamp": int(time.time()) - 3600,
                    "contribution_score": 1.5  # Answering = 1.5
                },
                {
                    "source": "confluence",
                    "action": "authored",
                    "doc_id": "confluence_page_12345",
                    "doc_title": "Kubernetes Deployment Guide",
                    "doc_url": "https://wiki.company.com/pages/12345",
                    "timestamp": int(time.time()) - 86400,
                    "contribution_score": 3.0  # Documentation = 3.0
                }
            ],
            "last_contribution": int(time.time()),
            "contribution_count": 3,
            "tags": ["kubernetes", "deployment", "docker"]
        }
    )

    service.upsert(
        collection_name="expertise_map",
        points=[expertise_entry],
        show_progress=True
    )

    print("✓ Expertise tracked for user: alice")
    print(f"  Topic: kubernetes deployment")
    print(f"  Score: {expertise_entry.payload['expertise_score']}")
    print(f"  Evidence: {len(expertise_entry.payload['evidence'])} contributions")


def example_conversation_tracking(service: QdrantService):
    """Example: Track a user query for learning"""
    print("\n=== Track User Query ===")

    query_record = PointStruct(
        id=f"conv_{int(time.time())}_user_123",
        vector=[0.6] * 768,  # Query embedding
        payload={
            "user_id": "user_123",
            "query": "How do we deploy to production?",
            "results_count": 5,
            "top_result_score": 0.87,
            "clicked_results": ["slack_C123_1234567890", "github_company/backend_abc123"],
            "user_rating": 5,  # 5 stars
            "timestamp": int(time.time()),
            "response_time_ms": 234,
            "triggered_approval": False,
            "approval_granted": False
        }
    )

    service.upsert(
        collection_name="conversations",
        points=[query_record],
        show_progress=True
    )

    print("✓ Query tracked")
    print(f"  Query: {query_record.payload['query']}")
    print(f"  Results: {query_record.payload['results_count']}")
    print(f"  Top score: {query_record.payload['top_result_score']}")
    print(f"  User rating: {query_record.payload['user_rating']}/5")


def example_knowledge_gap(service: QdrantService):
    """Example: Record a knowledge gap"""
    print("\n=== Record Knowledge Gap ===")

    gap_record = PointStruct(
        id="gap_database_migration_rollback",
        vector=[0.7] * 768,  # Query pattern embedding
        payload={
            "query_pattern": "How to rollback database migrations?",
            "search_count": 18,
            "unique_users": ["user_1", "user_2", "user_3", "user_4", "user_5"],
            "avg_result_score": 0.32,  # Poor results
            "avg_user_rating": 2.1,  # Low satisfaction
            "first_detected": int(time.time()) - (5 * 86400),  # 5 days ago
            "last_searched": int(time.time()),
            "priority": "high",  # High because 18 searches and 5+ unique users
            "suggested_action": "Create documentation on: Database migration rollback procedures",
            "assigned_to": "alice",  # Alice is DB expert
            "status": "detected",
            "related_docs": ["confluence_page_db_guide"]
        }
    )

    service.upsert(
        collection_name="knowledge_gaps",
        points=[gap_record],
        show_progress=True
    )

    print("✓ Knowledge gap recorded")
    print(f"  Pattern: {gap_record.payload['query_pattern']}")
    print(f"  Searches: {gap_record.payload['search_count']}")
    print(f"  Priority: {gap_record.payload['priority']}")
    print(f"  Suggested: {gap_record.payload['suggested_action']}")


def example_update_document(service: QdrantService):
    """Example: Update an existing document"""
    print("\n=== Update Existing Document ===")

    # Get existing document
    existing = service.retrieve(
        collection_name="knowledge_base",
        ids=["slack_C123_1234567890"]
    )

    if existing:
        # Update payload
        updated_payload = existing[0].payload
        updated_payload["tags"].append("answered")
        updated_payload["modified_at"] = int(time.time())

        # Upsert with same ID (updates the document)
        service.upsert(
            collection_name="knowledge_base",
            points=[{
                "id": "slack_C123_1234567890",
                "vector": existing[0].vector,
                "payload": updated_payload
            }],
            show_progress=True
        )

        print("✓ Document updated")
        print(f"  Tags: {updated_payload['tags']}")
    else:
        print("✗ Document not found")


def example_delete_documents(service: QdrantService):
    """Example: Delete documents"""
    print("\n=== Delete Documents ===")

    # Delete by IDs
    ids_to_delete = ["test_doc_0", "test_doc_1", "test_doc_2"]

    service.delete(
        collection_name="knowledge_base",
        points_selector=ids_to_delete
    )

    print(f"✓ Deleted {len(ids_to_delete)} documents by ID")

    # Delete by filter (all test documents)
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    service.delete(
        collection_name="knowledge_base",
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="tags",
                    match=MatchValue(any=["test"])
                )
            ]
        )
    )

    print("✓ Deleted all documents tagged 'test'")


def example_performance_monitoring(service: QdrantService):
    """Example: Monitor indexing performance"""
    print("\n=== Performance Monitoring ===")

    # Create test documents of varying sizes
    sizes = [100, 500, 1000, 5000, 10000]

    for size in sizes:
        # Create document with 'size' words
        content = " ".join(["word"] * size)

        start = time.time()

        service.upsert(
            collection_name="knowledge_base",
            points=[{
                "id": f"perf_test_{size}",
                "vector": [0.1] * 768,
                "payload": {
                    "source": "test",
                    "content_type": "text",
                    "file_type": "txt",
                    "title": f"Performance Test {size} words",
                    "content": content,
                    "url": "https://example.com",
                    "created_at": int(time.time()),
                    "modified_at": int(time.time()),
                    "owner": "test",
                    "contributors": ["test"],
                    "permissions": {
                        "public": True,
                        "teams": [],
                        "users": [],
                        "sensitivity": "public",
                        "offshore_restricted": False,
                        "third_party_restricted": False
                    },
                    "metadata": {},
                    "tags": ["test"],
                    "language": "en",
                    "embedding_model": "gemini-text-embedding-004",
                    "embedding_version": "v1",
                    "chunk_index": 0,
                    "total_chunks": 1
                }
            }],
            show_progress=False
        )

        elapsed = (time.time() - start) * 1000
        print(f"  {size:5d} words: {elapsed:6.1f}ms")


# Main execution
if __name__ == "__main__":
    # Initialize service
    service = QdrantService(
        url="http://localhost:6333",
        api_key=None
    )

    print("=" * 70)
    print("ENGINEIQ QDRANT INDEXING EXAMPLES")
    print("=" * 70)

    # Basic indexing
    example_single_document(service)
    example_batch_indexing(service)
    example_chunked_document(service)

    # Different content types
    example_code_file(service)
    example_multimodal_image(service)

    # Other collections
    example_expertise_tracking(service)
    example_conversation_tracking(service)
    example_knowledge_gap(service)

    # Updates and deletes
    example_update_document(service)
    example_delete_documents(service)

    # Performance
    example_performance_monitoring(service)

    print("\n" + "=" * 70)
    print("ALL INDEXING EXAMPLES COMPLETE")
    print("=" * 70)
