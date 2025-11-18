"""
Test suite for Notion write operations.

Tests create_page, update_page, and append_to_page tools.
These tests will modify pages in your Notion workspace.

IMPORTANT: Make sure you have:
1. NOTION_TOKEN environment variable set
2. A test page in your Notion workspace
3. The integration added to it

Setup:
    export NOTION_TOKEN="your_notion_token"

Usage:
    # Test with a specific parent page (recommended)
    python -m src.tests.notion.write 2afaa83fae948098bda6de87a3a6295a
"""

import os
import json
import sys
import asyncio
from datetime import datetime

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


async def test_create_update_append(client: Client, parent_page_id: str):
    """Test complete workflow: create a child page, then update and append to it."""

    parent_page_id = format_notion_id(parent_page_id)
    console.print(
        f"[cyan]📄 Creating child page under parent: {parent_page_id}[/cyan]\n"
    )

    # Step 1: Create a new child page
    console.print(Panel.fit("STEP 1: Creating a new child page", style="bold blue"))

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        page_title = f"MCP Test Page - {timestamp}"

        # Page properties - for child pages, we just need a title
        page_properties = {"title": {"title": [{"text": {"content": page_title}}]}}

        # Initial content blocks
        content_blocks = [
            {
                "object": "block",
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [
                        {"text": {"content": "🧪 MCP Notion Integration Test"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "text": {
                                "content": f"This page was created at {timestamp} by the Notion MCP test suite."
                            }
                        }
                    ]
                },
            },
        ]

        console.print(f"[cyan]📄 Creating child page:[/cyan] '{page_title}'")

        create_result = await client.call_tool(
            name="create_page",
            arguments={
                "parent_type": "page",
                "parent_id": parent_page_id,
                "properties": json.dumps(page_properties),
                "content_blocks": json.dumps(content_blocks),
            },
        )

        # Result data is a Pydantic model - access attributes directly
        result_data = create_result.data
        created_page = result_data.page if hasattr(result_data, "page") else result_data
        new_page_id = (
            created_page.id if hasattr(created_page, "id") else created_page["id"]
        )
        new_page_url = (
            created_page.url if hasattr(created_page, "url") else created_page["url"]
        )

        console.print(f"[green]✅ Child page created successfully![/green]")
        console.print(f"   [bold]Page ID:[/bold] {new_page_id}")
        console.print(
            f"   [bold]URL:[/bold] [link={new_page_url}]{new_page_url}[/link]"
        )

    except Exception as e:
        console.print(f"[red]❌ ERROR creating page: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False

    # Step 2: Update the newly created page
    console.print()
    console.print(
        Panel.fit("STEP 2: Updating the newly created page", style="bold blue")
    )

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updated_title = f"{page_title} ✅ [Updated]"

        update_properties = {"title": {"title": [{"text": {"content": updated_title}}]}}

        console.print(f"[cyan]✏️  Updating title to:[/cyan] '{updated_title}'")

        update_result = await client.call_tool(
            name="update_page",
            arguments={
                "page_id": new_page_id,
                "properties": json.dumps(update_properties),
            },
        )

        result_data = update_result.data
        message = result_data.message if hasattr(result_data, "message") else "Updated"
        console.print(f"[green]✅ Page updated successfully![/green]")
        console.print(f"   [bold]Message:[/bold] {message}")

    except Exception as e:
        console.print(f"[red]❌ ERROR updating page: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False

    # Step 3: Append more content to the page
    console.print()
    console.print(
        Panel.fit("STEP 3: Appending content blocks to the page", style="bold blue")
    )

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        new_blocks = [
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {"rich_text": [{"text": {"content": "✅ Test Results"}}]},
            },
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {"text": {"content": f"Content appended at {timestamp}"}}
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "✅ create_page - Successfully created child page"
                            }
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "✅ update_page - Successfully updated page title"
                            }
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "✅ append_to_page - Successfully appended content"
                            }
                        }
                    ]
                },
            },
            {
                "object": "block",
                "type": "heading_3",
                "heading_3": {"rich_text": [{"text": {"content": "Code Sample"}}]},
            },
            {
                "object": "block",
                "type": "code",
                "code": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "# All write operations working perfectly!\nfrom mcp_server.tools.notion_tools import create_notion_tools\n\nprint('Notion MCP integration test passed ✅')"
                            }
                        }
                    ],
                    "language": "python",
                },
            },
            {"object": "block", "type": "divider", "divider": {}},
        ]

        console.print(f"[cyan]📝 Appending {len(new_blocks)} content blocks...[/cyan]")

        append_result = await client.call_tool(
            name="append_to_page",
            arguments={"page_id": new_page_id, "blocks": json.dumps(new_blocks)},
        )

        result_data = append_result.data
        message = result_data.message if hasattr(result_data, "message") else "Appended"
        count = result_data.count if hasattr(result_data, "count") else len(new_blocks)
        console.print(f"[green]✅ Content appended successfully![/green]")
        console.print(f"   [bold]Message:[/bold] {message}")
        console.print(f"   [bold]Blocks added:[/bold] {count}")

    except Exception as e:
        console.print(f"[red]❌ ERROR appending content: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False

    # Summary
    console.print()
    table = Table(title="✅ Test Summary", style="green")
    table.add_column("Operation", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")

    table.add_row("create_page", "✅ Created child page with initial content")
    table.add_row("update_page", "✅ Updated page title")
    table.add_row("append_to_page", "✅ Added 8 content blocks")

    console.print(table)

    console.print(
        f"\n[bold]📄 Test page created:[/bold] [link={new_page_url}]{new_page_url}[/link]"
    )
    console.print(f"   [bold]Page ID:[/bold] {new_page_id}")
    console.print("\n[cyan]💡 You can now run read.py to verify the content:[/cyan]")
    console.print(f"   python -m src.tests.notion.read {new_page_id}")

    return True


async def test_write_operations(parent_page_id: str = None):
    """Test all write operations."""

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

    if not parent_page_id:
        console.print("[red]❌ No parent page ID provided[/red]")
        console.print("\n[yellow]Please provide a parent page ID:[/yellow]")
        console.print(
            "   [cyan]python -m src.tests.notion.write 2afaa83fae948098bda6de87a3a6295a[/cyan]"
        )
        console.print(
            "\n[yellow]The test will create a child page under this parent page,[/yellow]"
        )
        console.print("[yellow]then update it and append content to it.[/yellow]")
        return False

    console.print(f"[cyan]🎯 Parent page ID:[/cyan] {parent_page_id}")
    console.print("[cyan]📝 Test plan:[/cyan]")
    console.print("   [bold]1.[/bold] Create a new child page under the parent")
    console.print("   [bold]2.[/bold] Update the child page's title")
    console.print("   [bold]3.[/bold] Append additional content to the child page\n")

    # Create client and run tests
    async with Client(mcp) as client:
        success = await test_create_update_append(client, parent_page_id)

    return success


def main():
    """Main entry point."""
    console.rule("[bold blue]🚀 NOTION WRITE OPERATIONS TEST SUITE 🚀[/bold blue]")
    console.print()

    # Get target ID from command line
    parent_page_id = sys.argv[1] if len(sys.argv) > 1 else None

    # Run async tests
    success = asyncio.run(test_write_operations(parent_page_id))

    console.print()
    if success:
        console.print(
            Panel.fit("[bold green]✅ ALL TESTS PASSED![/bold green]", style="green")
        )
    else:
        console.print(Panel.fit("[bold red]❌ TESTS FAILED[/bold red]", style="red"))
    console.print()


if __name__ == "__main__":
    main()
