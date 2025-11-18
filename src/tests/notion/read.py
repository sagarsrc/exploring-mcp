"""
Test suite for Notion read operations.

Tests search_pages, get_page, get_page_content, list_databases,
get_database, and query_database tools.

IMPORTANT: Make sure you have:
1. NOTION_TOKEN environment variable set
2. Some pages/databases in your Notion workspace
3. The integration added to those pages/databases

Setup:
    export NOTION_TOKEN="your_notion_token"

Usage:
    # Run all read tests
    python -m src.tests.notion.read

    # Test reading a specific page
    python -m src.tests.notion.read 2afaa83f-ae94-81d6-937c-f53f0d2f2216
"""

import os
import sys
import asyncio
from typing import Optional

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.notion_client import NotionAPIClient
from mcp_server.tools.notion_tools import create_notion_tools

console = Console()


def format_notion_id(notion_id: str) -> str:
    """
    Format a Notion ID to proper UUID format.

    Notion IDs can be in formats like:
    - 2afaa83fae948098bda6de87a3a6295a (32 chars, no hyphens)
    - 2afaa83f-ae94-8098-bda6-de87a3a6295a (36 chars, with hyphens)

    Args:
        notion_id: Raw Notion ID from URL or other source

    Returns:
        Properly formatted UUID string with hyphens
    """
    # Remove any hyphens first
    clean_id = notion_id.replace("-", "")

    # Add hyphens in UUID format: 8-4-4-4-12
    if len(clean_id) == 32:
        return f"{clean_id[:8]}-{clean_id[8:12]}-{clean_id[12:16]}-{clean_id[16:20]}-{clean_id[20:]}"

    # If it already has hyphens and is correct length, return as-is
    return notion_id


async def test_search_pages(client: Client):
    """Test search_pages tool."""
    console.print()
    console.print(Panel.fit("TEST: search_pages", style="bold cyan"))

    try:
        # Search all
        console.print(
            "\n[cyan]1. Searching all pages and databases (limit 5)...[/cyan]"
        )
        result = await client.call_tool(name="search_pages", arguments={"limit": 5})
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        results = result_data.results if hasattr(result_data, "results") else []

        console.print(f"[green]✅ Found {count} results:[/green]")
        for i, item in enumerate(results, 1):
            item_type = item.object if hasattr(item, "object") else "unknown"
            title = item.title if hasattr(item, "title") else "Untitled"
            item_id = item.id if hasattr(item, "id") else ""
            url = item.url if hasattr(item, "url") else ""
            console.print(f"   [bold]{i}. [{item_type}][/bold] {title}")
            console.print(f"      ID: {item_id}")
            console.print(f"      URL: [link={url}]{url}[/link]")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in search_pages: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_list_databases(client: Client):
    """Test list_databases tool."""
    console.print()
    console.print(Panel.fit("TEST: list_databases", style="bold cyan"))

    try:
        result = await client.call_tool(name="list_databases", arguments={"limit": 10})
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        databases = result_data.databases if hasattr(result_data, "databases") else []

        console.print(f"[green]✅ Found {count} database(s):[/green]\n")
        for i, db in enumerate(databases, 1):
            title = db.title if hasattr(db, "title") else "Untitled"
            db_id = db.id if hasattr(db, "id") else ""
            url = db.url if hasattr(db, "url") else ""
            created = db.created_time if hasattr(db, "created_time") else ""
            console.print(f"   [bold]{i}. {title}[/bold]")
            console.print(f"      ID: {db_id}")
            console.print(f"      URL: [link={url}]{url}[/link]")
            console.print(f"      Created: {created}")
            console.print()

        return databases[0].id if databases and hasattr(databases[0], "id") else None

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_databases: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


async def test_get_database(client: Client, database_id: str):
    """Test get_database tool."""
    console.print()
    console.print(Panel.fit("TEST: get_database", style="bold cyan"))

    try:
        result = await client.call_tool(
            name="get_database", arguments={"database_id": database_id}
        )
        result_data = result.data
        database = (
            result_data.database if hasattr(result_data, "database") else result_data
        )

        title = database.title if hasattr(database, "title") else "Untitled"
        db_id = database.id if hasattr(database, "id") else ""
        url = database.url if hasattr(database, "url") else ""
        created = database.created_time if hasattr(database, "created_time") else ""
        edited = (
            database.last_edited_time if hasattr(database, "last_edited_time") else ""
        )

        console.print(f"[green]✅ Retrieved database:[/green] [bold]{title}[/bold]")
        console.print(f"   [bold]ID:[/bold] {db_id}")
        console.print(f"   [bold]URL:[/bold] [link={url}]{url}[/link]")
        console.print(f"   [bold]Created:[/bold] {created}")
        console.print(f"   [bold]Last edited:[/bold] {edited}")
        console.print("\n   [bold]Properties/Schema:[/bold]")

        properties = database.properties if hasattr(database, "properties") else {}
        if hasattr(properties, "items"):
            prop_items = properties.items()
        elif hasattr(properties, "__dict__"):
            prop_items = properties.__dict__.items()
        else:
            prop_items = []

        for prop_name, prop_data in prop_items:
            prop_type = (
                prop_data.get("type", "unknown")
                if isinstance(prop_data, dict)
                else getattr(prop_data, "type", "unknown")
            )
            console.print(f"      - [cyan]{prop_name}:[/cyan] {prop_type}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_database: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_query_database(client: Client, database_id: str):
    """Test query_database tool."""
    console.print()
    console.print(Panel.fit("TEST: query_database", style="bold cyan"))

    try:
        # Query without filter
        console.print("\n[cyan]1. Querying database without filter (limit 5)...[/cyan]")
        result = await client.call_tool(
            name="query_database", arguments={"database_id": database_id, "limit": 5}
        )
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        pages = result_data.pages if hasattr(result_data, "pages") else []

        console.print(f"[green]✅ Found {count} page(s) in database:[/green]")
        for i, page in enumerate(pages, 1):
            page_id = page.id if hasattr(page, "id") else ""
            url = page.url if hasattr(page, "url") else ""
            created = page.created_time if hasattr(page, "created_time") else ""
            properties = page.properties if hasattr(page, "properties") else {}

            # Get property keys safely
            if hasattr(properties, "keys"):
                prop_keys = list(properties.keys())
            elif hasattr(properties, "__dict__"):
                prop_keys = list(properties.__dict__.keys())
            else:
                prop_keys = []

            console.print(f"\n   [bold]{i}. Page ID:[/bold] {page_id}")
            console.print(f"      [bold]URL:[/bold] [link={url}]{url}[/link]")
            console.print(f"      [bold]Created:[/bold] {created}")
            console.print(f"      [bold]Properties:[/bold] {prop_keys}")

        # Return first page ID if available
        if pages:
            return pages[0].id if hasattr(pages[0], "id") else None
        return None

    except Exception as e:
        console.print(f"[red]❌ ERROR in query_database: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


async def test_get_page(client: Client, page_id: str):
    """Test get_page tool."""
    console.print()
    console.print(Panel.fit("TEST: get_page", style="bold cyan"))

    try:
        page_id = format_notion_id(page_id)
        result = await client.call_tool(name="get_page", arguments={"page_id": page_id})
        result_data = result.data
        page = result_data.page if hasattr(result_data, "page") else result_data

        if not page:
            console.print(
                f"[yellow]⚠️  Page {page_id} not found or not accessible[/yellow]"
            )
            return False

        page_id_val = page.id if hasattr(page, "id") else ""
        url = page.url if hasattr(page, "url") else ""
        created = page.created_time if hasattr(page, "created_time") else ""
        edited = page.last_edited_time if hasattr(page, "last_edited_time") else ""
        archived = page.archived if hasattr(page, "archived") else False

        console.print(f"[green]✅ Retrieved page:[/green]")
        console.print(f"   [bold]ID:[/bold] {page_id_val}")
        console.print(f"   [bold]URL:[/bold] [link={url}]{url}[/link]")
        console.print(f"   [bold]Created:[/bold] {created}")
        console.print(f"   [bold]Last edited:[/bold] {edited}")
        console.print(f"   [bold]Archived:[/bold] {archived}")
        console.print(f"\n   [bold]Properties:[/bold]")

        properties = page.properties if hasattr(page, "properties") else {}
        if hasattr(properties, "items"):
            prop_items = properties.items()
        elif hasattr(properties, "__dict__"):
            prop_items = properties.__dict__.items()
        else:
            prop_items = []

        for prop_name, prop_value in prop_items:
            prop_type = (
                prop_value.get("type", "unknown")
                if isinstance(prop_value, dict)
                else getattr(prop_value, "type", "unknown")
            )
            console.print(f"      - [cyan]{prop_name}:[/cyan] {prop_type}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_page: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_get_page_content(client: Client, page_id: str):
    """Test get_page_content tool."""
    console.print()
    console.print(Panel.fit("TEST: get_page_content", style="bold cyan"))

    try:
        page_id = format_notion_id(page_id)
        result = await client.call_tool(
            name="get_page_content", arguments={"page_id": page_id}
        )
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        blocks = result_data.blocks if hasattr(result_data, "blocks") else []

        console.print(f"[green]✅ Retrieved {count} content block(s):[/green]\n")

        for i, block in enumerate(blocks, 1):
            block_type = block.type if hasattr(block, "type") else "unknown"
            block_id = block.id if hasattr(block, "id") else ""
            has_children = (
                block.has_children if hasattr(block, "has_children") else False
            )

            console.print(f"   [bold]{i}. Block type:[/bold] {block_type}")
            console.print(f"      [bold]ID:[/bold] {block_id}")
            console.print(f"      [bold]Has children:[/bold] {has_children}")

            # Try to show content preview
            content = block.content if hasattr(block, "content") else {}
            if (
                isinstance(content, dict)
                and "rich_text" in content
                and content["rich_text"]
            ):
                text = content["rich_text"][0].get("plain_text", "")
                if text:
                    preview = text[:100] + "..." if len(text) > 100 else text
                    console.print(f"      [bold]Content:[/bold] {preview}")
            console.print()

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_page_content: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_all_read_operations(page_id: Optional[str] = None):
    """Run all read operation tests."""

    # Initialize client
    token = os.getenv("NOTION_TOKEN")
    if not token:
        console.print("[red]❌ ERROR: NOTION_TOKEN environment variable not set[/red]")
        console.print("   [yellow]Run: export NOTION_TOKEN='your_token'[/yellow]")
        return False

    console.print("[cyan]🔧 Initializing Notion client...[/cyan]")
    notion_client = NotionAPIClient(token=token)
    mcp = create_notion_tools(notion_client)

    # Health check
    if not notion_client.health_check():
        console.print("[red]❌ ERROR: Cannot connect to Notion API[/red]")
        return False

    console.print("[green]✅ Connected to Notion API[/green]\n")

    results = []

    async with Client(mcp) as client:
        # Test 1: Search pages
        results.append(("search_pages", await test_search_pages(client)))

        # Test 2: List databases
        db_id = await test_list_databases(client)
        if not db_id:
            console.print(
                "[yellow]⚠️  WARNING: No databases found, skipping database tests[/yellow]"
            )
        else:
            # Test 3: Get database
            results.append(("get_database", await test_get_database(client, db_id)))

            # Test 4: Query database
            queried_page_id = await test_query_database(client, db_id)
            if queried_page_id and not page_id:
                page_id = queried_page_id

        # Test 5 & 6: Get page and content
        if page_id:
            results.append(("get_page", await test_get_page(client, page_id)))
            results.append(
                ("get_page_content", await test_get_page_content(client, page_id))
            )
        else:
            console.print(
                "\n[yellow]⚠️  WARNING: No page ID provided or found, skipping page tests[/yellow]"
            )
            console.print(
                "   [cyan]Run: python -m src.tests.notion.read <page_id>[/cyan]"
            )

    # Summary
    console.print()
    table = Table(title="📊 Test Summary", style="cyan")
    table.add_column("Test", style="cyan", no_wrap=True)
    table.add_column("Status", style="bold")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
        table.add_row(test_name, status)

    console.print(table)
    console.print(f"\n   [bold]Total:[/bold] {passed}/{total} tests passed")

    return passed == total


def main():
    """Main entry point."""
    console.rule("[bold cyan]🔍 NOTION READ OPERATIONS TEST SUITE 🔍[/bold cyan]")
    console.print()

    # Check for page ID argument
    page_id = sys.argv[1] if len(sys.argv) > 1 else None

    if page_id:
        console.print(f"[cyan]📄 Testing with specific page ID: {page_id}[/cyan]\n")

    # Run async tests
    success = asyncio.run(test_all_read_operations(page_id))

    console.print()
    if success:
        console.print(
            Panel.fit("[bold green]✅ ALL TESTS PASSED![/bold green]", style="green")
        )
    else:
        console.print(
            Panel.fit(
                "[bold yellow]⚠️  SOME TESTS FAILED OR SKIPPED[/bold yellow]",
                style="yellow",
            )
        )
    console.print()


if __name__ == "__main__":
    main()
