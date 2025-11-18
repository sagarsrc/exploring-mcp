"""
Slack API client for MCP server.

Provides Slack API operations using slack_sdk library.
Implements core functions needed for Slack MCP tools.
"""

from typing import List, Optional
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from mcp_server.schemas.slack_schemas import SlackChannel, SlackMessage


class SlackAPIClient:
    """
    Slack API client using slack_sdk.

    Provides simplified interface for Slack operations needed by MCP tools.
    """

    def __init__(self, token: str):
        """
        Initialize Slack API client.

        Args:
            token: Slack bot token (starts with xoxb-)
        """
        self.token = token
        self.client = WebClient(token=token)

    def health_check(self) -> bool:
        """
        Check if Slack API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Test authentication
            response = self.client.auth_test()
            return response["ok"]
        except Exception:
            return False

    # ========================================================================
    # Channel Operations
    # ========================================================================

    def list_channels(
        self,
        exclude_archived: bool = True,
        types: str = "public_channel,private_channel",
        limit: int = 100,
    ) -> List[SlackChannel]:
        """
        List all channels the bot has access to.

        Args:
            exclude_archived: Exclude archived channels (default True)
            types: Comma-separated list of types (default: public_channel,private_channel)
            limit: Maximum channels to return (default 100)

        Returns:
            List of Slack channels
        """
        try:
            response = self.client.conversations_list(
                exclude_archived=exclude_archived,
                types=types,
                limit=limit,
            )

            channels = []
            for channel in response.get("channels", []):
                channels.append(
                    SlackChannel(
                        id=channel["id"],
                        name=channel["name"],
                        is_channel=channel.get("is_channel", True),
                        is_private=channel.get("is_private", False),
                        is_archived=channel.get("is_archived", False),
                        is_member=channel.get("is_member", False),
                        num_members=channel.get("num_members", 0),
                    )
                )

            return channels

        except SlackApiError as e:
            raise Exception(f"Slack API error: {e.response['error']}")

    # ========================================================================
    # Message Operations
    # ========================================================================

    def post_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
    ) -> SlackMessage:
        """
        Post a message to a Slack channel.

        Args:
            channel: Channel ID (e.g., C1234567890) or name (e.g., #general)
            text: Message text (supports Slack markdown)
            thread_ts: Optional thread timestamp to reply to a thread

        Returns:
            Posted message details
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text,
            }

            if thread_ts:
                kwargs["thread_ts"] = thread_ts

            response = self.client.chat_postMessage(**kwargs)

            return SlackMessage(
                channel=response["channel"],
                ts=response["ts"],
                text=text,
                success=True,
                message="Message posted successfully",
            )

        except SlackApiError as e:
            return SlackMessage(
                channel=channel,
                ts="",
                text=text,
                success=False,
                message=f"Failed to post message: {e.response['error']}",
            )
