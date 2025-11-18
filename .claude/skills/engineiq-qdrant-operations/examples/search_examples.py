"""
EngineIQ Qdrant Search Examples

Demonstrates all search patterns: basic, hybrid, permission-aware, recommendations.
"""

from qdrant_service import QdrantService
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range
import time


def example_basic_search(service: QdrantService, query_embedding: list):
    """Example: Basic vector similarity search"""
    print("\n=== Basic Vector Search ===")

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        limit=10,
        score_threshold=0.7
    )

    print(f"Found {len(results)} results")
    for i, result in enumerate(results):
        print(f"{i+1}. [{result.score:.2f}] {result.payload['title']}")
        print(f"   Source: {result.payload['source']}")
        print(f"   URL: {result.payload['url']}")


def example_source_filter(service: QdrantService, query_embedding: list):
    """Example: Search only in Slack messages"""
    print("\n=== Source Filter (Slack only) ===")

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="source",
                    match=MatchValue(value="slack")
                )
            ]
        ),
        limit=10
    )

    print(f"Found {len(results)} Slack messages")
    for result in results:
        channel = result.payload.get("metadata", {}).get("slack_channel", "unknown")
        print(f"- [{result.score:.2f}] #{channel}: {result.payload['title']}")


def example_date_filter(service: QdrantService, query_embedding: list):
    """Example: Search for recent documents (last 7 days)"""
    print("\n=== Date Filter (Last 7 Days) ===")

    one_week_ago = int(time.time()) - (7 * 86400)

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="created_at",
                    range=Range(gte=one_week_ago)
                )
            ]
        ),
        limit=10
    )

    print(f"Found {len(results)} recent documents")
    for result in results:
        created = time.strftime('%Y-%m-%d', time.localtime(result.payload['created_at']))
        print(f"- [{result.score:.2f}] {created}: {result.payload['title']}")


def example_tag_filter(service: QdrantService, query_embedding: list):
    """Example: Search for documents tagged with kubernetes"""
    print("\n=== Tag Filter (kubernetes) ===")

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="tags",
                    match=MatchValue(any=["kubernetes"])
                )
            ]
        ),
        limit=10
    )

    print(f"Found {len(results)} kubernetes documents")
    for result in results:
        tags = result.payload.get("tags", [])
        print(f"- [{result.score:.2f}] {result.payload['title']}")
        print(f"  Tags: {', '.join(tags)}")


def example_multi_condition(service: QdrantService, query_embedding: list):
    """Example: Complex multi-condition search"""
    print("\n=== Multi-Condition Search ===")
    print("Query: Slack messages from last week about kubernetes")

    one_week_ago = int(time.time()) - (7 * 86400)

    results = service.hybrid_search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        must=[
            FieldCondition(key="source", match=MatchValue(value="slack")),
            FieldCondition(key="created_at", range=Range(gte=one_week_ago)),
            FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
        ],
        limit=20
    )

    print(f"Found {len(results)} matching documents")
    for result in results:
        channel = result.payload.get("metadata", {}).get("slack_channel", "unknown")
        created = time.strftime('%Y-%m-%d', time.localtime(result.payload['created_at']))
        print(f"- [{result.score:.2f}] #{channel} ({created}): {result.payload['title']}")


def example_permission_search(service: QdrantService, query_embedding: list):
    """Example: Permission-aware search for different user types"""

    # Example 1: Regular employee
    print("\n=== Permission Search: Regular Employee ===")

    regular_user = {
        "id": "user_123",
        "teams": ["engineering"],
        "offshore": False,
        "third_party": False
    }

    results = service.search_with_permissions(
        query_vector=query_embedding,
        user=regular_user,
        limit=10
    )

    print(f"Found {len(results)} accessible documents")
    for result in results:
        sensitivity = result.payload['permissions']['sensitivity']
        print(f"- [{result.score:.2f}] [{sensitivity}] {result.payload['title']}")

    # Example 2: Offshore contractor
    print("\n=== Permission Search: Offshore Contractor ===")

    offshore_user = {
        "id": "contractor_456",
        "teams": ["engineering"],
        "offshore": True,  # Offshore restricted
        "third_party": False
    }

    results = service.search_with_permissions(
        query_vector=query_embedding,
        user=offshore_user,
        limit=10
    )

    print(f"Found {len(results)} accessible documents (offshore restrictions applied)")
    for result in results:
        offshore_restricted = result.payload['permissions']['offshore_restricted']
        print(f"- [{result.score:.2f}] Offshore OK: {not offshore_restricted} - {result.payload['title']}")

    # Example 3: Third-party vendor
    print("\n=== Permission Search: Third-Party Vendor ===")

    vendor_user = {
        "id": "vendor_789",
        "teams": [],
        "offshore": False,
        "third_party": True  # Third-party restricted
    }

    results = service.search_with_permissions(
        query_vector=query_embedding,
        user=vendor_user,
        limit=10
    )

    print(f"Found {len(results)} accessible documents (third-party restrictions applied)")
    for result in results:
        print(f"- [{result.score:.2f}] {result.payload['title']}")


def example_sensitivity_filter(service: QdrantService, query_embedding: list):
    """Example: Filter by sensitivity level"""

    # Only public and internal (no confidential/restricted)
    print("\n=== Sensitivity Filter: Public + Internal Only ===")

    results = service.search(
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
        limit=10
    )

    print(f"Found {len(results)} public/internal documents")
    for result in results:
        sensitivity = result.payload['permissions']['sensitivity']
        print(f"- [{result.score:.2f}] [{sensitivity.upper()}] {result.payload['title']}")


def example_scroll_large_results(service: QdrantService):
    """Example: Scroll through large result sets"""
    print("\n=== Scroll API: Get All Slack Messages ===")

    offset = None
    total_count = 0
    page_num = 0

    while True:
        points, offset = service.scroll(
            collection_name="knowledge_base",
            scroll_filter=Filter(
                must=[
                    FieldCondition(key="source", match=MatchValue(value="slack"))
                ]
            ),
            limit=100,
            offset=offset,
            with_payload=["title", "created_at"]  # Only fetch needed fields
        )

        page_num += 1
        total_count += len(points)

        print(f"Page {page_num}: Retrieved {len(points)} messages (Total: {total_count})")

        # Show first few from this page
        for point in points[:3]:
            print(f"  - {point.payload['title']}")

        if offset is None:
            break

    print(f"\n✓ Retrieved {total_count} total Slack messages")


def example_similar_documents(service: QdrantService):
    """Example: Find documents similar to a given document"""
    print("\n=== Similar Documents ===")

    # Pick a document ID (in real usage, you'd get this from search results)
    reference_doc_id = "slack_C123_1234567890"

    similar = service.find_similar_documents(
        document_id=reference_doc_id,
        limit=5,
        score_threshold=0.7
    )

    if similar:
        print(f"Documents similar to '{reference_doc_id}':")
        for result in similar:
            print(f"- [{result.score:.2f}] {result.payload['title']}")
            print(f"  Source: {result.payload['source']}")
    else:
        print("No similar documents found")


def example_find_experts(service: QdrantService, topic_embedding: list):
    """Example: Find experts on a topic"""
    print("\n=== Find Experts: Kubernetes ===")

    experts = service.find_experts(
        topic_embedding=topic_embedding,
        limit=5,
        score_threshold=0.6
    )

    print(f"Found {len(experts)} experts:")
    for i, expert in enumerate(experts):
        print(f"\n{i+1}. {expert['user_id']} (Score: {expert['total_score']:.1f})")
        print(f"   Evidence ({len(expert['evidence'])} contributions):")

        # Show top 3 contributions
        for evidence in expert['evidence'][:3]:
            print(f"   - {evidence['action'].upper()} in {evidence['source']}: {evidence['doc_title']}")


def example_content_type_filter(service: QdrantService, query_embedding: list):
    """Example: Search only code files"""
    print("\n=== Content Type Filter: Code Only ===")

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="content_type",
                    match=MatchValue(value="code")
                )
            ]
        ),
        limit=10
    )

    print(f"Found {len(results)} code files")
    for result in results:
        file_type = result.payload.get("file_type", "unknown")
        repo = result.payload.get("metadata", {}).get("github_repo", "unknown")
        print(f"- [{result.score:.2f}] {file_type}: {repo}/{result.payload['title']}")


def example_owner_filter(service: QdrantService, query_embedding: list):
    """Example: Search documents by a specific owner"""
    print("\n=== Owner Filter: alice's documents ===")

    results = service.search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        query_filter=Filter(
            must=[
                FieldCondition(
                    key="owner",
                    match=MatchValue(value="alice")
                )
            ]
        ),
        limit=10
    )

    print(f"Found {len(results)} documents by alice")
    for result in results:
        print(f"- [{result.score:.2f}] {result.payload['title']}")
        print(f"  Source: {result.payload['source']}")


def example_combined_filters(service: QdrantService, query_embedding: list):
    """Example: Combine multiple filter types"""
    print("\n=== Combined Filters ===")
    print("Query: Recent GitHub code files about authentication")

    one_month_ago = int(time.time()) - (30 * 86400)

    results = service.hybrid_search(
        collection_name="knowledge_base",
        query_vector=query_embedding,
        must=[
            FieldCondition(key="source", match=MatchValue(value="github")),
            FieldCondition(key="content_type", match=MatchValue(value="code")),
            FieldCondition(key="created_at", range=Range(gte=one_month_ago)),
            FieldCondition(key="tags", match=MatchValue(any=["authentication"]))
        ],
        limit=10
    )

    print(f"Found {len(results)} matching code files")
    for result in results:
        repo = result.payload.get("metadata", {}).get("github_repo", "unknown")
        path = result.payload.get("metadata", {}).get("github_path", "unknown")
        print(f"- [{result.score:.2f}] {repo}/{path}")


def example_search_performance(service: QdrantService, query_embedding: list):
    """Example: Measure search performance"""
    print("\n=== Search Performance Benchmark ===")

    import time

    # Test 1: Simple search
    start = time.time()
    results = service.search("knowledge_base", query_embedding, limit=20)
    elapsed = (time.time() - start) * 1000
    print(f"Simple search: {elapsed:.1f}ms ({len(results)} results)")

    # Test 2: Hybrid search with filters
    start = time.time()
    results = service.hybrid_search(
        "knowledge_base",
        query_embedding,
        must=[
            FieldCondition(key="source", match=MatchValue(value="slack")),
            FieldCondition(key="tags", match=MatchValue(any=["kubernetes"]))
        ],
        limit=20
    )
    elapsed = (time.time() - start) * 1000
    print(f"Hybrid search: {elapsed:.1f}ms ({len(results)} results)")

    # Test 3: Permission-aware search
    start = time.time()
    user = {"id": "test", "teams": ["engineering"], "offshore": False, "third_party": False}
    results = service.search_with_permissions(query_embedding, user, limit=20)
    elapsed = (time.time() - start) * 1000
    print(f"Permission-aware search: {elapsed:.1f}ms ({len(results)} results)")


# Main execution
if __name__ == "__main__":
    # Initialize service
    service = QdrantService(
        url="http://localhost:6333",
        api_key=None
    )

    # Example query embedding (in real usage, get from Gemini)
    query_embedding = [0.1] * 768  # Placeholder

    # Run all examples
    print("=" * 70)
    print("ENGINEIQ QDRANT SEARCH EXAMPLES")
    print("=" * 70)

    # Basic searches
    example_basic_search(service, query_embedding)
    example_source_filter(service, query_embedding)
    example_date_filter(service, query_embedding)
    example_tag_filter(service, query_embedding)

    # Complex searches
    example_multi_condition(service, query_embedding)
    example_combined_filters(service, query_embedding)

    # Permission-aware
    example_permission_search(service, query_embedding)
    example_sensitivity_filter(service, query_embedding)

    # Content type filters
    example_content_type_filter(service, query_embedding)
    example_owner_filter(service, query_embedding)

    # Advanced features
    example_scroll_large_results(service)
    example_similar_documents(service)
    example_find_experts(service, query_embedding)

    # Performance
    example_search_performance(service, query_embedding)

    print("\n" + "=" * 70)
    print("ALL EXAMPLES COMPLETE")
    print("=" * 70)
