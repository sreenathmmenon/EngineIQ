# EngineIQ Connector Builder Skill

A comprehensive skill for building standardized connectors for EngineIQ's knowledge intelligence platform.

## What This Skill Teaches

This skill provides everything you need to build connectors that:
- ✅ Fetch content from external data sources (Slack, GitHub, Jira, etc.)
- ✅ Extract and transform content using Gemini multimodal AI
- ✅ Generate semantic embeddings with Gemini text-embedding-004
- ✅ Index to Qdrant with proper payload structure
- ✅ Track contributor expertise automatically
- ✅ Handle permissions and sensitivity levels
- ✅ Implement error handling and retries
- ✅ Support real-time updates via webhooks

## Quick Start

### 1. Read the Main Skill Documentation
Start with `skill.md` for the complete connector pattern.

### 2. Review Example Implementations
- `examples/slack_connector.py` - Complete Slack connector
- `examples/github_connector.py` - Complete GitHub connector
- `examples/test_connector.py` - Testing patterns

### 3. Use the Template
Copy one of the examples and adapt for your data source.

## File Structure

```
engineiq-connector-builder/
├── README.md                    # This file
├── skill.md                     # Complete connector pattern documentation
└── examples/
    ├── slack_connector.py       # Slack connector example
    ├── github_connector.py      # GitHub connector example
    └── test_connector.py        # Testing examples
```

## Core Concepts

### 1. BaseConnector Pattern
All connectors extend `BaseConnector` which provides:
- Content extraction for all file types
- Embedding generation with caching
- Qdrant indexing with proper payload
- Expertise tracking
- Error handling

### 2. Standardized Item Structure
Every content item must have:
```python
{
    "id": str,                    # Unique identifier
    "title": str,                 # Display title
    "raw_content": str | bytes,   # Content to extract
    "content_type": str,          # text|code|image|pdf|video|audio
    "file_type": str,             # Extension (py, md, jpg, etc.)
    "url": str,                   # Link back to source
    "created_at": int,            # Unix timestamp
    "modified_at": int,           # Unix timestamp
    "owner": str,                 # Primary author
    "contributors": [str],        # All contributors
    "permissions": {...},         # Permission structure
    "metadata": {...}             # Source-specific metadata
}
```

### 3. Permission Structure
Critical for human-in-loop approval:
```python
{
    "public": bool,
    "teams": [str],
    "users": [str],
    "sensitivity": str,           # public|internal|confidential|restricted
    "offshore_restricted": bool,
    "third_party_restricted": bool
}
```

### 4. Gemini Integration
Content extraction uses Gemini for:
- **Text**: Direct indexing
- **Code**: Semantic understanding (purpose, concepts) + code
- **Images**: Vision analysis (diagrams, screenshots)
- **PDFs**: Multimodal parsing (text + images)
- **Videos**: Transcription + key moments
- **Audio**: Transcription + speaker identification

Embeddings use `gemini-text-embedding-004` (768 dimensions).

### 5. Qdrant Collections
Connectors index to 2 collections:

**knowledge_base** - Primary search collection
- Vector: 768-dim Gemini embedding
- Payload: Full content item structure

**expertise_map** - Contributor expertise tracking
- Vector: 768-dim topic embedding
- Payload: User, topic, evidence, scores

## Building Your First Connector

### Step 1: Choose a Template
Start with the example that's closest to your data source:
- **Slack** - For chat/messaging platforms
- **GitHub** - For code repositories and issue trackers

### Step 2: Implement Required Methods

```python
class MyConnector(BaseConnector):
    async def authenticate(self) -> bool:
        """Authenticate with your data source"""
        # Implement OAuth2, API token, or basic auth
        pass

    async def get_content(self, since: int = None) -> AsyncGenerator[Dict, None]:
        """Yield content items from your source"""
        # Fetch and yield standardized items
        pass

    async def watch_for_changes(self):
        """Set up real-time updates"""
        # Implement webhooks or polling
        pass
```

### Step 3: Customize Scoring (Optional)

```python
def get_action_type(self, item: dict) -> str:
    """Return: authored, reviewed, answered, commented, etc."""
    pass

def calculate_contribution_score(self, item: dict) -> float:
    """Return score based on action type"""
    pass
```

### Step 4: Test Thoroughly

```python
# Unit tests
def test_authenticate():
    # Mock external API
    pass

def test_get_content():
    # Mock data fetching
    pass

# Integration tests
@pytest.mark.integration
async def test_full_sync():
    # Test with real credentials
    pass
```

## Common Patterns

### Authentication

**OAuth2** (Slack, Box, Google Drive):
```python
self.client = OAuth2Client(
    client_id=credentials["client_id"],
    client_secret=credentials["client_secret"],
    access_token=credentials["access_token"]
)
```

**API Token** (GitHub, Jira):
```python
self.client = APIClient(token=credentials["api_token"])
```

**Basic Auth** (Confluence):
```python
self.client = BasicAuthClient(
    username=credentials["username"],
    password=credentials["password"]
)
```

### Pagination

```python
cursor = None
while True:
    response = await self.client.get_items(cursor=cursor, limit=100)

    for item in response["items"]:
        yield transform_item(item)

    cursor = response.get("next_cursor")
    if not cursor:
        break
```

### Error Handling

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(self, url: str):
    response = await self.client.get(url)
    response.raise_for_status()
    return response.json()
```

### Rate Limiting

```python
async def handle_rate_limit(self, retry_after: int):
    print(f"⏳ Rate limited. Waiting {retry_after}s...")
    await asyncio.sleep(retry_after)
```

## Testing Your Connector

### Run Unit Tests
```bash
pytest tests/connectors/test_my_connector.py -v
```

### Run Integration Tests
```bash
pytest tests/connectors/test_my_connector.py -v -m integration
```

### Run with Real Credentials
```bash
export MY_SOURCE_API_KEY="your_key"
pytest tests/connectors/test_my_connector.py -v -m integration
```

## Performance Guidelines

### Targets
- **Indexing**: <1 second per item (with Gemini caching)
- **Batch sync**: 100 items in <60 seconds
- **Memory**: <500MB for normal operation

### Optimization Tips
1. **Use batch operations**: Batch Gemini embeddings (100 at a time)
2. **Cache embeddings**: GeminiService caches automatically
3. **Limit content**: Chunk documents >10k chars
4. **Parallelize**: Use asyncio.gather() for independent operations
5. **Rate limits**: Respect source API rate limits

## Troubleshooting

### Issue: Authentication fails
- ✅ Check credentials are correct
- ✅ Verify token hasn't expired
- ✅ Check required scopes/permissions

### Issue: Content not appearing in search
- ✅ Verify Qdrant indexing succeeded
- ✅ Check embedding generation didn't fail
- ✅ Verify payload structure matches schema

### Issue: Slow indexing
- ✅ Enable Gemini caching
- ✅ Use batch operations
- ✅ Check for rate limiting

### Issue: Missing expertise data
- ✅ Verify `update_expertise_map()` is called
- ✅ Check contributors list is populated
- ✅ Verify expertise_map collection exists

## Supported Data Sources

Based on EngineIQ build plan, we support:

**Priority 1 (Must Have):**
- ✅ Slack
- ✅ GitHub
- ✅ Box

**Priority 2 (Should Have):**
- ✅ Google Drive
- ✅ Jira
- ✅ Confluence

**Priority 3 (Nice to Have):**
- Asana
- Notion
- Linear
- Monday.com
- ClickUp
- Azure DevOps

## Contributing New Connectors

When adding a new connector:

1. **Create connector file**: `connectors/my_source_connector.py`
2. **Create test file**: `tests/connectors/test_my_source_connector.py`
3. **Add example**: Update `examples/` with usage example
4. **Document quirks**: Add source-specific notes to README
5. **Test thoroughly**: Unit + integration tests
6. **Add to registry**: Update connector registry in main app

## Resources

- **Main Build Plan**: `../../../BUILD_PLAN.md`
- **Qdrant Schema**: Section 2 of BUILD_PLAN.md
- **Gemini Integration**: Section 3 of BUILD_PLAN.md
- **BaseConnector**: `skill.md` Section 1

## Questions?

Common questions are answered in `skill.md`. For specific issues, check:
- Qdrant docs: https://qdrant.tech/documentation/
- Gemini docs: https://ai.google.dev/docs
- Source API docs: Check your data source's documentation

---

**Ready to build your connector?** Start with `skill.md` for the complete pattern! 🚀
