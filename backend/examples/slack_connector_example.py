"""
EngineIQ Slack Connector Example

Demonstrates how to use the SlackConnector to index Slack messages.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from connectors.slack_connector import SlackConnector
from connectors.slack_demo_data import SlackDemoDataGenerator
from services.gemini_service import GeminiService
from services.qdrant_service import QdrantService
from config.qdrant_config import QdrantConfig


async def main():
    """Run Slack connector example"""

    print("=" * 70)
    print("EngineIQ Slack Connector Example")
    print("=" * 70)

    # Step 1: Initialize services
    print("\n1. Initializing services...")

    try:
        # Initialize Gemini service
        gemini_api_key = os.getenv("GOOGLE_API_KEY")
        if not gemini_api_key:
            print("   ⚠️  GOOGLE_API_KEY not set, using mock embeddings")
            gemini = MockGeminiService()
        else:
            gemini = GeminiService(api_key=gemini_api_key)

        # Initialize Qdrant service
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        qdrant = QdrantService(url=qdrant_url)

        if not qdrant.health_check():
            print(f"   ✗ Qdrant not available at {qdrant_url}")
            print("\n   Start Qdrant with:")
            print("   docker run -p 6333:6333 qdrant/qdrant")
            return

        print("   ✓ Services initialized")

    except Exception as e:
        print(f"   ✗ Error initializing services: {e}")
        return

    # Step 2: Initialize Slack connector
    print("\n2. Initializing Slack connector...")

    slack_token = os.getenv("SLACK_BOT_TOKEN")

    if not slack_token:
        print("   ⚠️  SLACK_BOT_TOKEN not set, using demo data")
        use_demo_data = True
    else:
        use_demo_data = False

    connector = SlackConnector(
        credentials={
            "bot_token": slack_token or "xoxb-demo-token",
            "workspace": os.getenv("SLACK_WORKSPACE", "engineiq"),
        },
        gemini_service=gemini,
        qdrant_service=qdrant,
    )

    print("   ✓ Slack connector initialized")

    # Step 3: Authenticate (skip if demo data)
    if not use_demo_data:
        print("\n3. Authenticating with Slack...")
        if await connector.authenticate():
            print("   ✓ Authenticated successfully")
        else:
            print("   ✗ Authentication failed")
            return
    else:
        print("\n3. Using demo data (skip authentication)")

    # Step 4: Index messages
    print("\n4. Indexing Slack messages...")

    if use_demo_data:
        print("   Using character-driven demo data:")

        # Generate demo data
        demo_gen = SlackDemoDataGenerator()

        print(f"\n   Characters:")
        for char in demo_gen.characters.values():
            print(f"     - {char['name']} ({char['role']}, {char['location']})")

        print(f"\n   Channels:")
        for channel in demo_gen.get_mock_channels():
            privacy = "Private" if channel["is_private"] else "Public"
            print(f"     - #{channel['name']} ({privacy})")

        # Get demo messages
        messages = demo_gen.generate_all_messages()
        print(f"\n   Generated {len(messages)} demo messages")

        # Index each message
        indexed_count = 0
        approval_triggered_count = 0

        for message in messages:
            try:
                # Convert to connector format
                item = await convert_demo_message_to_item(
                    message, demo_gen, connector
                )

                # Check if approval needed
                if connector.should_trigger_approval(item):
                    print(
                        f"     🚨 Human-in-loop: #{item['metadata']['slack_channel']} - {item['title']}"
                    )
                    approval_triggered_count += 1

                # Index item
                await connector.index_item(item)
                indexed_count += 1

                if indexed_count % 3 == 0:
                    print(f"     ✓ Indexed {indexed_count}/{len(messages)} messages")

            except Exception as e:
                print(f"     ✗ Error indexing message: {e}")
                continue

        print(f"\n   ✓ Indexed {indexed_count} messages")
        print(f"   ⚠️  Triggered {approval_triggered_count} human-in-loop approvals")

    else:
        # Real Slack data
        count = await connector.sync()
        print(f"   ✓ Indexed {count} messages")

    # Step 5: Show examples
    print("\n5. Example indexed content:")

    # Query Qdrant for sample results
    stats = qdrant.get_collection_stats("knowledge_base")
    print(f"\n   knowledge_base collection:")
    print(f"     Total documents: {stats.get('points_count', 0)}")

    stats = qdrant.get_collection_stats("expertise_map")
    print(f"\n   expertise_map collection:")
    print(f"     Expertise records: {stats.get('points_count', 0)}")

    print("\n" + "=" * 70)
    print("✓ Slack connector example completed!")
    print("=" * 70)

    print("\n📚 Next steps:")
    print("  1. View indexed data: http://localhost:6333/dashboard")
    print("  2. Run tests: pytest backend/tests/test_slack_connector.py")
    print("  3. Set up real Slack bot:")
    print("     - Create Slack app: https://api.slack.com/apps")
    print("     - Add bot token scopes: channels:history, channels:read, users:read")
    print("     - Install to workspace and get bot token")
    print("     - Set SLACK_BOT_TOKEN environment variable")


async def convert_demo_message_to_item(
    message: dict, demo_gen: SlackDemoDataGenerator, connector: SlackConnector
) -> dict:
    """Convert demo message to connector item format"""

    # Get user name
    user_mapping = demo_gen.get_user_mapping()
    user_name = user_mapping.get(message["user"], message["user"])

    # Get channel info
    channels = demo_gen.get_mock_channels()
    channel = next(
        (c for c in channels if c["id"] == message["channel_id"]), channels[0]
    )

    # Extract code blocks
    code_blocks = connector.extract_code_blocks(message["text"])
    content_type = "code" if code_blocks else "text"

    # Build metadata
    metadata = {
        "slack_channel": message["channel_name"],
        "slack_channel_id": message["channel_id"],
        "slack_thread_ts": message.get("thread_ts"),
        "slack_reactions": [r["name"] for r in message.get("reactions", [])],
        "slack_reply_count": message.get("reply_count", 0),
        "slack_reaction_count": sum(r["count"] for r in message.get("reactions", [])),
        "has_code_blocks": bool(code_blocks),
        "is_thread_reply": message.get("ts") != message.get("thread_ts"),
        "thread_participants": [],
    }

    # Get permissions
    permissions = connector._get_permissions(channel)

    return {
        "id": f"slack_{message['channel_id']}_{message['ts']}",
        "title": f"#{message['channel_name']} - {user_name}: {connector._truncate_text(message['text'], 60)}",
        "raw_content": message["text"],
        "content_type": content_type,
        "file_type": "md",
        "url": connector.get_message_url(message["channel_id"], message["ts"]),
        "created_at": int(float(message["ts"])),
        "modified_at": int(float(message["ts"])),
        "owner": message["user"],
        "contributors": [message["user"]],
        "permissions": permissions,
        "metadata": metadata,
    }


class MockGeminiService:
    """Mock Gemini service for testing without API key"""

    async def generate_embedding(self, content: str, task_type: str = None):
        """Generate mock embedding"""
        import hashlib

        # Generate deterministic embedding based on content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        seed = int(content_hash[:8], 16)

        import random

        random.seed(seed)
        return [random.random() for _ in range(768)]

    async def analyze_code(self, code: str, language: str = None):
        """Mock code analysis"""
        return {"purpose": "Mock code analysis", "concepts": ["testing", "demo"]}


if __name__ == "__main__":
    asyncio.run(main())
