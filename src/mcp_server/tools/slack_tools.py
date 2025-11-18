"""
Tools for Slack - Channel discovery and notification

IMPORTANT: Type Annotation Guidelines
--------------------------------------
When defining tool parameters with Field():
- If Field has `default=None`, the parameter type MUST be `Optional[Type]`
- If Field has a non-None default, the parameter type can be just `Type`
- Example CORRECT:
    thread_ts: Optional[str] = Field(default=None, ...)
- Example WRONG:
    thread_ts: str = Field(default=None, ...)  # Type error! str can't be None

This applies to all optional parameters including filters, search fields, etc.
Pydantic will raise ValidationError if type annotations don't match Field defaults.
"""

from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.api_clients.slack_client import SlackAPIClient
from mcp_server.schemas.slack_schemas import (
    SlackChannelListResponse,
    SlackNotifyResponse,
)


def create_slack_tools(slack_client: SlackAPIClient) -> FastMCP:
    """
    Create FastMCP instance with Slack tools.

    Args:
        slack_client: Initialized Slack API client

    Returns:
        FastMCP instance with registered Slack tools
    """
    mcp = FastMCP("slack")

    # ========================================================================
    # Channel Discovery Tools
    # ========================================================================

    @mcp.tool(tags={"slack", "channels", "discovery"})
    def list_channels(
        exclude_archived: bool = Field(
            default=True,
            description="Exclude archived channels (default: True)",
        ),
        include_private: bool = Field(
            default=True,
            description="Include private channels bot has access to (default: True)",
        ),
        limit: int = Field(
            default=100,
            description="Maximum number of channels to return (default: 100)",
        ),
    ) -> SlackChannelListResponse:
        """
        List all Slack channels the bot has access to.

        Retrieves channels to help discover channel IDs needed for sending notifications.
        By default, shows all public and private channels the bot is part of, excluding
        archived channels. Each channel includes its ID, name, member status, and metadata.

        Use this tool to:
        - Find channel IDs for use with slack_notify
        - See which channels the bot can access
        - Check if the bot is a member of specific channels

        Args:
            exclude_archived: Exclude archived channels (default: True)
            include_private: Include private channels bot has access to (default: True)
            limit: Maximum number of channels to return (default: 100)

        Returns:
            Response containing:
            - count: Number of channels found
            - channels: List of channel objects with:
                - id: Channel ID (e.g., C1234567890) - use this for slack_notify
                - name: Channel name without # prefix
                - is_private: Whether this is a private channel
                - is_archived: Whether the channel is archived
                - is_member: Whether the bot is a member of this channel
                - num_members: Number of members in the channel
        """
        try:
            types = "public_channel"
            if include_private:
                types += ",private_channel"

            channels = slack_client.list_channels(
                exclude_archived=exclude_archived,
                types=types,
                limit=limit,
            )

            return SlackChannelListResponse(
                count=len(channels),
                channels=channels,
            )

        except Exception as e:
            raise ToolError(f"Failed to list Slack channels: {str(e)}")

    # ========================================================================
    # Notification Tools
    # ========================================================================

    @mcp.tool(tags={"slack", "messaging", "notifications"})
    def slack_notify(
        channel: str = Field(
            ...,
            description="Channel ID (e.g., C1234567890) or name (e.g., #general). Use list_channels to find IDs.",
        ),
        message: str = Field(
            ...,
            description="Message text to send (supports Slack markdown formatting)",
            min_length=1,
        ),
        thread_ts: Optional[str] = Field(
            default=None,
            description="Optional thread timestamp to reply in a thread",
        ),
    ) -> SlackNotifyResponse:
        """
        Send a notification message to a Slack channel.

        Posts a message to the specified Slack channel or thread. Messages support Slack's
        markdown-like formatting including bold (*bold*), italic (_italic_), code (`code`),
        and links (<https://example.com|link text>).

        IMPORTANT:
        - The bot must be a member of the channel to post messages
        - Use list_channels tool to find channel IDs
        - For channel names, include the # prefix (e.g., #general)
        - For private channels, the bot must be explicitly invited

        Message Formatting Tips:
        - Bold: *text*
        - Italic: _text_
        - Code: `code`
        - Code block: ```code block```
        - Link: <https://example.com|link text>
        - Mention user: <@U1234567890>
        - Mention channel: <!channel> or <!here>

        Args:
            channel: Channel ID (e.g., C1234567890) or name (e.g., #general)
                    Tip: Use list_channels to find channel IDs
            message: Message text to send (supports Slack markdown, must not be empty)
            thread_ts: Optional thread timestamp to reply in a thread
                      Get this from a previous message's ts value

        Returns:
            Response containing:
            - success: Boolean indicating if message was sent successfully
            - message: Success or error message
            - channel: Channel where notification was sent
            - ts: Message timestamp (unique ID) if successful
        """
        try:
            result = slack_client.post_message(
                channel=channel,
                text=message,
                thread_ts=thread_ts,
            )

            return SlackNotifyResponse(
                success=result.success,
                message=result.message,
                channel=result.channel,
                ts=result.ts if result.success else None,
            )

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages for common issues
            if "channel_not_found" in error_msg:
                raise ToolError(
                    f"Failed to send message: Channel not found. "
                    f"Make sure the channel ID or name is correct. "
                    f"Use list_channels tool to find available channels. "
                    f"Slack error: {error_msg}"
                )
            elif "not_in_channel" in error_msg:
                raise ToolError(
                    f"Failed to send message: Bot is not a member of this channel. "
                    f"Please invite the bot to the channel first. "
                    f"Slack error: {error_msg}"
                )
            elif "is_archived" in error_msg:
                raise ToolError(
                    f"Failed to send message: Channel is archived. "
                    f"Unarchive the channel or use a different channel. "
                    f"Slack error: {error_msg}"
                )
            else:
                raise ToolError(f"Failed to send Slack notification: {error_msg}")

    return mcp
