"""
Tools for Notion - Page management, database operations, and content manipulation

IMPORTANT: Type Annotation Guidelines
--------------------------------------
When defining tool parameters with Field():
- If Field has `default=None`, the parameter type MUST be `Optional[Type]`
- If Field has a non-None default, the parameter type can be just `Type`
- Example CORRECT:
    query: Optional[str] = Field(default=None, ...)
- Example WRONG:
    query: str = Field(default=None, ...)  # Type error! str can't be None

This applies to all optional parameters including filters, search fields, etc.
Pydantic will raise ValidationError if type annotations don't match Field defaults.
"""

import json
from typing import Optional, Dict, Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.api_clients.notion_client import NotionAPIClient
from mcp_server.schemas.notion_schemas import (
    SearchPagesInput,
    SearchPagesOutput,
    GetPageInput,
    GetPageOutput,
    ListDatabasesInput,
    ListDatabasesOutput,
    GetDatabaseInput,
    GetDatabaseOutput,
    QueryDatabaseInput,
    QueryDatabaseOutput,
    CreatePageInput,
    CreatePageOutput,
    UpdatePageInput,
    UpdatePageOutput,
    GetPageContentInput,
    GetPageContentOutput,
    AppendToPageInput,
    AppendToPageOutput,
)


def create_notion_tools(notion_client: NotionAPIClient) -> FastMCP:
    """
    Create FastMCP instance with Notion tools.

    Args:
        notion_client: Initialized Notion API client

    Returns:
        FastMCP instance with registered Notion tools
    """
    mcp = FastMCP("notion")

    # ========================================================================
    # Search and Discovery Tools
    # ========================================================================

    @mcp.tool(tags={"notion", "search"})
    def search_pages(
        query: Optional[str] = Field(
            default=None,
            description="Search query to filter by title (leave empty for all)",
        ),
        filter_type: Optional[str] = Field(
            default=None,
            description="Filter by type: 'page' or 'database' (leave empty for both)",
        ),
        limit: int = Field(
            default=10,
            description="Maximum results to return (1-100, default: 10)",
        ),
    ) -> SearchPagesOutput:
        """
        Search for pages and databases in Notion workspace.

        Searches across all accessible pages and databases by title. Useful for
        discovering content, finding specific pages, or listing all databases.
        Results include page/database ID, URL, and title.

        Args:
            query: Search query to filter by title (optional)
            filter_type: Filter by type - 'page' or 'database' (optional)
            limit: Maximum results to return (1-100, default: 10)

        Returns:
            Response containing:
            - count: Number of results found
            - results: List of search results with id, url, title, and type
        """
        try:
            params = SearchPagesInput(query=query, filter_type=filter_type, limit=limit)

            results = notion_client.search(
                query=params.query, filter_type=params.filter_type, limit=params.limit
            )

            return SearchPagesOutput(count=len(results), results=results)

        except Exception as e:
            raise ToolError(f"Failed to search pages: {str(e)}")

    # ========================================================================
    # Page Operations
    # ========================================================================

    @mcp.tool(tags={"notion", "pages", "read"})
    def get_page(
        page_id: str = Field(..., description="Page ID to retrieve", min_length=1),
    ) -> GetPageOutput:
        """
        Get detailed information about a specific Notion page.

        Retrieves page metadata including properties, parent, timestamps, and URL.
        Returns null if the page is not found or not accessible.

        Args:
            page_id: Page ID to retrieve (required)

        Returns:
            Response containing:
            - page: Page object with properties, timestamps, and URL or null if not found
        """
        try:
            params = GetPageInput(page_id=page_id)
            page = notion_client.get_page(params.page_id)

            return GetPageOutput(page=page)

        except Exception as e:
            raise ToolError(f"Failed to get page: {str(e)}")

    @mcp.tool(tags={"notion", "pages", "write"})
    def create_page(
        parent_type: str = Field(..., description="Parent type: 'database' or 'page'"),
        parent_id: str = Field(
            ..., description="Parent database or page ID", min_length=1
        ),
        properties: str = Field(
            ...,
            description="Page properties as JSON string (format depends on database schema)",
        ),
        content_blocks: Optional[str] = Field(
            default=None,
            description="Optional content blocks as JSON array (Notion block format)",
        ),
    ) -> CreatePageOutput:
        """
        Create a new page in a database or as a child page.

        Creates a new Notion page with specified properties. When creating in a database,
        properties must match the database schema. Content blocks can be added during
        creation or later using append_to_page.

        IMPORTANT:
        - properties must be valid JSON matching the target database/page schema
        - For database pages, check database schema using get_database first
        - content_blocks must be valid Notion block objects if provided

        Args:
            parent_type: Parent type - 'database' or 'page' (required)
            parent_id: Parent database or page ID (required)
            properties: Page properties as JSON string (required)
            content_blocks: Optional content blocks as JSON array

        Returns:
            Response containing:
            - success: Boolean indicating if creation was successful
            - page: Created page object with ID and URL
            - message: Status message
        """
        try:
            # Parse JSON inputs
            props = json.loads(properties)
            blocks = json.loads(content_blocks) if content_blocks else None

            params = CreatePageInput(
                parent_type=parent_type,
                parent_id=parent_id,
                properties=props,
                content_blocks=blocks,
            )

            page = notion_client.create_page(
                parent_type=params.parent_type,
                parent_id=params.parent_id,
                properties=params.properties,
                content_blocks=params.content_blocks,
            )

            return CreatePageOutput(
                success=True,
                page=page,
                message=f"Successfully created page: {page.url}",
            )

        except json.JSONDecodeError as e:
            raise ToolError(f"Invalid JSON in properties or content_blocks: {str(e)}")
        except Exception as e:
            raise ToolError(f"Failed to create page: {str(e)}")

    @mcp.tool(tags={"notion", "pages", "write"})
    def update_page(
        page_id: str = Field(..., description="Page ID to update", min_length=1),
        properties: str = Field(..., description="Properties to update as JSON string"),
    ) -> UpdatePageOutput:
        """
        Update properties of an existing Notion page.

        Updates page properties such as title, status, dates, etc. Only specified
        properties are updated; others remain unchanged. Properties must match the
        database schema if the page is in a database.

        Args:
            page_id: Page ID to update (required)
            properties: Properties to update as JSON string (required)

        Returns:
            Response containing:
            - success: Boolean indicating if update was successful
            - page: Updated page object or null if not found
            - message: Status message
        """
        try:
            props = json.loads(properties)

            params = UpdatePageInput(page_id=page_id, properties=props)

            page = notion_client.update_page(
                page_id=params.page_id, properties=params.properties
            )

            if not page:
                return UpdatePageOutput(
                    success=False, page=None, message=f"Page {page_id} not found"
                )

            return UpdatePageOutput(
                success=True,
                page=page,
                message=f"Successfully updated page: {page.url}",
            )

        except json.JSONDecodeError as e:
            raise ToolError(f"Invalid JSON in properties: {str(e)}")
        except Exception as e:
            raise ToolError(f"Failed to update page: {str(e)}")

    # ========================================================================
    # Database Operations
    # ========================================================================

    @mcp.tool(tags={"notion", "database", "read"})
    def list_databases(
        limit: int = Field(
            default=10,
            description="Maximum databases to return (1-100, default: 10)",
        ),
    ) -> ListDatabasesOutput:
        """
        List all databases accessible to the Notion integration.

        Retrieves all databases that the integration has access to. Useful for
        discovering available databases and their IDs for querying or creating pages.

        Args:
            limit: Maximum databases to return (1-100, default: 10)

        Returns:
            Response containing:
            - count: Number of databases found
            - databases: List of database objects with ID, title, and schema
        """
        try:
            params = ListDatabasesInput(limit=limit)
            databases = notion_client.list_databases(limit=params.limit)

            return ListDatabasesOutput(count=len(databases), databases=databases)

        except Exception as e:
            raise ToolError(f"Failed to list databases: {str(e)}")

    @mcp.tool(tags={"notion", "database", "read"})
    def get_database(
        database_id: str = Field(..., description="Database ID", min_length=1),
    ) -> GetDatabaseOutput:
        """
        Get database schema and properties.

        Retrieves detailed database information including the schema (properties/columns).
        Essential for understanding what properties are required when creating pages
        in this database.

        Args:
            database_id: Database ID (required)

        Returns:
            Response containing:
            - database: Database object with schema, title, and properties
        """
        try:
            params = GetDatabaseInput(database_id=database_id)
            database = notion_client.get_database(params.database_id)

            return GetDatabaseOutput(database=database)

        except Exception as e:
            raise ToolError(f"Failed to get database: {str(e)}")

    @mcp.tool(tags={"notion", "database", "query"})
    def query_database(
        database_id: str = Field(..., description="Database ID to query", min_length=1),
        filter_json: Optional[str] = Field(
            default=None,
            description="Filter as JSON string (Notion filter format, optional)",
        ),
        limit: int = Field(
            default=10,
            description="Maximum pages to return (1-100, default: 10)",
        ),
    ) -> QueryDatabaseOutput:
        """
        Query database for pages matching filter criteria.

        Retrieves pages from a database, optionally filtered by property values.
        Useful for finding specific records, getting all entries, or filtering by
        status, dates, or other properties.

        Args:
            database_id: Database ID to query (required)
            filter_json: Filter as JSON string in Notion filter format (optional)
            limit: Maximum pages to return (1-100, default: 10)

        Returns:
            Response containing:
            - count: Number of pages found
            - pages: List of page objects from the database
        """
        try:
            filter_dict = json.loads(filter_json) if filter_json else None

            params = QueryDatabaseInput(
                database_id=database_id, filter_json=filter_json, limit=limit
            )

            pages = notion_client.query_database(
                database_id=params.database_id,
                filter_dict=filter_dict,
                limit=params.limit,
            )

            return QueryDatabaseOutput(count=len(pages), pages=pages)

        except json.JSONDecodeError as e:
            raise ToolError(f"Invalid JSON in filter: {str(e)}")
        except Exception as e:
            raise ToolError(f"Failed to query database: {str(e)}")

    # ========================================================================
    # Content/Block Operations
    # ========================================================================

    @mcp.tool(tags={"notion", "blocks", "read"})
    def get_page_content(
        page_id: str = Field(
            ..., description="Page ID to get content from", min_length=1
        ),
    ) -> GetPageContentOutput:
        """
        Get all content blocks from a Notion page.

        Retrieves all child blocks (content) of a page. Blocks can be paragraphs,
        headings, lists, code blocks, images, etc. Useful for reading page content
        or understanding page structure.

        Args:
            page_id: Page ID to get content from (required)

        Returns:
            Response containing:
            - count: Number of blocks
            - blocks: List of block objects with type and content
        """
        try:
            params = GetPageContentInput(page_id=page_id)
            blocks = notion_client.get_blocks(params.page_id)

            return GetPageContentOutput(count=len(blocks), blocks=blocks)

        except Exception as e:
            raise ToolError(f"Failed to get page content: {str(e)}")

    @mcp.tool(tags={"notion", "blocks", "write"})
    def append_to_page(
        page_id: str = Field(..., description="Page ID to append to", min_length=1),
        blocks: str = Field(
            ...,
            description="List of block objects as JSON array (Notion block format)",
        ),
    ) -> AppendToPageOutput:
        """
        Append content blocks to a Notion page.

        Adds new content blocks to the end of a page. Blocks can be paragraphs,
        headings, lists, code blocks, callouts, etc. This is how you add content
        to pages programmatically.

        Common block types:
        - paragraph: {"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "text"}}]}}
        - heading_2: {"object": "block", "type": "heading_2", "heading_2": {"rich_text": [{"text": {"content": "text"}}]}}
        - bulleted_list_item: {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": [{"text": {"content": "text"}}]}}

        Args:
            page_id: Page ID to append to (required)
            blocks: List of block objects as JSON array (required)

        Returns:
            Response containing:
            - success: Boolean indicating if blocks were appended
            - count: Number of blocks appended
            - message: Status message
        """
        try:
            blocks_list = json.loads(blocks)

            params = AppendToPageInput(page_id=page_id, blocks=blocks_list)

            count = notion_client.append_blocks(
                block_id=params.page_id, children=params.blocks
            )

            return AppendToPageOutput(
                success=True,
                count=count,
                message=f"Successfully appended {count} blocks to page",
            )

        except json.JSONDecodeError as e:
            raise ToolError(f"Invalid JSON in blocks: {str(e)}")
        except Exception as e:
            raise ToolError(f"Failed to append blocks: {str(e)}")

    return mcp
