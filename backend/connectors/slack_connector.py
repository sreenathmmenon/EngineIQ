"""
EngineIQ Slack Connector

Complete Slack integration for indexing messages, threads, and tracking expertise.
"""

from typing import AsyncGenerator, Dict, List, Optional
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from .base_connector import BaseConnector
import re
import logging
import asyncio

logger = logging.getLogger(__name__)


class SlackConnector(BaseConnector):
    """
    Slack connector for indexing messages, threads, and files.

    Features:
    - Fetches messages from all accessible channels
    - Preserves thread context
    - Extracts code blocks separately
    - Tracks reactions (indicates valuable content)
    - Respects channel permissions
    - Flags confidential channels for human-in-loop
    - Updates expertise map for answerers
    """

    def __init__(self, credentials: dict, gemini_service, qdrant_service):
        """
        Initialize Slack connector.

        Args:
            credentials: Dict with:
                - bot_token: Slack bot token (xoxb-...)
                - workspace: Workspace name (optional)
        """
        super().__init__(credentials, gemini_service, qdrant_service)
        self.client = AsyncWebClient(token=credentials["bot_token"])
        self.workspace = credentials.get("workspace", "yourworkspace")
        self.user_cache = {}  # Cache for user ID -> name mapping

    async def authenticate(self) -> bool:
        """
        Authenticate with Slack using bot token.

        Returns:
            bool: True if authentication successful
        """
        try:
            response = await self.client.auth_test()
            if response["ok"]:
                logger.info(f"✓ Authenticated with Slack as {response['user']}")
                return True
            return False
        except (SlackApiError, Exception) as e:
            logger.error(f"Slack authentication failed: {e}")
            return False

    async def get_content(
        self, since: Optional[int] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Fetch all messages from all accessible channels.

        Args:
            since: Unix timestamp to fetch messages after this time

        Yields:
            dict: Standardized content item
        """
        # Get all channels bot has access to
        channels = await self.get_channels()
        logger.info(f"Found {len(channels)} accessible Slack channels")

        for channel in channels:
            logger.info(f"Fetching messages from #{channel['name']}...")

            async for message in self.get_messages(channel["id"], since):
                try:
                    # Get thread if exists
                    thread_messages = []
                    if message.get("thread_ts") and message.get("reply_count", 0) > 0:
                        thread_messages = await self.get_thread_messages(
                            channel["id"], message["thread_ts"]
                        )

                    # Build full text with thread
                    full_text = await self._build_full_text(
                        message, thread_messages, channel
                    )

                    # Extract code blocks
                    code_blocks = self.extract_code_blocks(full_text)

                    # Determine content type
                    content_type = "code" if code_blocks else "text"

                    # Get metadata
                    metadata = await self.extract_metadata(
                        message, channel, thread_messages
                    )

                    # Get permissions
                    permissions = self._get_permissions(channel)

                    # Get contributors
                    contributors = self._get_thread_participants(message, thread_messages)

                    # Get user name
                    user_name = await self.get_user_name(message.get("user", "unknown"))

                    yield {
                        "id": f"slack_{channel['id']}_{message['ts']}",
                        "title": f"#{channel['name']} - {user_name}: {self._truncate_text(message.get('text', ''), 60)}",
                        "raw_content": full_text,
                        "content_type": content_type,
                        "file_type": "md",
                        "url": self.get_message_url(channel["id"], message["ts"]),
                        "created_at": int(float(message["ts"])),
                        "modified_at": int(
                            float(message.get("latest_reply", message["ts"]))
                        ),
                        "owner": message.get("user", "unknown"),
                        "contributors": contributors,
                        "permissions": permissions,
                        "metadata": metadata,
                    }

                except Exception as e:
                    logger.error(
                        f"Error processing message {message.get('ts')}: {e}"
                    )
                    continue

    async def get_channels(self) -> List[dict]:
        """
        Get all channels bot has access to.

        Returns:
            List[dict]: List of channel objects
        """
        try:
            result = await self.client.conversations_list(
                types="public_channel,private_channel",
                exclude_archived=True,
                limit=200,
            )
            return result["channels"]
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")
            return []

    async def get_messages(
        self, channel_id: str, since: Optional[int] = None
    ) -> AsyncGenerator[dict, None]:
        """
        Get messages from a channel with pagination.

        Args:
            channel_id: Slack channel ID
            since: Unix timestamp to fetch messages after

        Yields:
            dict: Message object
        """
        cursor = None

        while True:
            try:
                result = await self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(since) if since else None,
                    cursor=cursor,
                    limit=200,
                )

                for message in result["messages"]:
                    # Only yield regular messages (not system messages)
                    if message.get("type") == "message" and not message.get(
                        "subtype"
                    ):
                        yield message

                # Check for next page
                cursor = result.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break

            except SlackApiError as e:
                logger.error(f"Error fetching messages from {channel_id}: {e}")
                break

    async def get_thread_messages(
        self, channel_id: str, thread_ts: str
    ) -> List[dict]:
        """
        Get all messages in a thread.

        Args:
            channel_id: Slack channel ID
            thread_ts: Thread timestamp

        Returns:
            List[dict]: List of thread messages (excluding parent)
        """
        try:
            result = await self.client.conversations_replies(
                channel=channel_id, ts=thread_ts
            )
            # Skip parent message (first in list)
            return result["messages"][1:] if len(result["messages"]) > 1 else []
        except SlackApiError as e:
            logger.error(f"Error fetching thread {thread_ts}: {e}")
            return []

    def extract_code_blocks(self, text: str) -> List[str]:
        """
        Extract ```code blocks``` from message.

        Args:
            text: Message text

        Returns:
            List[str]: List of code blocks
        """
        return re.findall(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)

    async def extract_metadata(
        self, message: dict, channel: dict, thread_messages: List[dict]
    ) -> dict:
        """
        Extract Slack-specific metadata.

        Args:
            message: Message object
            channel: Channel object
            thread_messages: List of thread messages

        Returns:
            dict: Metadata dictionary
        """
        return {
            "slack_channel": channel["name"],
            "slack_channel_id": channel["id"],
            "slack_thread_ts": message.get("thread_ts"),
            "slack_reactions": [r["name"] for r in message.get("reactions", [])],
            "slack_reply_count": message.get("reply_count", 0),
            "slack_reaction_count": sum(
                r["count"] for r in message.get("reactions", [])
            ),
            "has_code_blocks": "```" in message.get("text", ""),
            "is_thread_reply": bool(
                message.get("thread_ts") and message["ts"] != message.get("thread_ts")
            ),
            "thread_participants": [
                m.get("user", "unknown") for m in thread_messages
            ],
        }

    def get_message_url(self, channel_id: str, ts: str) -> str:
        """
        Construct Slack message URL.

        Args:
            channel_id: Slack channel ID
            ts: Message timestamp

        Returns:
            str: Message permalink
        """
        ts_clean = ts.replace(".", "")
        return f"https://{self.workspace}.slack.com/archives/{channel_id}/p{ts_clean}"

    async def get_user_name(self, user_id: str) -> str:
        """
        Get user display name from user ID with caching.

        Args:
            user_id: Slack user ID

        Returns:
            str: User display name or user_id if not found
        """
        if user_id in self.user_cache:
            return self.user_cache[user_id]

        try:
            result = await self.client.users_info(user=user_id)
            name = result["user"].get("real_name") or result["user"].get("name", user_id)
            self.user_cache[user_id] = name
            return name
        except (SlackApiError, Exception) as e:
            logger.warning(f"Could not fetch user name for {user_id}: {e}")
            return user_id

    def get_action_type(self, item: dict) -> str:
        """
        Determine action type for expertise tracking.

        Args:
            item: Content item

        Returns:
            str: "answered" for thread replies, "authored" for original messages
        """
        # Thread replies are answers
        if item["metadata"].get("is_thread_reply"):
            return "answered"
        # Messages with threads are questions that got answered
        elif item["metadata"].get("slack_reply_count", 0) > 0:
            return "asked"
        return "authored"

    def calculate_contribution_score(self, item: dict) -> float:
        """
        Calculate contribution score for Slack messages.

        Scoring:
        - Answers in threads: 1.5 (more valuable)
        - Messages with reactions: +0.1 per reaction (up to +1.0)
        - Messages with code blocks: +0.5
        - Standalone messages: 1.0

        Args:
            item: Content item

        Returns:
            float: Contribution score
        """
        base_score = 1.0

        # Answers are more valuable
        if self.get_action_type(item) == "answered":
            base_score = 1.5

        # Reactions indicate valuable content
        reaction_count = item["metadata"].get("slack_reaction_count", 0)
        reaction_bonus = min(reaction_count * 0.1, 1.0)

        # Code blocks add value
        code_bonus = 0.5 if item["metadata"].get("has_code_blocks") else 0.0

        return base_score + reaction_bonus + code_bonus

    async def track_expertise(self, item: dict, embedding: List[float]):
        """
        Track expertise for message contributors.

        Tracks both the original poster and thread responders.

        Args:
            item: Content item
            embedding: Content embedding vector
        """
        # Track original poster
        await self.update_expertise_map(item, item["raw_content"], embedding)

        # Track thread participants separately if they answered
        if item["metadata"].get("thread_participants"):
            for participant in item["metadata"]["thread_participants"]:
                if participant != item["owner"]:
                    # Create a variant item for the responder
                    responder_item = item.copy()
                    responder_item["contributors"] = [participant]
                    responder_item["metadata"] = item["metadata"].copy()
                    responder_item["metadata"]["is_thread_reply"] = True

                    await self.update_expertise_map(
                        responder_item, item["raw_content"], embedding
                    )

    def should_trigger_approval(self, item: dict) -> bool:
        """
        Determine if message should trigger human-in-loop approval.

        Triggers on:
        - Channels with "confidential" in name
        - Private channels with sensitive keywords
        - Messages with restricted sensitivity

        Args:
            item: Content item

        Returns:
            bool: True if approval needed
        """
        channel_name = item["metadata"].get("slack_channel", "").lower()

        # Check for confidential in channel name
        if "confidential" in channel_name:
            logger.info(
                f"Human-in-loop triggered for confidential channel: #{channel_name}"
            )
            return True

        # Check for other sensitive keywords
        sensitive_keywords = ["secret", "private-", "restricted-", "internal-"]
        if any(keyword in channel_name for keyword in sensitive_keywords):
            logger.info(
                f"Human-in-loop triggered for sensitive channel: #{channel_name}"
            )
            return True

        # Check base class conditions (permissions sensitivity)
        if super().should_trigger_approval(item):
            return True

        return False

    async def watch_for_changes(self):
        """
        Set up real-time updates using polling.

        In production, use Slack Events API webhook.
        For now, poll every 5 minutes.
        """
        logger.info("Starting Slack change watcher (polling mode)...")

        last_sync = int(asyncio.get_event_loop().time())

        while True:
            try:
                await asyncio.sleep(300)  # 5 minutes

                logger.info("Checking for new Slack messages...")
                count = await self.sync(since=last_sync)
                logger.info(f"✓ Synced {count} new messages")

                last_sync = int(asyncio.get_event_loop().time())

            except Exception as e:
                logger.error(f"Error in Slack watcher: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    # Private helper methods

    async def _build_full_text(
        self, message: dict, thread_messages: List[dict], channel: dict
    ) -> str:
        """Build full text including thread context."""
        text = message.get("text", "")

        if thread_messages:
            thread_text = "\n\n=== Thread ===\n"
            for msg in thread_messages:
                user_name = await self.get_user_name(msg.get("user", "unknown"))
                thread_text += f"\n{user_name}: {msg.get('text', '')}"

            text = text + thread_text

        return text

    def _get_permissions(self, channel: dict) -> dict:
        """Get permissions structure for channel."""
        is_private = channel.get("is_private", False)

        # Check for confidential in name
        channel_name = channel.get("name", "").lower()
        is_confidential = "confidential" in channel_name

        return {
            "public": not is_private,
            "teams": [channel.get("context_team_id", "")],
            "users": [],
            "sensitivity": "confidential" if is_confidential else "internal",
            "offshore_restricted": is_confidential,
            "third_party_restricted": is_private or is_confidential,
        }

    def _get_thread_participants(
        self, message: dict, thread_messages: List[dict]
    ) -> List[str]:
        """Get all unique users who participated in the conversation."""
        participants = {message.get("user", "unknown")}

        for msg in thread_messages:
            participants.add(msg.get("user", "unknown"))

        return list(participants)

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to max_length with ellipsis."""
        text = text.replace("\n", " ").strip()
        if len(text) <= max_length:
            return text
        return text[: max_length - 3] + "..."
