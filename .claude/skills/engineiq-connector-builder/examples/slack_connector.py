"""
EngineIQ Slack Connector Example

Complete implementation of a Slack connector following the standard pattern.
"""

from typing import AsyncGenerator, Dict, List
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from connectors.base_connector import BaseConnector
import re


class SlackConnector(BaseConnector):
    """Slack connector for indexing messages, threads, and files"""

    def __init__(self, credentials: dict, gemini_service, qdrant_service):
        super().__init__(credentials, gemini_service, qdrant_service)
        self.client = AsyncWebClient(token=credentials["bot_token"])

    async def authenticate(self) -> bool:
        """Authenticate with Slack using bot token"""
        try:
            response = await self.client.auth_test()
            return response["ok"]
        except SlackApiError as e:
            print(f"Slack authentication failed: {e.response['error']}")
            return False

    async def get_content(self, since: int = None) -> AsyncGenerator[Dict, None]:
        """Fetch all messages from all accessible channels"""
        # Get all channels
        channels = await self.get_channels()

        for channel in channels:
            print(f"Fetching messages from #{channel['name']}...")

            # Get messages from channel
            async for message in self.get_channel_messages(channel["id"], since):
                # Get thread if exists
                if message.get("thread_ts"):
                    thread_messages = await self.get_thread_messages(
                        channel["id"],
                        message["thread_ts"]
                    )
                    # Combine thread into single document
                    full_text = f"{message['text']}\n\nThread:\n" + "\n".join([
                        f"{m.get('user', 'unknown')}: {m['text']}"
                        for m in thread_messages
                    ])
                else:
                    full_text = message["text"]

                # Extract code blocks
                code_blocks = self.extract_code_blocks(full_text)
                content_type = "code" if code_blocks else "text"

                # Determine sensitivity based on channel
                is_private = channel.get("is_private", False)
                sensitivity = "internal" if is_private else "public"

                yield {
                    "id": f"slack_{channel['id']}_{message['ts']}",
                    "title": f"#{channel['name']} - {message.get('user', 'unknown')}",
                    "raw_content": full_text,
                    "content_type": content_type,
                    "file_type": "md",
                    "url": self.get_message_url(channel["id"], message["ts"]),
                    "created_at": int(float(message["ts"])),
                    "modified_at": int(float(message.get("latest_reply", message["ts"]))),
                    "owner": message.get("user", "unknown"),
                    "contributors": self.get_thread_participants(message),
                    "permissions": {
                        "public": not is_private,
                        "teams": [channel.get("team_id", "")],
                        "users": [],
                        "sensitivity": sensitivity,
                        "offshore_restricted": False,
                        "third_party_restricted": is_private
                    },
                    "metadata": {
                        "slack_channel": channel["name"],
                        "slack_thread_ts": message.get("thread_ts"),
                        "slack_reactions": [
                            r["name"] for r in message.get("reactions", [])
                        ]
                    }
                }

    async def get_channels(self) -> List[dict]:
        """Get all channels bot has access to"""
        try:
            result = await self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True,
                limit=200
            )
            return result["channels"]
        except SlackApiError as e:
            print(f"Error fetching channels: {e}")
            return []

    async def get_channel_messages(
        self,
        channel_id: str,
        since: int = None
    ) -> AsyncGenerator[dict, None]:
        """Get messages from a channel with pagination"""
        cursor = None

        while True:
            try:
                result = await self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(since) if since else None,
                    cursor=cursor,
                    limit=200
                )

                for message in result["messages"]:
                    # Only yield regular messages (not system messages)
                    if message.get("type") == "message" and not message.get("subtype"):
                        yield message

                # Check for next page
                cursor = result.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

            except SlackApiError as e:
                print(f"Error fetching messages from {channel_id}: {e}")
                break

    async def get_thread_messages(self, channel_id: str, thread_ts: str) -> List[dict]:
        """Get all messages in a thread"""
        try:
            result = await self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )
            # Skip parent message (first in list)
            return result["messages"][1:]
        except SlackApiError as e:
            print(f"Error fetching thread {thread_ts}: {e}")
            return []

    def extract_code_blocks(self, text: str) -> List[str]:
        """Extract ```code blocks``` from message"""
        return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

    def get_message_url(self, channel_id: str, ts: str) -> str:
        """Construct Slack message URL"""
        # Replace with your workspace URL
        workspace = self.credentials.get("workspace", "yourworkspace")
        ts_clean = ts.replace(".", "")
        return f"https://{workspace}.slack.com/archives/{channel_id}/p{ts_clean}"

    def get_thread_participants(self, message: dict) -> List[str]:
        """Get all users who participated in thread"""
        participants = [message.get("user", "unknown")]

        if message.get("replies"):
            for reply in message["replies"]:
                participants.append(reply["user"])

        return list(set(participants))

    def get_action_type(self, item: dict) -> str:
        """Determine action type for expertise tracking"""
        # First message in thread = authored, replies = answered
        if "Thread:" in item["raw_content"]:
            return "answered"
        return "authored"

    def calculate_contribution_score(self, item: dict) -> float:
        """Calculate contribution score for Slack messages"""
        # Answers in threads are more valuable than standalone messages
        if self.get_action_type(item) == "answered":
            return 1.5
        return 1.0

    async def watch_for_changes(self):
        """
        Set up real-time updates using Slack Events API.

        In production, this would be a webhook endpoint in your FastAPI app.
        For development/testing, we use polling.
        """
        import asyncio

        print(f"Starting Slack change watcher (polling mode)...")

        while True:
            try:
                # Get last sync time
                last_sync = await self.get_last_sync_time()

                # Sync new messages
                await self.sync(since=last_sync)

                # Save current time
                await self.save_last_sync_time(int(asyncio.get_event_loop().time()))

            except Exception as e:
                print(f"Error in Slack watcher: {e}")

            # Poll every 5 minutes
            await asyncio.sleep(300)

    async def get_last_sync_time(self) -> int:
        """Get timestamp of last sync (implement based on your storage)"""
        # Could store in Redis, database, or file
        # For now, return 0 to sync all messages
        return 0

    async def save_last_sync_time(self, timestamp: int):
        """Save timestamp of current sync"""
        # Implement based on your storage
        pass


# Example usage
if __name__ == "__main__":
    import asyncio
    from services.gemini_service import GeminiService
    from services.qdrant_service import QdrantService

    async def main():
        # Initialize services
        gemini = GeminiService(api_key="your_gemini_key")
        qdrant = QdrantService(url="your_qdrant_url", api_key="your_qdrant_key")

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
            print("✓ Authenticated with Slack")

            # Sync all messages
            await slack.sync()

            print("✓ Sync complete!")
        else:
            print("✗ Authentication failed")

    asyncio.run(main())
