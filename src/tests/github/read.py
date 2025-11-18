"""
Test suite for GitHub read operations.

Tests list_issues, get_issue, get_issue_comments, get_repository_info,
list_labels, and list_commits tools.

IMPORTANT: Make sure you have:
1. GITHUB_TOKEN environment variable set
2. GITHUB_USERNAME environment variable set
3. REPO_NAME environment variable set
4. Some issues in your repository

Setup:
    export GITHUB_TOKEN="your_github_token"
    export GITHUB_USERNAME="your_username"
    export REPO_NAME="your_repo"

Usage:
    # Run all read tests
    python -m src.tests.github.read

    # Test with specific issue number
    python -m src.tests.github.read 123
"""

import os
import sys
import asyncio
from typing import Optional

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.tools.github_tools import create_github_tools

console = Console()


async def test_get_repository_info(client: Client):
    """Test get_repository_info tool."""
    console.print()
    console.print(Panel.fit("TEST: get_repository_info", style="bold cyan"))

    try:
        result = await client.call_tool(name="get_repository_info", arguments={})
        result_data = result.data

        # Access repository info
        repo_info = (
            result_data.repository
            if hasattr(result_data, "repository")
            else result_data
        )

        name = (
            repo_info.name if hasattr(repo_info, "name") else repo_info.get("name", "")
        )
        owner = (
            repo_info.owner
            if hasattr(repo_info, "owner")
            else repo_info.get("owner", "")
        )
        full_name = (
            repo_info.full_name
            if hasattr(repo_info, "full_name")
            else repo_info.get("full_name", "")
        )
        url = (
            repo_info.html_url
            if hasattr(repo_info, "html_url")
            else repo_info.get("html_url", "")
        )
        description = (
            repo_info.description
            if hasattr(repo_info, "description")
            else repo_info.get("description", "")
        )
        default_branch = (
            repo_info.default_branch
            if hasattr(repo_info, "default_branch")
            else repo_info.get("default_branch", "")
        )
        open_issues = (
            repo_info.open_issues_count
            if hasattr(repo_info, "open_issues_count")
            else repo_info.get("open_issues_count", 0)
        )

        console.print("[green]✅ Repository information:[/green]")
        console.print(f"   [bold]Name:[/bold] {name}")
        console.print(f"   [bold]Owner:[/bold] {owner}")
        console.print(f"   [bold]Full name:[/bold] {full_name}")
        console.print(f"   [bold]URL:[/bold] [link={url}]{url}[/link]")
        console.print(f"   [bold]Description:[/bold] {description or 'N/A'}")
        console.print(f"   [bold]Default branch:[/bold] {default_branch}")
        console.print(f"   [bold]Open issues:[/bold] {open_issues}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_repository_info: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_list_labels(client: Client):
    """Test list_labels tool."""
    console.print()
    console.print(Panel.fit("TEST: list_labels", style="bold cyan"))

    try:
        result = await client.call_tool(name="list_labels", arguments={})
        result_data = result.data

        count = result_data.count if hasattr(result_data, "count") else 0
        labels = result_data.labels if hasattr(result_data, "labels") else []

        console.print(f"[green]✅ Found {count} label(s):[/green]\n")

        for i, label in enumerate(labels[:10], 1):  # Show first 10
            name = label.name if hasattr(label, "name") else label.get("name", "")
            color = label.color if hasattr(label, "color") else label.get("color", "")
            description = (
                label.description
                if hasattr(label, "description")
                else label.get("description", "")
            )

            console.print(f"   [bold]{i}. {name}[/bold]")
            console.print(f"      Color: [#{color}]#{color}[/#{color}]")
            if description:
                console.print(f"      Description: {description}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_labels: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_list_issues(client: Client):
    """Test list_issues tool."""
    console.print()
    console.print(Panel.fit("TEST: list_issues", style="bold cyan"))

    try:
        # Test 1: List all open issues
        console.print("\n[cyan]1. Listing all open issues...[/cyan]")
        result = await client.call_tool(name="list_issues", arguments={"state": "open"})
        result_data = result.data

        count = result_data.count if hasattr(result_data, "count") else 0
        issues = result_data.issues if hasattr(result_data, "issues") else []

        console.print(f"[green]✅ Found {count} open issue(s):[/green]")

        for i, issue in enumerate(issues[:5], 1):  # Show first 5
            number = (
                issue.number if hasattr(issue, "number") else issue.get("number", 0)
            )
            title = issue.title if hasattr(issue, "title") else issue.get("title", "")
            assignee = (
                issue.assignee if hasattr(issue, "assignee") else issue.get("assignee")
            )
            labels = (
                issue.labels if hasattr(issue, "labels") else issue.get("labels", [])
            )

            console.print(f"   [bold]{i}. #{number}:[/bold] {title}")
            console.print(f"      Assignee: {assignee or 'None'}")
            console.print(f"      Labels: {', '.join(labels) if labels else 'None'}")

        # Test 2: Filter by label
        console.print("\n[cyan]2. Filtering by 'test' label...[/cyan]")
        result2 = await client.call_tool(
            name="list_issues", arguments={"labels": "test", "state": "all"}
        )
        result_data2 = result2.data

        count2 = result_data2.count if hasattr(result_data2, "count") else 0
        console.print(f"[green]✅ Found {count2} issue(s) with 'test' label[/green]")

        # Return first issue number if available
        if issues:
            return (
                issues[0].number
                if hasattr(issues[0], "number")
                else issues[0].get("number")
            )
        return None

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_issues: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


async def test_get_issue(client: Client, issue_number: int):
    """Test get_issue tool."""
    console.print()
    console.print(Panel.fit("TEST: get_issue", style="bold cyan"))

    try:
        result = await client.call_tool(
            name="get_issue", arguments={"issue_number": issue_number}
        )
        result_data = result.data

        issue = result_data.issue if hasattr(result_data, "issue") else result_data

        if not issue:
            console.print(f"[yellow]⚠️  Issue #{issue_number} not found[/yellow]")
            return False

        number = issue.number if hasattr(issue, "number") else issue.get("number", 0)
        title = issue.title if hasattr(issue, "title") else issue.get("title", "")
        body = issue.body if hasattr(issue, "body") else issue.get("body", "")
        state = issue.state if hasattr(issue, "state") else issue.get("state", "")
        assignee = (
            issue.assignee if hasattr(issue, "assignee") else issue.get("assignee")
        )
        labels = issue.labels if hasattr(issue, "labels") else issue.get("labels", [])
        comments_count = (
            issue.comments_count
            if hasattr(issue, "comments_count")
            else issue.get("comments_count", 0)
        )
        created_at = (
            issue.created_at
            if hasattr(issue, "created_at")
            else issue.get("created_at", "")
        )
        html_url = (
            issue.html_url if hasattr(issue, "html_url") else issue.get("html_url", "")
        )

        console.print(f"[green]✅ Retrieved issue #{number}:[/green]")
        console.print(f"   [bold]Title:[/bold] {title}")
        console.print(f"   [bold]State:[/bold] {state}")
        console.print(f"   [bold]Assignee:[/bold] {assignee or 'None'}")
        console.print(
            f"   [bold]Labels:[/bold] {', '.join(labels) if labels else 'None'}"
        )
        console.print(f"   [bold]Comments:[/bold] {comments_count}")
        console.print(f"   [bold]Created:[/bold] {created_at}")
        console.print(f"   [bold]URL:[/bold] [link={html_url}]{html_url}[/link]")
        console.print("\n   [bold]Body preview:[/bold]")
        body_preview = body[:200] + "..." if len(body) > 200 else body
        console.print(f"   {body_preview}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_issue: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_get_issue_comments(client: Client, issue_number: int):
    """Test get_issue_comments tool."""
    console.print()
    console.print(Panel.fit("TEST: get_issue_comments", style="bold cyan"))

    try:
        result = await client.call_tool(
            name="get_issue_comments", arguments={"issue_number": issue_number}
        )
        result_data = result.data

        count = result_data.count if hasattr(result_data, "count") else 0
        comments = result_data.comments if hasattr(result_data, "comments") else []

        console.print(f"[green]✅ Retrieved {count} comment(s):[/green]\n")

        for i, comment in enumerate(comments[:5], 1):  # Show first 5
            comment_id = comment.id if hasattr(comment, "id") else comment.get("id", 0)
            body = comment.body if hasattr(comment, "body") else comment.get("body", "")
            user = comment.user if hasattr(comment, "user") else comment.get("user", "")
            created_at = (
                comment.created_at
                if hasattr(comment, "created_at")
                else comment.get("created_at", "")
            )

            console.print(f"   [bold]{i}. Comment #{comment_id}[/bold]")
            console.print(f"      By: [cyan]@{user}[/cyan]")
            console.print(f"      Created: {created_at}")
            body_preview = body[:100] + "..." if len(body) > 100 else body
            console.print(f"      Body: {body_preview}")
            console.print()

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_issue_comments: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_list_commits(client: Client):
    """Test list_commits tool."""
    console.print()
    console.print(Panel.fit("TEST: list_commits", style="bold cyan"))

    try:
        # List recent commits
        console.print("\n[cyan]1. Listing recent commits (limit 5)...[/cyan]")
        result = await client.call_tool(name="list_commits", arguments={"limit": 5})
        result_data = result.data

        count = result_data.count if hasattr(result_data, "count") else 0
        commits = result_data.commits if hasattr(result_data, "commits") else []

        console.print(f"[green]✅ Found {count} commit(s):[/green]\n")

        for i, commit in enumerate(commits, 1):
            sha = commit.sha if hasattr(commit, "sha") else commit.get("sha", "")
            message = (
                commit.message
                if hasattr(commit, "message")
                else commit.get("message", "")
            )
            author = (
                commit.author if hasattr(commit, "author") else commit.get("author", "")
            )
            date = commit.date if hasattr(commit, "date") else commit.get("date", "")

            # Get first line of commit message
            message_first_line = message.split("\n")[0] if message else ""

            console.print(f"   [bold]{i}. {sha[:7]}:[/bold] {message_first_line[:60]}")
            console.print(f"      Author: [cyan]@{author}[/cyan]")
            console.print(f"      Date: {date}")

        return True

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_commits: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return False


async def test_all_read_operations(issue_number: Optional[int] = None):
    """Run all read operation tests."""

    # Initialize client
    token = os.getenv("GITHUB_TOKEN")
    username = os.getenv("GITHUB_USERNAME")
    repo_name = os.getenv("REPO_NAME")

    if not token:
        console.print("[red]❌ ERROR: GITHUB_TOKEN environment variable not set[/red]")
        return False
    if not username:
        console.print(
            "[red]❌ ERROR: GITHUB_USERNAME environment variable not set[/red]"
        )
        return False
    if not repo_name:
        console.print("[red]❌ ERROR: REPO_NAME environment variable not set[/red]")
        return False

    console.print("[cyan]🔧 Initializing GitHub client...[/cyan]")
    github_client = GitHubAPIClient(
        token=token, repo_owner=username, repo_name=repo_name
    )
    mcp = create_github_tools(github_client)

    # Health check
    if not github_client.health_check():
        console.print("[red]❌ ERROR: Cannot connect to GitHub API[/red]")
        return False

    console.print("[green]✅ Connected to GitHub API[/green]")
    console.print(f"   [bold]Repository:[/bold] {username}/{repo_name}\n")

    results = []

    async with Client(mcp) as client:
        # Test 1: Get repository info
        results.append(("get_repository_info", await test_get_repository_info(client)))

        # Test 2: List labels
        results.append(("list_labels", await test_list_labels(client)))

        # Test 3: List issues
        found_issue_number = await test_list_issues(client)
        results.append(("list_issues", found_issue_number is not None))

        # Use found issue if no specific one provided
        if not issue_number and found_issue_number:
            issue_number = found_issue_number

        # Test 4 & 5: Get issue and comments
        if issue_number:
            results.append(("get_issue", await test_get_issue(client, issue_number)))
            results.append(
                (
                    "get_issue_comments",
                    await test_get_issue_comments(client, issue_number),
                )
            )
        else:
            console.print(
                "\n[yellow]⚠️  WARNING: No issue number provided or found, skipping issue detail tests[/yellow]"
            )
            console.print("   Run: python -m src.tests.github.read <issue_number>")

        # Test 6: List commits
        results.append(("list_commits", await test_list_commits(client)))

    # Summary
    console.print()
    console.print(Panel.fit("TEST SUMMARY", style="bold magenta"))

    passed = sum(1 for _, result in results if result)
    total = len(results)

    # Create summary table
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Test", style="cyan", no_wrap=True)
    table.add_column("Status", justify="center")

    for test_name, result in results:
        status = "[green]✅ PASS[/green]" if result else "[red]❌ FAIL[/red]"
        table.add_row(test_name, status)

    console.print(table)
    console.print(f"\n   [bold]Total:[/bold] {passed}/{total} tests passed")

    return passed == total


def main():
    """Main entry point."""
    console.rule("[bold blue]🔍 GITHUB READ OPERATIONS TEST SUITE 🔍[/bold blue]")
    console.print()

    # Check for issue number argument
    issue_number = None
    if len(sys.argv) > 1:
        try:
            issue_number = int(sys.argv[1])
            console.print(
                f"[yellow]📝 Testing with specific issue #{issue_number}[/yellow]\n"
            )
        except ValueError:
            console.print(f"[red]⚠️  Invalid issue number: {sys.argv[1]}[/red]")
            console.print("   Usage: python -m src.tests.github.read [issue_number]")
            return

    # Run async tests
    success = asyncio.run(test_all_read_operations(issue_number))

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
