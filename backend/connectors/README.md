# EngineIQ Connectors

Data source connectors for indexing content into EngineIQ's knowledge base.

## Overview

EngineIQ connectors follow a consistent pattern to:
1. **Authenticate** with external services
2. **Fetch content** from sources
3. **Extract and transform** content for different file types
4. **Generate embeddings** using Gemini text-embedding-004
5. **Index to Qdrant** knowledge_base collection
6. **Update expertise map** for contributor tracking
7. **Handle errors** gracefully with retries
8. **Support real-time updates** via webhooks/polling

---

## Architecture

```
BaseConnector (Abstract)
├── authenticate()
├── get_content()
├── extract_content()
├── generate_embedding()
├── index_item()
├── sync()
└── watch_for_changes()

SlackConnector (Concrete)
├── get_channels()
├── get_messages()
├── get_thread_messages()
├── extract_code_blocks()
├── extract_metadata()
├── track_expertise()
└── should_trigger_approval()
```

---

## Base Connector

All connectors extend `BaseConnector`:

```python
from backend.connectors import BaseConnector

class MyConnector(BaseConnector):
    async def authenticate(self) -> bool:
        # Implement authentication
        pass
    
    async def get_content(self, since=None):
        # Yield content items
        pass
    
    async def watch_for_changes(self):
        # Set up real-time updates
        pass
```

### Required Methods

- **`authenticate()`** - Authenticate with the external service
- **`get_content(since)`** - Generator that yields standardized content items
- **`watch_for_changes()`** - Set up webhooks or polling for real-time updates

### Provided Methods

- **`extract_content(item)`** - Extract text from various file types (text, code, PDF, images, video, audio)
- **`generate_embedding(content)`** - Generate 768-dim Gemini embedding
- **`index_item(item)`** - Process and index item to Qdrant
- **`sync(since)`** - Full sync of all content
- **`chunk_content(content)`** - Smart chunking with overlap
- **`extract_tags(content)`** - Extract relevant tags
- **`detect_language(content)`** - Detect content language
- **`update_expertise_map(item, content, embedding)`** - Track contributor expertise

---

## Slack Connector

Complete Slack integration for indexing messages, threads, and tracking expertise.

### Features

✅ Fetches messages from all accessible channels  
✅ Preserves thread context  
✅ Extracts code blocks separately (```markers```)  
✅ Tracks reactions (indicates valuable content)  
✅ Handles channel permissions (public vs private)  
✅ Flags confidential channels for human-in-loop  
✅ Updates expertise map for answerers  
✅ Caches user names for performance  

### Installation

```bash
pip install slack-sdk==3.23.0
```

### Setup

1. **Create Slack App**: https://api.slack.com/apps
2. **Add Bot Token Scopes**:
   - `channels:history` - Read messages from public channels
   - `channels:read` - List public channels
   - `groups:history` - Read messages from private channels (optional)
   - `groups:read` - List private channels (optional)
   - `users:read` - Read user information
3. **Install to Workspace**
4. **Get Bot Token** (starts with `xoxb-`)

### Environment Variables

```bash
export SLACK_BOT_TOKEN=xoxb-your-bot-token-here
export SLACK_WORKSPACE=yourworkspace
```

### Usage

```python
from backend.connectors import SlackConnector
from backend.services import GeminiService, QdrantService

# Initialize services
gemini = GeminiService(api_key="your_key")
qdrant = QdrantService(url="http://localhost:6333")

# Initialize connector
slack = SlackConnector(
    credentials={
        "bot_token": "xoxb-your-bot-token",
        "workspace": "yourworkspace"
    },
    gemini_service=gemini,
    qdrant_service=qdrant
)

# Authenticate
if await slack.authenticate():
    # Sync all messages
    count = await slack.sync()
    print(f"Indexed {count} messages")
```

### Methods

#### Core Methods

- **`authenticate()`** - Authenticate with Slack bot token
- **`get_channels()`** - List all accessible channels
- **`get_messages(channel_id, since)`** - Get messages from channel with pagination
- **`get_thread_messages(channel_id, thread_ts)`** - Get all messages in a thread

#### Content Processing

- **`extract_code_blocks(text)`** - Extract ```code blocks``` from message
- **`extract_metadata(message, channel, thread_messages)`** - Extract Slack-specific metadata
- **`get_message_url(channel_id, ts)`** - Construct message permalink

#### Expertise Tracking

- **`get_action_type(item)`** - Determine action type (authored/answered/asked)
- **`calculate_contribution_score(item)`** - Calculate contribution score (1.0-3.0)
- **`track_expertise(item, embedding)`** - Update expertise map

#### Permission & Approval

- **`should_trigger_approval(item)`** - Check if human-in-loop needed
- **`_get_permissions(channel)`** - Get permissions structure for channel

### Contribution Scoring

The Slack connector uses intelligent scoring:

```python
# Base scores
base_score = 1.0              # Standalone message
base_score = 1.5              # Answer in thread

# Bonuses
reaction_bonus = min(reaction_count * 0.1, 1.0)  # Up to +1.0
code_bonus = 0.5 if has_code_blocks else 0.0     # +0.5

# Final score
score = base_score + reaction_bonus + code_bonus
# Range: 1.0 - 3.0
```

### Human-in-Loop Triggers

Approval is triggered for:
- Channels with "confidential" in name
- Channels with "private-", "secret-", "restricted-" prefixes
- Messages with `sensitivity: "confidential"` or `"restricted"`

Example:
```python
# These trigger approval:
- #confidential-payments
- #private-security
- #restricted-hr
```

### Demo Data

Character-driven demo data with realistic conversations:

**Characters:**
- **Priya Sharma** (Junior Engineer, Bangalore) - Asks deployment questions
- **Sarah Chen** (Senior Engineer, San Francisco) - Answers with expertise
- **Diego Fernández** (DevOps Lead, Buenos Aires) - Kubernetes expert

**Topics:**
- Deployment procedures with checklists
- Kubernetes troubleshooting (OOMKilled pods)
- Database migrations
- Payment system integration (confidential channel)

```python
from backend.connectors.slack_demo_data import SlackDemoDataGenerator

generator = SlackDemoDataGenerator()
messages = generator.generate_all_messages()

print(f"Generated {len(messages)} realistic messages")
```

### Real-Time Updates

The connector supports real-time updates via polling (webhook support coming soon):

```python
# Start watching for changes (polls every 5 minutes)
await slack.watch_for_changes()
```

---

## Testing

Run comprehensive tests:

```bash
# All connector tests
pytest backend/tests/test_slack_connector.py -v

# Specific tests
pytest backend/tests/test_slack_connector.py::TestSlackConnector::test_authenticate_success -v
pytest backend/tests/test_slack_connector.py::TestSlackDemoDataGenerator -v

# With coverage
pytest backend/tests/test_slack_connector.py --cov=backend/connectors --cov-report=html
```

---

## Example

Run the complete example:

```bash
# With demo data (no Slack token needed)
python backend/examples/slack_connector_example.py

# With real Slack data
export SLACK_BOT_TOKEN=xoxb-your-token
export GOOGLE_API_KEY=your-gemini-key
python backend/examples/slack_connector_example.py
```

Expected output:
```
======================================================================
EngineIQ Slack Connector Example
======================================================================

1. Initializing services...
   ✓ Services initialized

2. Initializing Slack connector...
   ✓ Slack connector initialized

3. Using demo data (skip authentication)

4. Indexing Slack messages...
   Using character-driven demo data:

   Characters:
     - Priya Sharma (Junior Engineer, Bangalore, India)
     - Sarah Chen (Senior Engineer, San Francisco, USA)
     - Diego Fernández (DevOps Lead, Buenos Aires, Argentina)

   Channels:
     - #engineering (Public)
     - #confidential-payments (Private)

   Generated 8 demo messages

     🚨 Human-in-loop: #confidential-payments - Payment processor integration
     ✓ Indexed 3/8 messages
     ✓ Indexed 6/8 messages

   ✓ Indexed 8 messages
   ⚠️  Triggered 2 human-in-loop approvals

5. Example indexed content:

   knowledge_base collection:
     Total documents: 8

   expertise_map collection:
     Expertise records: 8

======================================================================
✓ Slack connector example completed!
======================================================================
```

---

## Content Item Structure

All connectors yield items with this structure:

```python
{
    "id": str,                      # Unique identifier
    "title": str,                   # Display title
    "raw_content": str,             # Full text content
    "content_type": str,            # text|code|image|pdf|video|audio
    "file_type": str,               # md|py|jpg|pdf|...
    "url": str,                     # Link back to source
    "created_at": int,              # Unix timestamp
    "modified_at": int,             # Unix timestamp
    "owner": str,                   # Primary author
    "contributors": [str],          # All contributors
    "permissions": {
        "public": bool,
        "teams": [str],
        "users": [str],
        "sensitivity": str,         # public|internal|confidential|restricted
        "offshore_restricted": bool,
        "third_party_restricted": bool
    },
    "metadata": {}                  # Source-specific metadata
}
```

---

## File Structure

```
backend/connectors/
├── __init__.py
├── base_connector.py              # Abstract base class
├── slack_connector.py             # Slack implementation
├── slack_demo_data.py             # Character-driven demo data
└── README.md                      # This file

backend/tests/
└── test_slack_connector.py        # Comprehensive tests

backend/examples/
└── slack_connector_example.py     # Working example
```

---

## Next Steps

### Build More Connectors

Follow the same pattern for other sources:

1. **GitHub Connector** - Index code, PRs, issues
2. **Box Connector** - Index documents and files
3. **Jira Connector** - Index issues and projects
4. **Confluence Connector** - Index wiki pages
5. **Google Drive Connector** - Index docs, sheets, slides

### Enhance Slack Connector

- ✅ Webhook support for real-time updates
- ✅ File attachments (images, PDFs, etc.)
- ✅ Emoji reactions sentiment analysis
- ✅ Better code language detection
- ✅ User profile enrichment

---

## Troubleshooting

### Authentication Failed

```bash
# Check token
echo $SLACK_BOT_TOKEN

# Verify token format (should start with xoxb-)
# Re-install app to workspace if needed
```

### No Messages Indexed

```bash
# Check bot has access to channels
# Verify bot scopes in Slack app settings
# Try inviting bot to channels: /invite @your_bot
```

### Qdrant Connection Failed

```bash
# Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# Check connection
curl http://localhost:6333/collections
```

### Gemini API Errors

```bash
# Check API key
echo $GOOGLE_API_KEY

# Verify quota at: https://ai.google.dev/
```

---

## Resources

- **Slack API Docs**: https://api.slack.com/
- **Gemini API Docs**: https://ai.google.dev/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **EngineIQ Skills**: `.claude/skills/engineiq-connector-builder/`

---

**Built following `engineiq-connector-builder` skill patterns**
