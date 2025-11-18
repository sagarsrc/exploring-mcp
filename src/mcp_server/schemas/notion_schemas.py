"""
Pydantic schemas for Notion API responses.

These models define the structure of data returned from Notion API
and used throughout the MCP server.
"""

from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer


# ============================================================================
# Core Notion Models
# ============================================================================


class NotionUser(BaseModel):
    """Notion user model."""

    id: str = Field(..., description="User ID")
    name: Optional[str] = Field(None, description="User name")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")


class NotionParent(BaseModel):
    """Parent reference for pages/databases."""

    type: Literal["database_id", "page_id", "workspace"] = Field(
        ..., description="Parent type"
    )
    database_id: Optional[str] = Field(
        None, description="Database ID if parent is database"
    )
    page_id: Optional[str] = Field(None, description="Page ID if parent is page")


class NotionPage(BaseModel):
    """Notion page model."""

    id: str = Field(..., description="Page ID")
    created_time: datetime = Field(..., description="Creation timestamp")
    last_edited_time: datetime = Field(..., description="Last edit timestamp")
    archived: bool = Field(False, description="Archived status")
    url: str = Field(..., description="Page URL")
    parent: Dict[str, Any] = Field(..., description="Parent object")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Page properties"
    )

    @field_serializer("created_time", "last_edited_time", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class NotionDatabase(BaseModel):
    """Notion database model."""

    id: str = Field(..., description="Database ID")
    title: str = Field(..., description="Database title")
    created_time: datetime = Field(..., description="Creation timestamp")
    last_edited_time: datetime = Field(..., description="Last edit timestamp")
    archived: bool = Field(False, description="Archived status")
    url: str = Field(..., description="Database URL")
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Database schema"
    )

    @field_serializer("created_time", "last_edited_time", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class NotionBlock(BaseModel):
    """Notion block model (content block)."""

    id: str = Field(..., description="Block ID")
    type: str = Field(..., description="Block type")
    created_time: datetime = Field(..., description="Creation timestamp")
    last_edited_time: datetime = Field(..., description="Last edit timestamp")
    archived: bool = Field(False, description="Archived status")
    has_children: bool = Field(False, description="Has child blocks")
    content: Dict[str, Any] = Field(default_factory=dict, description="Block content")

    @field_serializer("created_time", "last_edited_time", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class SearchResult(BaseModel):
    """Search result item."""

    object: str = Field(
        ..., description="Object type (page, database, data_source, etc)"
    )
    id: str = Field(..., description="Object ID")
    url: str = Field(..., description="Object URL")
    title: str = Field(..., description="Title extracted from properties")


# ============================================================================
# Tool Input/Output Schemas
# ============================================================================


class SearchPagesInput(BaseModel):
    """Input schema for search_pages tool."""

    query: Optional[str] = Field(
        default=None, description="Search query (searches titles)"
    )
    filter_type: Optional[Literal["page", "database"]] = Field(
        default=None, description="Filter by object type"
    )
    limit: int = Field(
        default=10, description="Maximum results to return (1-100)", gt=0, le=100
    )


class SearchPagesOutput(BaseModel):
    """Output schema for search_pages tool."""

    count: int = Field(..., description="Number of results found")
    results: List[SearchResult] = Field(..., description="Search results")


class GetPageInput(BaseModel):
    """Input schema for get_page tool."""

    page_id: str = Field(..., description="Page ID", min_length=1)


class GetPageOutput(BaseModel):
    """Output schema for get_page tool."""

    page: Optional[NotionPage] = Field(
        ..., description="Page details or null if not found"
    )


class ListDatabasesInput(BaseModel):
    """Input schema for list_databases tool."""

    limit: int = Field(
        default=10, description="Maximum databases to return (1-100)", gt=0, le=100
    )


class ListDatabasesOutput(BaseModel):
    """Output schema for list_databases tool."""

    count: int = Field(..., description="Number of databases found")
    databases: List[NotionDatabase] = Field(..., description="List of databases")


class GetDatabaseInput(BaseModel):
    """Input schema for get_database tool."""

    database_id: str = Field(..., description="Database ID", min_length=1)


class GetDatabaseOutput(BaseModel):
    """Output schema for get_database tool."""

    database: Optional[NotionDatabase] = Field(
        ..., description="Database details or null if not found"
    )


class QueryDatabaseInput(BaseModel):
    """Input schema for query_database tool."""

    database_id: str = Field(..., description="Database ID", min_length=1)
    filter_json: Optional[str] = Field(
        default=None, description="Filter as JSON string (Notion filter format)"
    )
    limit: int = Field(
        default=10, description="Maximum pages to return (1-100)", gt=0, le=100
    )


class QueryDatabaseOutput(BaseModel):
    """Output schema for query_database tool."""

    count: int = Field(..., description="Number of pages found")
    pages: List[NotionPage] = Field(..., description="List of pages from database")


class CreatePageInput(BaseModel):
    """Input schema for create_page tool."""

    parent_type: Literal["database", "page"] = Field(
        ..., description="Parent type: 'database' or 'page'"
    )
    parent_id: str = Field(..., description="Parent database or page ID", min_length=1)
    properties: Dict[str, Any] = Field(
        ..., description="Page properties as JSON (depends on database schema)"
    )
    content_blocks: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Optional content blocks to add"
    )


class CreatePageOutput(BaseModel):
    """Output schema for create_page tool."""

    success: bool = Field(..., description="Whether page was created successfully")
    page: Optional[NotionPage] = Field(None, description="Created page details")
    message: str = Field(..., description="Status message")


class UpdatePageInput(BaseModel):
    """Input schema for update_page tool."""

    page_id: str = Field(..., description="Page ID to update", min_length=1)
    properties: Dict[str, Any] = Field(..., description="Properties to update as JSON")


class UpdatePageOutput(BaseModel):
    """Output schema for update_page tool."""

    success: bool = Field(..., description="Whether update was successful")
    page: Optional[NotionPage] = Field(None, description="Updated page details")
    message: str = Field(..., description="Status message")


class GetPageContentInput(BaseModel):
    """Input schema for get_page_content tool."""

    page_id: str = Field(..., description="Page ID", min_length=1)


class GetPageContentOutput(BaseModel):
    """Output schema for get_page_content tool."""

    count: int = Field(..., description="Number of blocks")
    blocks: List[NotionBlock] = Field(..., description="List of content blocks")


class AppendToPageInput(BaseModel):
    """Input schema for append_to_page tool."""

    page_id: str = Field(..., description="Page ID to append to", min_length=1)
    blocks: List[Dict[str, Any]] = Field(
        ..., description="List of block objects to append (Notion block format)"
    )


class AppendToPageOutput(BaseModel):
    """Output schema for append_to_page tool."""

    success: bool = Field(..., description="Whether blocks were appended successfully")
    count: int = Field(..., description="Number of blocks appended")
    message: str = Field(..., description="Status message")
