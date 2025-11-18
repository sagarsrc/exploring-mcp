"""
Test suite for Slack read operations.

Tests list_channels tool to discover available Slack channels.

IMPORTANT: Make sure you have:
1. SLACK_TOKEN environment variable set (bot token starting with xoxb-)
2. The Slack bot installed in your workspace
3. The bot added to some channels

Setup:
    export SLACK_TOKEN="xoxb-your-bot-token"

Usage:
    # Run list_channels test
    python -m src.tests.slack.read
"""

import os
import asyncio

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.slack_client import SlackAPIClient
from mcp_server.tools.slack_tools import create_slack_tools

console = Console()


async def test_list_channels(client: Client):
    """Test list_channels tool."""
    console.print()
    console.print(Panel.fit("TEST: list_channels", style="bold cyan"))

    try:
        # Test 1: List all non-archived channels
        console.print("\n[cyan]1. Listing all non-archived channels...[/cyan]")
        result = await client.call_tool(
            name="list_channels",
            arguments={
                "exclude_archived": True,
                "include_private": True,
                "limit": 50,
            }
        )
        result_data = result.data
        count = result_data.count if hasattr(result_data, 'count') else 0
        channels = result_data.channels if hasattr(result_data, 'channels') else []

        console.print(f"[green]✅ Found {count} channel(s):[/green]\n")

        # Create table for better visualization
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Name", style="cyan", no_wrap=True)
        table.add_column("ID", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Member", justify="center")
        table.add_column("Members", justify="right")

        for channel in channels[:20]:  # Show first 20
            name = channel.name if hasattr(channel, 'name') else channel.get('name', '')
            ch_id = channel.id if hasattr(channel, 'id') else channel.get('id', '')
            is_private = channel.is_private if hasattr(channel, 'is_private') else channel.get('is_private', False)
            is_member = channel.is_member if hasattr(channel, 'is_member') else channel.get('is_member', False)
            num_members = channel.num_members if hasattr(channel, 'num_members') else channel.get('num_members', 0)

            ch_type = "Private" if is_private else "Public"
            member_status = "[green]✓[/green]" if is_member else "[red]✗[/red]"

            table.add_row(
                f"#{name}",
                ch_id,
                ch_type,
                member_status,
                str(num_members)
            )

        console.print(table)

        if count > 20:
            console.print(f"\n   [yellow]... and {count - 20} more channels[/yellow]")

        # Test 2: List only public channels
        console.print("\n[cyan]2. Listing only public channels...[/cyan]")
        result2 = await client.call_tool(
            name="list_channels",
            arguments={
                "exclude_archived": True,
                "include_private": False,
                "limit": 50,
            }
        )
        result_data2 = result2.data
        count2 = result_data2.count if hasattr(result_data2, 'count') else 0

        console.print(f"[green]✅ Found {count2} public channel(s)[/green]")

        # Return first channel for use in write tests
        if channels:
            return channels[0].id if hasattr(channels[0], 'id') else channels[0].get('id')
        return None

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_channels: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return None


async def test_all_read_operations():
    """Run all read operation tests."""

    # Initialize client
    token = os.getenv("SLACK_TOKEN")
    if not token:
        console.print("[red]❌ ERROR: SLACK_TOKEN environment variable not set[/red]")
        console.print("   [yellow]Run: export SLACK_TOKEN='xoxb-your-token'[/yellow]")
        return False

    console.print("[cyan]🔧 Initializing Slack client...[/cyan]")
    slack_client = SlackAPIClient(token=token)
    mcp = create_slack_tools(slack_client)

    # Health check
    if not slack_client.health_check():
        console.print("[red]❌ ERROR: Cannot connect to Slack API[/red]")
        console.print("   [yellow]Check your SLACK_TOKEN is valid[/yellow]")
        return False

    console.print("[green]✅ Connected to Slack API[/green]\n")

    results = []

    async with Client(mcp) as client:
        # Test list_channels
        channel_id = await test_list_channels(client)
        results.append(("list_channels", channel_id is not None))

        # Store channel_id for potential use in write tests
        if channel_id:
            console.print(f"\n[cyan]💡 Example channel ID for testing:[/cyan] {channel_id}")
            console.print(f"   [yellow]You can use this with write.py[/yellow]")

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
    console.rule("[bold cyan]🔍 SLACK READ OPERATIONS TEST SUITE 🔍[/bold cyan]")
    console.print()

    # Run async tests
    success = asyncio.run(test_all_read_operations())

    console.print()
    if success:
        console.print(Panel.fit("[bold green]✅ ALL TESTS PASSED![/bold green]", style="green"))
    else:
        console.print(Panel.fit("[bold yellow]⚠️  SOME TESTS FAILED OR SKIPPED[/bold yellow]", style="yellow"))
    console.print()


if __name__ == "__main__":
    main()
