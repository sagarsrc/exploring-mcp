"""
Test suite for Slack write operations.

Tests slack_notify tool to send messages to Slack channels.
These tests will send actual messages to your Slack workspace.

IMPORTANT: Make sure you have:
1. SLACK_TOKEN environment variable set (bot token starting with xoxb-)
2. The Slack bot installed in your workspace
3. The bot added to a test channel
4. A channel ID to send test messages to

Setup:
    export SLACK_TOKEN="xoxb-your-bot-token"

Usage:
    # Send test notification to a specific channel
    python -m src.tests.slack.write C1234567890

    # Or use channel name with # prefix
    python -m src.tests.slack.write "#test-channel"
"""

import os
import sys
import asyncio
from datetime import datetime

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.slack_client import SlackAPIClient
from mcp_server.tools.slack_tools import create_slack_tools

console = Console()


async def test_send_notification(client: Client, channel: str):
    """Test slack_notify tool."""
    console.print(Panel.fit("STEP 1: Sending a test notification", style="bold blue"))

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message_text = f"""🧪 *MCP Slack Integration Test*

This is a test notification sent at *{timestamp}* by the Slack MCP test suite.

*Test Purpose:*
Testing the `slack_notify` tool from the MCP Slack integration.

*Message Formatting Examples:*
• *Bold text*
• _Italic text_
• `Code snippet`
• <https://github.com|Link to GitHub>

---
✅ If you can read this, the Slack integration is working!
🤖 _This is an automated test message._
"""

        console.print(f"[cyan]Sending notification to:[/cyan] {channel}")

        notify_result = await client.call_tool(
            name="slack_notify",
            arguments={
                "channel": channel,
                "message": message_text,
            },
        )

        result_data = notify_result.data
        success = result_data.success if hasattr(result_data, "success") else False
        message = result_data.message if hasattr(result_data, "message") else ""
        ts = result_data.ts if hasattr(result_data, "ts") else None

        if success:
            console.print("[green]✅ Notification sent successfully![/green]")
            console.print(f"   [bold]Message:[/bold] {message}")
            console.print(f"   [bold]Timestamp:[/bold] {ts}")
            return ts
        else:
            console.print(f"[red]❌ Failed to send notification: {message}[/red]")
            return None

    except Exception as e:
        console.print(f"[red]❌ ERROR sending notification: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


async def test_send_threaded_reply(client: Client, channel: str, thread_ts: str):
    """Test sending a threaded reply."""
    console.print(Panel.fit("STEP 2: Sending a threaded reply", style="bold blue"))

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reply_text = f"""📊 *Test Results Summary*

*All write operations tested:*
1. ✅ `slack_notify` - Basic notification successful
2. ✅ `slack_notify` (threaded) - Thread reply successful

*Test completed at:* `{timestamp}`

---
🎉 *All Slack MCP tools are working correctly!*
"""

        console.print(
            f"[cyan]Sending threaded reply to message {thread_ts[:10]}...[/cyan]"
        )

        reply_result = await client.call_tool(
            name="slack_notify",
            arguments={
                "channel": channel,
                "message": reply_text,
                "thread_ts": thread_ts,
            },
        )

        result_data = reply_result.data
        success = result_data.success if hasattr(result_data, "success") else False
        message = result_data.message if hasattr(result_data, "message") else ""

        if success:
            console.print("[green]✅ Threaded reply sent successfully![/green]")
            console.print(f"   [bold]Message:[/bold] {message}")
            return True
        else:
            console.print(f"[red]❌ Failed to send threaded reply: {message}[/red]")
            return False

    except Exception as e:
        console.print(f"[red]❌ ERROR sending threaded reply: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_write_operations(channel: str):
    """Test all write operations."""

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

    console.print("[green]✅ Connected to Slack API[/green]")
    console.print(f"   [bold]Target channel:[/bold] {channel}\n")

    success = True

    async with Client(mcp) as client:
        # Test 1: Send notification
        thread_ts = await test_send_notification(client, channel)

        if not thread_ts:
            success = False
        else:
            # Test 2: Send threaded reply
            console.print()
            if not await test_send_threaded_reply(client, channel, thread_ts):
                success = False

    # Summary
    if success:
        console.print()

        # Create summary table
        table = Table(title="✅ Test Summary", style="green")
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        table.add_row("slack_notify (basic)", "✅ Sent test notification")
        table.add_row("slack_notify (threaded)", "✅ Sent threaded reply")

        console.print(table)

        console.print(f"\n[bold]Test channel:[/bold] {channel}")
        console.print(
            "\n[cyan]💡 Check your Slack workspace to see the test messages![/cyan]"
        )
        console.print(
            "\n[cyan]💡 You can run read.py to list all available channels:[/cyan]"
        )
        console.print("   python -m src.tests.slack.read")

    return success


def main():
    """Main entry point."""
    console.rule("[bold blue]🚀 SLACK WRITE OPERATIONS TEST SUITE 🚀[/bold blue]")
    console.print()

    # Get channel from command line
    if len(sys.argv) < 2:
        console.print("[red]❌ No channel specified[/red]")
        console.print("\n[yellow]Please provide a channel ID or name:[/yellow]")
        console.print("   [cyan]python -m src.tests.slack.write C1234567890[/cyan]")
        console.print('   [cyan]python -m src.tests.slack.write "#test-channel"[/cyan]')
        console.print("\n[yellow]To find channel IDs, run:[/yellow]")
        console.print("   [cyan]python -m src.tests.slack.read[/cyan]")
        return

    channel = sys.argv[1]

    console.print(f"[cyan]🎯 Target channel:[/cyan] {channel}")
    console.print("[cyan]📝 Test plan:[/cyan]")
    console.print("   [bold]1.[/bold] Send a test notification to the channel")
    console.print("   [bold]2.[/bold] Send a threaded reply to the notification\n")

    # Run async tests
    success = asyncio.run(test_write_operations(channel))

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
