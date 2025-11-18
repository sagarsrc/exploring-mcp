"""
Test suite for GitHub write operations.

Tests create_issue, add_issue_comment, and update_issue_status tools.
These tests will create actual issues and comments in your GitHub repository.

IMPORTANT: Make sure you have:
1. GITHUB_TOKEN environment variable set
2. GITHUB_USERNAME environment variable set
3. REPO_NAME environment variable set
4. Proper permissions on the repository

Setup:
    export GITHUB_TOKEN="your_github_token"
    export GITHUB_USERNAME="your_username"
    export REPO_NAME="your_repo"

Usage:
    # Run all write tests (creates test issue)
    python -m src.tests.github.write

    # Test with specific issue number
    python -m src.tests.github.write 123
"""

import os
import sys
import asyncio
from datetime import datetime

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.tools.github_tools import create_github_tools

console = Console()


async def test_create_issue(client: Client):
    """Test create_issue tool."""
    console.print(Panel.fit("STEP 1: Creating a new test issue", style="bold blue"))

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issue_title = f"🧪 MCP Test Issue - {timestamp}"
        issue_body = f"""## MCP GitHub Integration Test

This issue was created at **{timestamp}** by the GitHub MCP test suite.

### Test Purpose
Testing the `create_issue` tool from the MCP GitHub integration.

### Test Checklist
- [x] Issue creation working
- [ ] Comment addition (will be tested next)
- [ ] Status update (will be tested last)

---
🤖 *This is an automated test issue. You can safely close it.*
"""

        console.print(f"[cyan]Creating issue:[/cyan] '{issue_title}'")

        create_result = await client.call_tool(
            name="create_issue",
            arguments={
                "title": issue_title,
                "body": issue_body,
                "labels": "test,automated"
            }
        )

        result_data = create_result.data
        issue = result_data.issue if hasattr(result_data, 'issue') else result_data
        issue_number = issue.number if hasattr(issue, 'number') else issue.get('number')
        issue_url = issue.html_url if hasattr(issue, 'html_url') else issue.get('html_url')

        console.print("[green]✅ Issue created successfully![/green]")
        console.print(f"   [bold]Issue #:[/bold] {issue_number}")
        console.print(f"   [bold]URL:[/bold] [link={issue_url}]{issue_url}[/link]")

        return issue_number

    except Exception as e:
        console.print(f"[red]❌ ERROR creating issue: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return None


async def test_add_comment(client: Client, issue_number: int):
    """Test add_issue_comment tool."""
    console.print(Panel.fit("STEP 2: Adding comments to the issue", style="bold blue"))

    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add first comment
        console.print(f"[cyan]Adding first comment to issue #{issue_number}...[/cyan]")

        comment_body = f"""### ✅ Test Comment 1

Added at {timestamp}

This comment tests the `add_issue_comment` tool. The tool is working correctly!

**Test details:**
- Comment added via MCP GitHub integration
- Timestamp: `{timestamp}`
- Test status: **PASSING** ✅
"""

        comment_result = await client.call_tool(
            name="add_issue_comment",
            arguments={
                "issue_number": issue_number,
                "comment": comment_body
            }
        )

        result_data = comment_result.data
        comment = result_data.comment if hasattr(result_data, 'comment') else result_data
        comment_url = comment.html_url if hasattr(comment, 'html_url') else comment.get('html_url', '')

        console.print("[green]✅ First comment added![/green]")
        console.print(f"   [link={comment_url}]{comment_url}[/link]")

        # Add second comment
        console.print("\n[cyan]Adding second comment...[/cyan]")

        comment_body_2 = """### 📊 Test Results Summary

**All write operations tested:**
1. ✅ `create_issue` - Issue creation successful
2. ✅ `add_issue_comment` - Comment addition successful
3. ⏳ `update_issue_status` - Will be tested next

**Next step:** Testing issue status update (close/reopen)
"""

        await client.call_tool(
            name="add_issue_comment",
            arguments={
                "issue_number": issue_number,
                "comment": comment_body_2
            }
        )

        console.print("[green]✅ Second comment added![/green]")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR adding comments: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_update_status(client: Client, issue_number: int):
    """Test update_issue_status tool."""
    console.print(Panel.fit("STEP 3: Testing issue status updates", style="bold blue"))

    try:
        # Close the issue
        console.print(f"[cyan]Closing issue #{issue_number}...[/cyan]")

        close_result = await client.call_tool(
            name="update_issue_status",
            arguments={
                "issue_number": issue_number,
                "new_state": "closed"
            }
        )

        result_data = close_result.data
        message = result_data.message if hasattr(result_data, 'message') else "Issue closed"

        console.print("[green]✅ Issue closed successfully![/green]")
        console.print(f"   {message}")

        # Wait a moment
        await asyncio.sleep(1)

        # Reopen the issue
        console.print(f"\n[cyan]Reopening issue #{issue_number}...[/cyan]")

        reopen_result = await client.call_tool(
            name="update_issue_status",
            arguments={
                "issue_number": issue_number,
                "new_state": "open"
            }
        )

        result_data = reopen_result.data
        message = result_data.message if hasattr(result_data, 'message') else "Issue reopened"

        console.print("[green]✅ Issue reopened successfully![/green]")
        console.print(f"   {message}")

        # Add final comment
        console.print("\n[cyan]Adding final test summary comment...[/cyan]")

        final_comment = """### 🎉 All Tests Complete!

**Final test results:**
1. ✅ `create_issue` - Successfully created test issue
2. ✅ `add_issue_comment` - Successfully added multiple comments
3. ✅ `update_issue_status` - Successfully closed and reopened issue

---
**Test Status:** ALL PASSING ✅

🤖 *Automated test complete. You can now close this issue.*
"""

        await client.call_tool(
            name="add_issue_comment",
            arguments={
                "issue_number": issue_number,
                "comment": final_comment
            }
        )

        console.print("[green]✅ Final comment added![/green]")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR updating status: {str(e)}[/red]")
        import traceback
        traceback.print_exc()
        return False


async def test_write_operations(issue_number: int = None):
    """Test all write operations."""

    # Initialize client
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")
    repo_name = os.getenv("REPO_NAME")

    if not token:
        console.print("[red]❌ ERROR: GITHUB_TOKEN environment variable not set[/red]")
        return False
    if not username:
        console.print("[red]❌ ERROR: GITHUB_USERNAME environment variable not set[/red]")
        return False
    if not repo_name:
        console.print("[red]❌ ERROR: REPO_NAME environment variable not set[/red]")
        return False

    console.print("[cyan]🔧 Initializing GitHub client...[/cyan]")
    github_client = GitHubAPIClient(token=token, repo_owner=username, repo_name=repo_name)
    mcp = create_github_tools(github_client)

    # Health check
    if not github_client.health_check():
        console.print("[red]❌ ERROR: Cannot connect to GitHub API[/red]")
        return False

    console.print("[green]✅ Connected to GitHub API[/green]")
    console.print(f"   [bold]Repository:[/bold] {username}/{repo_name}\n")

    success = True

    async with Client(mcp) as client:
        if issue_number:
            # Test with existing issue
            console.print(f"[yellow]🎯 Testing with existing issue #{issue_number}[/yellow]\n")

            # Test comments
            if not await test_add_comment(client, issue_number):
                success = False

            # Test status update
            if not await test_update_status(client, issue_number):
                success = False
        else:
            # Create new issue and test everything
            issue_number = await test_create_issue(client)

            if not issue_number:
                success = False
            else:
                # Test comments
                if not await test_add_comment(client, issue_number):
                    success = False

                # Test status update
                if not await test_update_status(client, issue_number):
                    success = False

    # Summary
    if success and issue_number:
        console.print()

        # Create summary table
        table = Table(title="✅ Test Summary", style="green")
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        table.add_row("create_issue", "✅ Created test issue")
        table.add_row("add_issue_comment", "✅ Added multiple comments")
        table.add_row("update_issue_status", "✅ Closed and reopened issue")

        console.print(table)

        console.print(f"\n[bold]Test issue:[/bold] #{issue_number}")
        console.print(f"[bold]Repository:[/bold] https://github.com/{username}/{repo_name}")
        console.print(f"[bold]Issue URL:[/bold] [link=https://github.com/{username}/{repo_name}/issues/{issue_number}]https://github.com/{username}/{repo_name}/issues/{issue_number}[/link]")
        console.print("\n[cyan]💡 You can now run read.py to verify the created content:[/cyan]")
        console.print(f"   python -m src.tests.github.read {issue_number}")

    return success


def main():
    """Main entry point."""
    console.rule("[bold blue]🚀 GITHUB WRITE OPERATIONS TEST SUITE 🚀[/bold blue]")
    console.print()

    # Get issue number from command line (optional)
    issue_number = None
    if len(sys.argv) > 1:
        try:
            issue_number = int(sys.argv[1])
            console.print(f"[yellow]📝 Testing with existing issue #{issue_number}[/yellow]\n")
        except ValueError:
            console.print(f"[red]⚠️  Invalid issue number: {sys.argv[1]}[/red]")
            console.print("   Usage: python -m src.tests.github.write [issue_number]")
            return

    # Run async tests
    success = asyncio.run(test_write_operations(issue_number))

    console.print()
    if success:
        console.print(Panel.fit("[bold green]✅ ALL TESTS PASSED![/bold green]", style="green"))
    else:
        console.print(Panel.fit("[bold red]❌ TESTS FAILED[/bold red]", style="red"))
    console.print()


if __name__ == "__main__":
    main()
