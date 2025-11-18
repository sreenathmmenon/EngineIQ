"""
EngineIQ Connector Testing Examples

Shows how to write unit and integration tests for connectors.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from connectors.slack_connector import SlackConnector
from connectors.github_connector import GitHubConnector


# ============================================================================
# UNIT TESTS
# ============================================================================

@pytest.fixture
def mock_gemini_service():
    """Mock Gemini service"""
    gemini = AsyncMock()
    gemini.generate_embedding.return_value = [0.1] * 768
    gemini.analyze_code.return_value = {
        "purpose": "Test function",
        "concepts": ["testing", "mocking"]
    }
    return gemini


@pytest.fixture
def mock_qdrant_service():
    """Mock Qdrant service"""
    qdrant = AsyncMock()
    qdrant.upsert.return_value = {"status": "ok"}
    return qdrant


@pytest.fixture
def slack_connector(mock_gemini_service, mock_qdrant_service):
    """Create Slack connector with mocked services"""
    credentials = {
        "bot_token": "xoxb-test-token",
        "workspace": "testworkspace"
    }
    return SlackConnector(credentials, mock_gemini_service, mock_qdrant_service)


@pytest.fixture
def github_connector(mock_gemini_service, mock_qdrant_service):
    """Create GitHub connector with mocked services"""
    credentials = {
        "access_token": "ghp_test_token",
        "org": "test-org"
    }
    return GitHubConnector(credentials, mock_gemini_service, mock_qdrant_service)


# ----------------------------------------------------------------------------
# Slack Connector Tests
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_slack_authenticate_success(slack_connector):
    """Test successful Slack authentication"""
    # Mock Slack client
    slack_connector.client = AsyncMock()
    slack_connector.client.auth_test.return_value = {"ok": True}

    result = await slack_connector.authenticate()

    assert result is True
    slack_connector.client.auth_test.assert_called_once()


@pytest.mark.asyncio
async def test_slack_authenticate_failure(slack_connector):
    """Test failed Slack authentication"""
    from slack_sdk.errors import SlackApiError

    # Mock Slack client to raise error
    slack_connector.client = AsyncMock()
    slack_connector.client.auth_test.side_effect = SlackApiError(
        message="Invalid token",
        response={"error": "invalid_auth"}
    )

    result = await slack_connector.authenticate()

    assert result is False


@pytest.mark.asyncio
async def test_slack_get_channels(slack_connector):
    """Test fetching Slack channels"""
    # Mock Slack client
    slack_connector.client = AsyncMock()
    slack_connector.client.conversations_list.return_value = {
        "channels": [
            {"id": "C1", "name": "general", "is_private": False},
            {"id": "C2", "name": "engineering", "is_private": True}
        ]
    }

    channels = await slack_connector.get_channels()

    assert len(channels) == 2
    assert channels[0]["name"] == "general"
    assert channels[1]["is_private"] is True


@pytest.mark.asyncio
async def test_slack_get_content(slack_connector):
    """Test fetching Slack content"""
    # Mock get_channels
    slack_connector.get_channels = AsyncMock(return_value=[
        {"id": "C1", "name": "general", "is_private": False, "team_id": "T1"}
    ])

    # Mock get_channel_messages
    async def mock_messages(channel_id, since):
        yield {
            "ts": "1234567890.123456",
            "text": "Hello world",
            "user": "U1",
            "type": "message"
        }

    slack_connector.get_channel_messages = mock_messages
    slack_connector.get_thread_messages = AsyncMock(return_value=[])

    # Collect items
    items = []
    async for item in slack_connector.get_content():
        items.append(item)

    assert len(items) == 1
    assert "slack_" in items[0]["id"]
    assert items[0]["title"] == "#general - U1"
    assert items[0]["permissions"]["public"] is True


def test_slack_extract_code_blocks(slack_connector):
    """Test extracting code blocks from Slack messages"""
    text = """
    Here's some code:
    ```python
    def hello():
        print("Hello")
    ```
    And more text
    """

    code_blocks = slack_connector.extract_code_blocks(text)

    assert len(code_blocks) == 1
    assert "def hello()" in code_blocks[0]


def test_slack_get_message_url(slack_connector):
    """Test generating Slack message URL"""
    url = slack_connector.get_message_url("C123", "1234567890.123456")

    assert "testworkspace.slack.com" in url
    assert "C123" in url
    assert "p1234567890123456" in url


def test_slack_action_type(slack_connector):
    """Test determining action type"""
    # Standalone message
    item1 = {"raw_content": "Hello world"}
    assert slack_connector.get_action_type(item1) == "authored"

    # Thread reply
    item2 = {"raw_content": "Hello\n\nThread:\nUser: Reply"}
    assert slack_connector.get_action_type(item2) == "answered"


def test_slack_contribution_score(slack_connector):
    """Test contribution score calculation"""
    # Standalone message
    item1 = {"raw_content": "Hello"}
    assert slack_connector.calculate_contribution_score(item1) == 1.0

    # Thread reply (more valuable)
    item2 = {"raw_content": "Thread:\nReply"}
    assert slack_connector.calculate_contribution_score(item2) == 1.5


# ----------------------------------------------------------------------------
# GitHub Connector Tests
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_github_authenticate_success(github_connector):
    """Test successful GitHub authentication"""
    # Mock GitHub client
    mock_user = MagicMock()
    mock_user.login = "testuser"
    github_connector.client.get_user = MagicMock(return_value=mock_user)

    result = await github_connector.authenticate()

    assert result is True


@pytest.mark.asyncio
async def test_github_authenticate_failure(github_connector):
    """Test failed GitHub authentication"""
    from github.GithubException import GithubException

    # Mock GitHub client to raise error
    github_connector.client.get_user.side_effect = GithubException(
        status=401,
        data={"message": "Bad credentials"}
    )

    result = await github_connector.authenticate()

    assert result is False


def test_github_is_code_file(github_connector):
    """Test code file detection"""
    assert github_connector.is_code_file("app.py") is True
    assert github_connector.is_code_file("index.js") is True
    assert github_connector.is_code_file("Main.java") is True
    assert github_connector.is_code_file("README.md") is False
    assert github_connector.is_code_file("image.png") is False


def test_github_action_type(github_connector):
    """Test determining action type"""
    # Code file
    item1 = {"id": "github_owner/repo_sha123"}
    assert github_connector.get_action_type(item1) == "authored"

    # Pull request
    item2 = {"id": "github_pr_owner/repo_123"}
    assert github_connector.get_action_type(item2) == "reviewed"

    # Issue
    item3 = {"id": "github_issue_owner/repo_123"}
    assert github_connector.get_action_type(item3) == "commented"


def test_github_contribution_score(github_connector):
    """Test contribution score calculation"""
    # Code authoring (highest score)
    item1 = {"id": "github_owner/repo_sha"}
    assert github_connector.calculate_contribution_score(item1) == 2.0

    # Code review
    item2 = {"id": "github_pr_owner/repo_123"}
    assert github_connector.calculate_contribution_score(item2) == 1.5

    # Issue comment
    item3 = {"id": "github_issue_owner/repo_123"}
    assert github_connector.calculate_contribution_score(item3) == 1.0


# ----------------------------------------------------------------------------
# Base Connector Tests
# ----------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_extract_content_text(slack_connector):
    """Test extracting plain text content"""
    item = {
        "content_type": "text",
        "raw_content": "Hello world"
    }

    content = await slack_connector.extract_content(item)

    assert content == "Hello world"


@pytest.mark.asyncio
async def test_extract_content_code(slack_connector, mock_gemini_service):
    """Test extracting code content"""
    item = {
        "content_type": "code",
        "file_type": "py",
        "raw_content": "def hello():\n    print('hi')"
    }

    content = await slack_connector.extract_content(item)

    # Should include Gemini analysis + code
    assert "Test function" in content
    assert "def hello()" in content
    mock_gemini_service.analyze_code.assert_called_once()


@pytest.mark.asyncio
async def test_generate_embedding(slack_connector, mock_gemini_service):
    """Test embedding generation"""
    embedding = await slack_connector.generate_embedding("Test content")

    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)
    mock_gemini_service.generate_embedding.assert_called_once_with(
        "Test content",
        "retrieval_document"
    )


def test_chunk_content(slack_connector):
    """Test content chunking"""
    # Small content - no chunking
    small = "Hello world"
    chunks = slack_connector.chunk_content(small)
    assert len(chunks) == 1
    assert chunks[0] == small

    # Large content - should be chunked
    large = "x" * 20000
    chunks = slack_connector.chunk_content(large, chunk_size=8000)
    assert len(chunks) > 1
    # Check overlap
    assert chunks[0][-100:] == chunks[1][:100]


def test_extract_tags(slack_connector):
    """Test tag extraction"""
    content = "We use Kubernetes for deployment with Docker containers and Python microservices"
    tags = slack_connector.extract_tags(content)

    assert "kubernetes" in tags
    assert "docker" in tags
    assert "python" in tags
    assert "deployment" in tags


def test_detect_language(slack_connector):
    """Test language detection"""
    # Default implementation returns 'en'
    lang = slack_connector.detect_language("Hello world")
    assert lang == "en"


@pytest.mark.asyncio
async def test_index_item(slack_connector, mock_gemini_service, mock_qdrant_service):
    """Test indexing a single item"""
    item = {
        "id": "test_1",
        "title": "Test Item",
        "raw_content": "Test content",
        "content_type": "text",
        "file_type": "txt",
        "url": "https://example.com/test",
        "created_at": 1234567890,
        "modified_at": 1234567890,
        "owner": "user_1",
        "contributors": ["user_1", "user_2"],
        "permissions": {
            "public": True,
            "teams": ["engineering"],
            "users": [],
            "sensitivity": "public",
            "offshore_restricted": False,
            "third_party_restricted": False
        },
        "metadata": {}
    }

    await slack_connector.index_item(item)

    # Verify Qdrant upsert was called
    mock_qdrant_service.upsert.assert_called()

    # Verify embedding was generated
    mock_gemini_service.generate_embedding.assert_called()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_slack_full_sync():
    """
    Integration test for full Slack sync.
    Requires real Slack credentials in environment.
    """
    import os
    from services.gemini_service import GeminiService
    from services.qdrant_service import QdrantService

    # Skip if no credentials
    if not os.getenv("SLACK_BOT_TOKEN"):
        pytest.skip("No Slack credentials")

    # Initialize services with test credentials
    gemini = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    qdrant = QdrantService(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    # Initialize connector
    slack = SlackConnector(
        credentials={
            "bot_token": os.getenv("SLACK_BOT_TOKEN"),
            "workspace": os.getenv("SLACK_WORKSPACE")
        },
        gemini_service=gemini,
        qdrant_service=qdrant
    )

    # Authenticate
    assert await slack.authenticate()

    # Sync (limit to recent messages for testing)
    import time
    one_day_ago = int(time.time()) - 86400
    await slack.sync(since=one_day_ago)

    # Verify items in Qdrant
    results = await qdrant.search(
        collection_name="knowledge_base",
        query_vector=[0.1] * 768,
        limit=10,
        query_filter={
            "must": [{"key": "source", "match": {"value": "slack"}}]
        }
    )

    assert len(results) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_github_full_sync():
    """
    Integration test for full GitHub sync.
    Requires real GitHub credentials in environment.
    """
    import os
    from services.gemini_service import GeminiService
    from services.qdrant_service import QdrantService

    # Skip if no credentials
    if not os.getenv("GITHUB_ACCESS_TOKEN"):
        pytest.skip("No GitHub credentials")

    # Initialize services
    gemini = GeminiService(api_key=os.getenv("GEMINI_API_KEY"))
    qdrant = QdrantService(
        url=os.getenv("QDRANT_URL"),
        api_key=os.getenv("QDRANT_API_KEY")
    )

    # Initialize connector (limit to specific repos for testing)
    github = GitHubConnector(
        credentials={
            "access_token": os.getenv("GITHUB_ACCESS_TOKEN"),
            "repos": ["test-repo"]  # Limit to one test repo
        },
        gemini_service=gemini,
        qdrant_service=qdrant
    )

    # Authenticate
    assert await github.authenticate()

    # Sync
    await github.sync()

    # Verify items in Qdrant
    results = await qdrant.search(
        collection_name="knowledge_base",
        query_vector=[0.1] * 768,
        limit=10,
        query_filter={
            "must": [{"key": "source", "match": {"value": "github"}}]
        }
    )

    assert len(results) > 0


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.performance
@pytest.mark.asyncio
async def test_indexing_performance(slack_connector, mock_gemini_service, mock_qdrant_service):
    """Test indexing performance with 100 items"""
    import time

    # Create 100 test items
    items = [
        {
            "id": f"test_{i}",
            "title": f"Test Item {i}",
            "raw_content": f"Test content {i}",
            "content_type": "text",
            "file_type": "txt",
            "url": f"https://example.com/test{i}",
            "created_at": 1234567890,
            "modified_at": 1234567890,
            "owner": "user_1",
            "contributors": ["user_1"],
            "permissions": {
                "public": True,
                "teams": [],
                "users": [],
                "sensitivity": "public",
                "offshore_restricted": False,
                "third_party_restricted": False
            },
            "metadata": {}
        }
        for i in range(100)
    ]

    # Time the indexing
    start = time.time()

    for item in items:
        await slack_connector.index_item(item)

    elapsed = time.time() - start

    print(f"\nIndexed 100 items in {elapsed:.2f}s ({elapsed/100*1000:.0f}ms per item)")

    # Should be reasonably fast (< 60 seconds for 100 items with mocks)
    assert elapsed < 60


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run all tests
    pytest.main([__file__, "-v", "-s"])

    # Run only unit tests
    # pytest.main([__file__, "-v", "-s", "-m", "not integration and not performance"])

    # Run only integration tests
    # pytest.main([__file__, "-v", "-s", "-m", "integration"])

    # Run only performance tests
    # pytest.main([__file__, "-v", "-s", "-m", "performance"])
