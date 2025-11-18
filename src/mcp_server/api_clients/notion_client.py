"""
Notion API client for MCP server.

Provides Notion API operations using notion-client library.
Implements core functions needed for Notion MCP tools.
"""

from typing import List, Optional, Dict, Any, Literal
from notion_client import Client as NotionClient
from notion_client.errors import APIResponseError

from mcp_server.schemas.notion_schemas import (
    NotionPage,
    NotionDatabase,
    NotionBlock,
    SearchResult,
)


class NotionAPIClient:
    """
    Notion API client using notion-client SDK.

    Provides simplified interface for Notion operations needed by MCP tools.
    """

    def __init__(self, token: str):
        """
        Initialize Notion API client.

        Args:
            token: Notion integration token
        """
        self.token = token
        self.client = NotionClient(auth=token)

    def health_check(self) -> bool:
        """
        Check if Notion API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Try to search - simplest API call
            self.client.search(page_size=1)
            return True
        except Exception:
            return False

    # ========================================================================
    # Search Operations
    # ========================================================================

    def search(
        self,
        query: Optional[str] = None,
        filter_type: Optional[Literal["page", "database"]] = None,
        limit: int = 10,
    ) -> List[SearchResult]:
        """
        Search for pages and databases.

        Args:
            query: Search query (searches titles)
            filter_type: Filter by 'page' or 'database'
            limit: Maximum results to return

        Returns:
            List of search results
        """
        kwargs: Dict[str, Any] = {"page_size": min(limit, 100)}

        if query:
            kwargs["query"] = query

        if filter_type:
            kwargs["filter"] = {"value": filter_type, "property": "object"}

        response = self.client.search(**kwargs)

        results = []
        for item in response.get("results", []):
            # Extract title from properties
            title = self._extract_title(item)

            results.append(
                SearchResult(
                    object=item["object"],
                    id=item["id"],
                    url=item.get("url", ""),
                    title=title,
                )
            )

        return results

    # ========================================================================
    # Page Operations
    # ========================================================================

    def get_page(self, page_id: str) -> Optional[NotionPage]:
        """
        Get page details.

        Args:
            page_id: Page ID

        Returns:
            Page object or None if not found
        """
        try:
            response = self.client.pages.retrieve(page_id)
            return self._convert_page(response)
        except APIResponseError as e:
            if e.code == "object_not_found":
                return None
            raise

    def create_page(
        self,
        parent_type: Literal["database", "page"],
        parent_id: str,
        properties: Dict[str, Any],
        content_blocks: Optional[List[Dict[str, Any]]] = None,
    ) -> NotionPage:
        """
        Create a new page.

        Args:
            parent_type: 'database' or 'page'
            parent_id: Parent database or page ID
            properties: Page properties
            content_blocks: Optional content blocks

        Returns:
            Created page object
        """
        parent_key = "database_id" if parent_type == "database" else "page_id"
        parent = {parent_key: parent_id}

        kwargs: Dict[str, Any] = {
            "parent": parent,
            "properties": properties,
        }

        if content_blocks:
            kwargs["children"] = content_blocks

        response = self.client.pages.create(**kwargs)
        return self._convert_page(response)

    def update_page(
        self, page_id: str, properties: Dict[str, Any]
    ) -> Optional[NotionPage]:
        """
        Update page properties.

        Args:
            page_id: Page ID
            properties: Properties to update

        Returns:
            Updated page or None if not found
        """
        try:
            response = self.client.pages.update(page_id, properties=properties)
            return self._convert_page(response)
        except APIResponseError as e:
            if e.code == "object_not_found":
                return None
            raise

    # ========================================================================
    # Database Operations
    # ========================================================================

    def list_databases(self, limit: int = 10) -> List[NotionDatabase]:
        """
        List all databases accessible to the integration.

        Args:
            limit: Maximum databases to return

        Returns:
            List of databases
        """
        # Notion API no longer supports filter.value="database"
        # Notion now returns databases as 'data_source' type in some cases
        # We search all items and filter manually
        response = self.client.search(page_size=min(limit * 2, 100))

        databases = []
        for item in response.get("results", []):
            # Accept both 'database' and 'data_source' types
            if item.get("object") in ["database", "data_source"]:
                databases.append(self._convert_database(item))
                if len(databases) >= limit:
                    break

        return databases

    def get_database(self, database_id: str) -> Optional[NotionDatabase]:
        """
        Get database details and schema.

        Args:
            database_id: Database ID

        Returns:
            Database object or None if not found
        """
        try:
            response = self.client.databases.retrieve(database_id)
            return self._convert_database(response)
        except APIResponseError as e:
            if e.code == "object_not_found":
                return None
            raise

    def query_database(
        self,
        database_id: str,
        filter_dict: Optional[Dict[str, Any]] = None,
        limit: int = 10,
    ) -> List[NotionPage]:
        """
        Query database for pages.

        Args:
            database_id: Database ID
            filter_dict: Notion filter object
            limit: Maximum pages to return

        Returns:
            List of pages from database
        """
        # Note: In newer notion-client versions, query is on data_sources, not databases
        # data_sources.query takes data_source_id as first positional argument
        kwargs: Dict[str, Any] = {
            "page_size": min(limit, 100),
        }

        if filter_dict:
            kwargs["filter"] = filter_dict

        try:
            # New API: data_sources.query(data_source_id, **kwargs)
            response = self.client.data_sources.query(database_id, **kwargs)
        except AttributeError:
            # Old API fallback: databases.query(database_id=..., **kwargs)
            kwargs["database_id"] = database_id
            response = self.client.databases.query(**kwargs)

        pages = []
        for item in response.get("results", []):
            pages.append(self._convert_page(item))

        return pages

    # ========================================================================
    # Block Operations (Page Content)
    # ========================================================================

    def get_blocks(self, block_id: str) -> List[NotionBlock]:
        """
        Get child blocks (page content).

        Args:
            block_id: Block/Page ID

        Returns:
            List of child blocks
        """
        response = self.client.blocks.children.list(block_id)

        blocks = []
        for item in response.get("results", []):
            blocks.append(self._convert_block(item))

        return blocks

    def append_blocks(self, block_id: str, children: List[Dict[str, Any]]) -> int:
        """
        Append blocks to a page.

        Args:
            block_id: Page/Block ID to append to
            children: List of block objects

        Returns:
            Number of blocks appended
        """
        self.client.blocks.children.append(block_id, children=children)
        return len(children)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _convert_page(self, page_data: Dict[str, Any]) -> NotionPage:
        """Convert Notion API page to Pydantic model."""
        from datetime import datetime

        return NotionPage(
            id=page_data["id"],
            created_time=datetime.fromisoformat(
                page_data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                page_data["last_edited_time"].replace("Z", "+00:00")
            ),
            archived=page_data.get("archived", False),
            url=page_data.get("url", ""),
            parent=page_data.get("parent", {}),
            properties=page_data.get("properties", {}),
        )

    def _convert_database(self, db_data: Dict[str, Any]) -> NotionDatabase:
        """Convert Notion API database to Pydantic model."""
        from datetime import datetime

        # Extract title
        title = ""
        if "title" in db_data and db_data["title"]:
            title = db_data["title"][0].get("plain_text", "")

        return NotionDatabase(
            id=db_data["id"],
            title=title,
            created_time=datetime.fromisoformat(
                db_data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                db_data["last_edited_time"].replace("Z", "+00:00")
            ),
            archived=db_data.get("archived", False),
            url=db_data.get("url", ""),
            properties=db_data.get("properties", {}),
        )

    def _convert_block(self, block_data: Dict[str, Any]) -> NotionBlock:
        """Convert Notion API block to Pydantic model."""
        from datetime import datetime

        block_type = block_data["type"]
        content = block_data.get(block_type, {})

        return NotionBlock(
            id=block_data["id"],
            type=block_type,
            created_time=datetime.fromisoformat(
                block_data["created_time"].replace("Z", "+00:00")
            ),
            last_edited_time=datetime.fromisoformat(
                block_data["last_edited_time"].replace("Z", "+00:00")
            ),
            archived=block_data.get("archived", False),
            has_children=block_data.get("has_children", False),
            content=content,
        )

    def _extract_title(self, item: Dict[str, Any]) -> str:
        """Extract title from page or database object."""
        # For databases
        if item["object"] == "database" and "title" in item:
            if item["title"]:
                return item["title"][0].get("plain_text", "Untitled")
            return "Untitled"

        # For pages - look in properties
        if item["object"] == "page" and "properties" in item:
            props = item["properties"]

            # Common title property names
            for key in ["Name", "Title", "title", "name"]:
                if key in props:
                    prop = props[key]
                    if prop["type"] == "title" and prop.get("title"):
                        return prop["title"][0].get("plain_text", "Untitled")

        return "Untitled"
