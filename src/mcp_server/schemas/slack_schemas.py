"""
Pydantic schemas for Slack API objects.

Defines data models for Slack channels, messages, and other objects
used by the MCP Slack tools.
"""

from pydantic import BaseModel, Field
from typing import Optional


class SlackChannel(BaseModel):
    """Slack channel information."""

    id: str = Field(..., description="Channel ID (e.g., C1234567890)")
    name: str = Field(..., description="Channel name without # prefix")
    is_channel: bool = Field(True, description="Whether this is a channel")
    is_private: bool = Field(False, description="Whether this is a private channel")
    is_archived: bool = Field(False, description="Whether the channel is archived")
    is_member: bool = Field(False, description="Whether the bot is a member")
    num_members: int = Field(0, description="Number of members in the channel")


class SlackMessage(BaseModel):
    """Slack message response."""

    channel: str = Field(..., description="Channel where message was posted")
    ts: str = Field(..., description="Message timestamp (unique ID)")
    text: str = Field(..., description="Message text")
    success: bool = Field(
        ..., description="Whether the message was posted successfully"
    )
    message: str = Field(..., description="Success or error message")


class SlackChannelListResponse(BaseModel):
    """Response for list_channels tool."""

    count: int = Field(..., description="Number of channels returned")
    channels: list[SlackChannel] = Field(..., description="List of channels")


class SlackNotifyResponse(BaseModel):
    """Response for slack_notify tool."""

    success: bool = Field(..., description="Whether notification was sent")
    message: str = Field(..., description="Success or error message")
    channel: str = Field(..., description="Channel where notification was sent")
    ts: Optional[str] = Field(None, description="Message timestamp if successful")
