# EngineIQ Connector Builder Skill

**Purpose:** Build EngineIQ connectors following a standard pattern for any data source (Slack, GitHub, Box, Jira, etc.)

**When to use:** When implementing a new connector to index content from external sources into EngineIQ's knowledge base.

---

## Overview

EngineIQ connectors follow a consistent pattern that:
1. Authenticates with the external service
2. Fetches content from the source
3. Extracts and transforms content for different file types
4. Generates embeddings using Gemini text-embedding-004
5. Indexes to Qdrant knowledge_base collection
6. Updates expertise_map for contributor tracking
7. Handles errors and retries gracefully
8. Supports real-time updates via webhooks

---

## 1. Base Connector Class Structure

All connectors extend `BaseConnector`:

```python
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, List, Optional
import asyncio
import uuid
from datetime import datetime

class BaseConnector(ABC):
    """Abstract base class for all EngineIQ connectors"""

    def __init__(
        self,
        credentials: dict,
        gemini_service: 'GeminiService',
        qdrant_service: 'QdrantService'
    ):
        self.credentials = credentials
        self.gemini = gemini_service
        self.qdrant = qdrant_service
        self.source_name = self.__class__.__name__.replace("Connector", "").lower()

    @abstractmethod
    async def authenticate(self) -> bool:
        """
        Authenticate with the external service.

        Returns:
            bool: True if authentication successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_content(self, since: Optional[int] = None) -> AsyncGenerator[Dict, None]:
        """
        Yield content items from the source.

        Args:
            since: Unix timestamp to fetch content modified after this time

        Yields:
            dict: Content item with standardized structure
        """
        pass

    async def extract_content(self, item: dict) -> str:
        """
        Extract text content from various file types using Gemini.

        Args:
            item: Content item with raw_content and content_type

        Returns:
            str: Extracted text content
        """
        content_type = item["content_type"]

        if content_type == "image":
            result = await self.gemini.analyze_image(item["raw_content"])
            return result["semantic_description"]

        elif content_type == "pdf":
            result = await self.gemini.parse_pdf(item["raw_content"])
            return result["text"]

        elif content_type == "video":
            result = await self.gemini.analyze_video(item["raw_content"])
            return result["transcript"]

        elif content_type == "audio":
            result = await self.gemini.transcribe_audio(item["raw_content"])
            return result["transcript"]

        elif content_type == "code":
            result = await self.gemini.analyze_code(
                item["raw_content"],
                item["file_type"]
            )
            return f"{result['purpose']}. Code: {item['raw_content']}"

        else:  # text
            return item["raw_content"]

    async def generate_embedding(self, content: str) -> List[float]:
        """
        Generate Gemini embedding with caching.

        Args:
            content: Text content to embed

        Returns:
            List[float]: 768-dimensional embedding vector
        """
        return await self.gemini.generate_embedding(content, "retrieval_document")

    async def index_item(self, item: dict):
        """
        Process and index a single item to Qdrant.

        Args:
            item: Content item to index
        """
        # Extract content
        content = await self.extract_content(item)

        # Chunk if too large (>10k chars)
        chunks = self.chunk_content(content) if len(content) > 10000 else [content]

        for idx, chunk in enumerate(chunks):
            # Generate embedding
            embedding = await self.generate_embedding(chunk)

            # Prepare payload
            payload = {
                "id": f"{item['id']}_chunk_{idx}" if len(chunks) > 1 else item["id"],
                "source": self.source_name,
                "content_type": item["content_type"],
                "file_type": item["file_type"],
                "title": item["title"],
                "content": chunk,
                "url": item["url"],
                "created_at": item["created_at"],
                "modified_at": item["modified_at"],
                "owner": item["owner"],
                "contributors": item["contributors"],
                "permissions": item["permissions"],
                "metadata": item["metadata"],
                "tags": self.extract_tags(chunk),
                "language": self.detect_language(chunk),
                "embedding_model": "gemini-text-embedding-004",
                "embedding_version": "v1",
                "chunk_index": idx,
                "total_chunks": len(chunks)
            }

            # Index to Qdrant knowledge_base
            await self.qdrant.upsert(
                collection_name="knowledge_base",
                points=[{
                    "id": payload["id"],
                    "vector": embedding,
                    "payload": payload
                }]
            )

            # Update expertise map
            await self.update_expertise_map(item, chunk)

    async def sync(self, since: Optional[int] = None):
        """
        Full sync - index all content.

        Args:
            since: Unix timestamp to sync content modified after this time
        """
        count = 0
        async for item in self.get_content(since):
            try:
                await self.index_item(item)
                count += 1
                if count % 10 == 0:
                    print(f"✓ Indexed {count} items from {self.source_name}")
            except Exception as e:
                print(f"✗ Error indexing {item['id']}: {e}")
                continue

        print(f"✓ Synced {count} total items from {self.source_name}")

    @abstractmethod
    async def watch_for_changes(self):
        """
        Set up webhooks or polling for real-time updates.

        Implementation depends on the source API capabilities.
        """
        pass

    def chunk_content(self, content: str, chunk_size: int = 8000) -> List[str]:
        """
        Smart chunking with overlap.

        Args:
            content: Text content to chunk
            chunk_size: Maximum characters per chunk

        Returns:
            List[str]: List of text chunks
        """
        chunks = []
        overlap = 500
        for i in range(0, len(content), chunk_size - overlap):
            chunks.append(content[i:i + chunk_size])
        return chunks

    def extract_tags(self, content: str) -> List[str]:
        """
        Extract relevant tags from content.

        Args:
            content: Text content

        Returns:
            List[str]: Extracted tags
        """
        # Simple keyword matching (can be enhanced with Gemini)
        common_tech_terms = [
            "kubernetes", "docker", "python", "javascript", "react",
            "database", "api", "authentication", "deployment", "testing",
            "cicd", "monitoring", "security", "performance"
        ]
        return [term for term in common_tech_terms if term.lower() in content.lower()]

    def detect_language(self, content: str) -> str:
        """
        Detect content language.

        Args:
            content: Text content

        Returns:
            str: Language code (e.g., "en", "es")
        """
        # Default to English (can use langdetect library)
        return "en"

    async def update_expertise_map(self, item: dict, content: str):
        """
        Track contributor expertise in expertise_map collection.

        Args:
            item: Content item
            content: Extracted text content
        """
        embedding = await self.generate_embedding(content)

        for contributor in item["contributors"]:
            score = self.calculate_contribution_score(item)

            await self.qdrant.upsert(
                collection_name="expertise_map",
                points=[{
                    "id": f"{contributor}_{item['id']}",
                    "vector": embedding,
                    "payload": {
                        "user_id": contributor,
                        "topic": item["title"],
                        "topic_embedding": embedding,
                        "expertise_score": score,
                        "evidence": [{
                            "source": self.source_name,
                            "action": self.get_action_type(item),
                            "doc_id": item["id"],
                            "doc_title": item["title"],
                            "doc_url": item["url"],
                            "timestamp": item["modified_at"],
                            "contribution_score": score
                        }],
                        "last_contribution": item["modified_at"],
                        "contribution_count": 1,
                        "tags": self.extract_tags(content)
                    }
                }]
            )

    def calculate_contribution_score(self, item: dict) -> float:
        """
        Calculate contribution score based on action type.
        Override in subclasses for source-specific scoring.

        Args:
            item: Content item

        Returns:
            float: Contribution score
        """
        return 1.0

    def get_action_type(self, item: dict) -> str:
        """
        Get action type (authored, reviewed, answered, etc.).
        Override in subclasses.

        Args:
            item: Content item

        Returns:
            str: Action type
        """
        return "authored"
```

---

## 2. Authentication Patterns

### OAuth2 (Slack, Box, Google Drive)

```python
async def authenticate(self) -> bool:
    """OAuth2 authentication pattern"""
    try:
        # Initialize OAuth client
        self.client = OAuth2Client(
            client_id=self.credentials["client_id"],
            client_secret=self.credentials["client_secret"],
            access_token=self.credentials["access_token"]
        )

        # Test authentication
        response = await self.client.test_auth()
        return response["ok"]

    except Exception as e:
        print(f"Authentication failed: {e}")
        return False
```

### API Token (GitHub, Jira, Confluence)

```python
async def authenticate(self) -> bool:
    """API token authentication pattern"""
    try:
        # Initialize client with token
        self.client = APIClient(token=self.credentials["api_token"])

        # Test authentication
        user = await self.client.get_current_user()
        return bool(user)

    except Exception as e:
        print(f"Authentication failed: {e}")
        return False
```

### Basic Auth (Jira, Confluence)

```python
async def authenticate(self) -> bool:
    """Basic authentication pattern"""
    try:
        # Initialize client with credentials
        self.client = BasicAuthClient(
            base_url=self.credentials["base_url"],
            username=self.credentials["username"],
            password=self.credentials["password"]
        )

        # Test authentication
        response = await self.client.get("/api/myself")
        return response.status_code == 200

    except Exception as e:
        print(f"Authentication failed: {e}")
        return False
```

---

## 3. Content Extraction for Different File Types

### Text Content

```python
# Plain text - return as-is
if content_type == "text":
    return item["raw_content"]
```

### Code Content

```python
# Use Gemini to understand code semantically
if content_type == "code":
    result = await self.gemini.analyze_code(
        code=item["raw_content"],
        language=item["file_type"]  # py, js, java, etc.
    )
    # Combine semantic understanding with actual code
    return f"{result['purpose']}. Concepts: {', '.join(result['concepts'])}. Code:\n{item['raw_content']}"
```

### PDF Content

```python
# Use Gemini multimodal PDF parsing
if content_type == "pdf":
    # Upload PDF to Gemini
    pdf_file = await self.gemini.upload_file(item["raw_content"])

    result = await self.gemini.parse_pdf(pdf_file)
    # result contains: text, image_descriptions, topics

    return f"{result['text']}\n\nImages: {result['image_descriptions']}"
```

### Image Content

```python
# Use Gemini Vision
if content_type == "image":
    result = await self.gemini.analyze_image(item["raw_content"])
    # result contains: type, main_components, concepts, semantic_description

    return result["semantic_description"]
```

### Video Content

```python
# Use Gemini video understanding
if content_type == "video":
    video_file = await self.gemini.upload_file(item["raw_content"])

    result = await self.gemini.analyze_video(video_file)
    # result contains: transcript, key_moments, action_items

    # Combine transcript with key moments
    moments_text = "\n".join([
        f"[{m['timestamp']}] {m['description']}"
        for m in result['key_moments']
    ])

    return f"{result['transcript']}\n\nKey Moments:\n{moments_text}"
```

### Audio Content

```python
# Use Gemini audio transcription
if content_type == "audio":
    audio_file = await self.gemini.upload_file(item["raw_content"])

    result = await self.gemini.transcribe_audio(audio_file)
    # result contains: transcript, speakers, key_points

    return result["transcript"]
```

---

## 4. Gemini Integration for Embeddings

### Generate Single Embedding

```python
async def generate_embedding(self, content: str) -> List[float]:
    """Generate embedding using Gemini text-embedding-004"""
    return await self.gemini.generate_embedding(
        content=content,
        task_type="retrieval_document"  # For indexing content
    )
```

### Batch Embeddings (More Efficient)

```python
async def generate_batch_embeddings(self, contents: List[str]) -> List[List[float]]:
    """Generate embeddings in batch for better performance"""
    return await self.gemini.batch_embed(
        texts=contents,
        batch_size=100
    )
```

### Embedding with Caching

```python
# Embeddings are automatically cached in GeminiService
# Cache key: hash(content + task_type)
# This prevents re-generating embeddings for duplicate content
```

---

## 5. Qdrant Indexing with Proper Payload

### Knowledge Base Payload Structure

```python
payload = {
    # Core fields
    "id": str,  # Unique ID (use UUID or source_id)
    "source": str,  # slack|github|box|jira|confluence|drive|asana|notion
    "content_type": str,  # text|code|image|pdf|video|audio
    "file_type": str,  # doc|pdf|py|jpg|mp4|md|...
    "title": str,
    "content": str,  # Extracted text (max 10k chars per chunk)
    "url": str,  # Link back to source

    # Timestamps
    "created_at": int,  # Unix timestamp
    "modified_at": int,

    # People
    "owner": str,  # Primary author/owner
    "contributors": List[str],  # All contributors

    # Permissions (CRITICAL for human-in-loop)
    "permissions": {
        "public": bool,
        "teams": List[str],
        "users": List[str],
        "sensitivity": str,  # public|internal|confidential|restricted
        "offshore_restricted": bool,
        "third_party_restricted": bool
    },

    # Source-specific metadata
    "metadata": {
        # Slack
        "slack_channel": str,
        "slack_thread_ts": str,

        # GitHub
        "github_repo": str,
        "github_path": str,

        # Jira
        "jira_project": str,
        "jira_issue_key": str,

        # Box/Drive
        "box_folder_id": str,
        "drive_folder_id": str,

        # Add source-specific fields as needed
    },

    # Extracted metadata
    "tags": List[str],
    "language": str,  # en, es, fr, etc.

    # Embedding metadata
    "embedding_model": "gemini-text-embedding-004",
    "embedding_version": "v1",

    # Chunking (for large documents)
    "chunk_index": int,  # 0 if not chunked
    "total_chunks": int  # 1 if not chunked
}
```

### Indexing to Qdrant

```python
await self.qdrant.upsert(
    collection_name="knowledge_base",
    points=[{
        "id": payload["id"],
        "vector": embedding,  # 768-dim from Gemini
        "payload": payload
    }]
)
```

### Batch Indexing (More Efficient)

```python
points = []
for item in items:
    embedding = await self.generate_embedding(item["content"])
    points.append({
        "id": item["id"],
        "vector": embedding,
        "payload": create_payload(item)
    })

await self.qdrant.upsert(
    collection_name="knowledge_base",
    points=points
)
```

---

## 6. Permission Handling

### Permission Structure

```python
permissions = {
    # Public access
    "public": bool,  # True if anyone can see

    # Team-based access
    "teams": ["engineering", "product", "sales"],

    # User-based access
    "users": ["user_id_1", "user_id_2"],

    # Sensitivity level
    "sensitivity": "public",  # public|internal|confidential|restricted

    # Special restrictions
    "offshore_restricted": False,  # True = offshore contractors can't see
    "third_party_restricted": False  # True = third-party vendors can't see
}
```

### Setting Permissions (Examples)

**Public Slack Channel:**
```python
permissions = {
    "public": True,
    "teams": [],
    "users": [],
    "sensitivity": "public",
    "offshore_restricted": False,
    "third_party_restricted": False
}
```

**Private GitHub Repo:**
```python
permissions = {
    "public": False,
    "teams": ["engineering"],
    "users": [],
    "sensitivity": "internal",
    "offshore_restricted": False,
    "third_party_restricted": True
}
```

**Confidential Confluence Page:**
```python
permissions = {
    "public": False,
    "teams": ["executive"],
    "users": ["ceo", "cfo"],
    "sensitivity": "confidential",
    "offshore_restricted": True,
    "third_party_restricted": True
}
```

---

## 7. Error Handling and Retry Logic

### Retry with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((ConnectionError, TimeoutError))
)
async def fetch_with_retry(self, url: str):
    """Fetch with automatic retry"""
    response = await self.client.get(url)
    response.raise_for_status()
    return response.json()
```

### Error Handling in Sync

```python
async def sync(self, since: Optional[int] = None):
    """Sync with comprehensive error handling"""
    count = 0
    errors = []

    async for item in self.get_content(since):
        try:
            await self.index_item(item)
            count += 1

            if count % 10 == 0:
                print(f"✓ Indexed {count} items from {self.source_name}")

        except Exception as e:
            error_msg = f"Error indexing {item.get('id', 'unknown')}: {str(e)}"
            print(f"✗ {error_msg}")
            errors.append(error_msg)

            # Continue with next item (don't fail entire sync)
            continue

    # Summary
    print(f"\n✓ Sync complete: {count} items indexed, {len(errors)} errors")

    if errors:
        print("\nErrors encountered:")
        for error in errors[:10]:  # Show first 10
            print(f"  - {error}")
```

### Rate Limit Handling

```python
import asyncio

async def handle_rate_limit(self, retry_after: int):
    """Handle rate limiting gracefully"""
    print(f"⏳ Rate limited. Waiting {retry_after} seconds...")
    await asyncio.sleep(retry_after)

async def make_api_call(self, endpoint: str):
    """API call with rate limit handling"""
    try:
        response = await self.client.get(endpoint)
        response.raise_for_status()
        return response.json()

    except RateLimitError as e:
        retry_after = int(e.response.headers.get("Retry-After", 60))
        await self.handle_rate_limit(retry_after)

        # Retry
        return await self.make_api_call(endpoint)
```

---

## 8. Webhook Setup for Real-Time Updates

### Webhook Pattern

```python
async def watch_for_changes(self):
    """Set up webhook for real-time updates"""
    # 1. Register webhook with source
    webhook_url = f"{self.config['base_url']}/webhooks/{self.source_name}"

    await self.client.register_webhook(
        url=webhook_url,
        events=["created", "updated", "deleted"]
    )

    print(f"✓ Webhook registered: {webhook_url}")

# In your FastAPI app:
@app.post("/webhooks/slack")
async def slack_webhook(request: Request):
    """Handle Slack webhook events"""
    payload = await request.json()

    # Verify webhook signature
    if not verify_slack_signature(request.headers, payload):
        raise HTTPException(401)

    # Process event
    event_type = payload["event"]["type"]

    if event_type == "message":
        await slack_connector.handle_new_message(payload["event"])

    return {"ok": True}
```

### Polling Fallback (If Webhooks Not Available)

```python
async def watch_for_changes(self):
    """Poll for changes if webhooks not available"""
    while True:
        try:
            # Get last sync time
            last_sync = await self.get_last_sync_time()

            # Sync new/updated content
            await self.sync(since=last_sync)

            # Save current time
            await self.save_last_sync_time(int(datetime.now().timestamp()))

        except Exception as e:
            print(f"✗ Polling error: {e}")

        # Wait before next poll (5 minutes)
        await asyncio.sleep(300)
```

---

## 9. Testing Approach

### Unit Tests

```python
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
async def connector():
    """Create test connector"""
    gemini = AsyncMock()
    qdrant = AsyncMock()
    credentials = {"api_token": "test_token"}

    return MyConnector(credentials, gemini, qdrant)

@pytest.mark.asyncio
async def test_authenticate(connector):
    """Test authentication"""
    connector.client = AsyncMock()
    connector.client.test_auth.return_value = {"ok": True}

    result = await connector.authenticate()
    assert result == True

@pytest.mark.asyncio
async def test_get_content(connector):
    """Test content fetching"""
    connector.client = AsyncMock()

    # Mock API response
    connector.client.get_items.return_value = [
        {"id": "1", "title": "Test", "content": "Hello"}
    ]

    items = []
    async for item in connector.get_content():
        items.append(item)

    assert len(items) > 0
    assert "id" in items[0]
    assert "title" in items[0]

@pytest.mark.asyncio
async def test_index_item(connector):
    """Test indexing"""
    # Mock Gemini embedding
    connector.gemini.generate_embedding.return_value = [0.1] * 768

    # Mock Qdrant upsert
    connector.qdrant.upsert = AsyncMock()

    item = {
        "id": "test_1",
        "title": "Test",
        "raw_content": "Test content",
        "content_type": "text",
        "file_type": "txt",
        "url": "https://example.com/test",
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

    await connector.index_item(item)

    # Verify Qdrant was called
    connector.qdrant.upsert.assert_called_once()
```

### Integration Tests

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_full_sync_flow():
    """Test full sync with real services (use test credentials)"""
    # Use test/staging credentials
    credentials = load_test_credentials()

    gemini = GeminiService(test_api_key)
    qdrant = QdrantService(test_url)

    connector = MyConnector(credentials, gemini, qdrant)

    # Authenticate
    assert await connector.authenticate()

    # Sync small dataset
    await connector.sync()

    # Verify items in Qdrant
    results = await qdrant.search(
        collection_name="knowledge_base",
        query_vector=[0.1] * 768,
        limit=10
    )

    assert len(results) > 0
```

---

## Example: Complete Slack Connector

See `examples/slack_connector.py` for a complete implementation.

---

## Checklist for New Connector

- [ ] Extend `BaseConnector`
- [ ] Implement `authenticate()`
- [ ] Implement `get_content()` with pagination
- [ ] Map content to standardized structure
- [ ] Set appropriate permissions
- [ ] Handle all relevant content types (text, code, images, etc.)
- [ ] Implement `watch_for_changes()` (webhook or polling)
- [ ] Override `calculate_contribution_score()` for source-specific scoring
- [ ] Override `get_action_type()` for source-specific actions
- [ ] Add error handling and retries
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Test with small dataset
- [ ] Document any source-specific quirks

---

## Resources

- **Qdrant Schema**: See `BUILD_PLAN.md` section 2
- **Gemini Integration**: See `BUILD_PLAN.md` section 3
- **Example Connectors**: See `examples/` directory
- **Testing**: See `tests/connectors/` directory
