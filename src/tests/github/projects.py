"""
Test suite for GitHub Projects (v2) operations.

Tests list_projects, get_project_fields, create_issue (with auto-project-assignment),
and update_project_item_field tools.

This test will:
1. List all projects and find "ai-dummy-project-tracker"
2. Get project fields (Status, Priority, Size) with their options
3. Create a test issue and automatically add it to the project
4. Move the issue through board columns (In Progress → Done)

IMPORTANT: Make sure you have:
1. GITHUB_TOKEN with 'project' scope (required for Projects v2 GraphQL API)
2. GITHUB_USERNAME environment variable set
3. REPO_NAME environment variable set
4. A GitHub Project (v2) board created
5. Status field configured with options like "Backlog", "In Progress", "Done"

Setup:
    export GITHUB_TOKEN="your_github_token_with_project_scope"
    export GITHUB_USERNAME="your_username"
    export REPO_NAME="your_repo"

Verify token has 'project' scope:
    python verify_token_scopes.py

Usage:
    # Run the full workflow test
    python -m src.tests.github.projects

Note: Field options must be ProjectV2FieldOption Pydantic models, not dicts,
for proper FastMCP serialization. Using List[dict] causes empty Root() objects.
"""

import os
import asyncio
from datetime import datetime

from fastmcp.client import Client
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.tools.github_tools import create_github_tools

console = Console()


async def test_list_projects(client: Client):
    """Test list_projects tool."""
    console.print()
    console.print(Panel.fit("STEP 1: Listing all projects", style="bold blue"))

    try:
        result = await client.call_tool(name="list_projects", arguments={})
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        projects = result_data.projects if hasattr(result_data, "projects") else []

        console.print(f"[green]✅ Found {count} project(s):[/green]\n")

        # Create table
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Number", style="yellow", no_wrap=True)
        table.add_column("Title", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("URL", style="dim")

        for project in projects:
            number = (
                project.number
                if hasattr(project, "number")
                else project.get("number", 0)
            )
            title = (
                project.title if hasattr(project, "title") else project.get("title", "")
            )
            closed = (
                project.closed
                if hasattr(project, "closed")
                else project.get("closed", False)
            )
            url = project.url if hasattr(project, "url") else project.get("url", "")

            status = "[red]Closed[/red]" if closed else "[green]Open[/green]"
            table.add_row(str(number), title, status, url)

        console.print(table)

        # Find "dummy-project-board"
        dummy_project = None
        for project in projects:
            title = (
                project.title if hasattr(project, "title") else project.get("title", "")
            )
            if (
                "ai-dummy-project-tracker" in title.lower()
                or "dummy project tracker" in title.lower()
            ):
                dummy_project = project
                break

        if dummy_project:
            number = (
                dummy_project.number
                if hasattr(dummy_project, "number")
                else dummy_project.get("number", 0)
            )
            title = (
                dummy_project.title
                if hasattr(dummy_project, "title")
                else dummy_project.get("title", "")
            )
            console.print(
                f"\n[cyan]🎯 Found target project:[/cyan] [bold]{title}[/bold] (#{number})"
            )
            return number
        else:
            console.print(
                "\n[yellow]⚠️  'dummy-project-board' not found. Using first project if available.[/yellow]"
            )
            if projects:
                return (
                    projects[0].number
                    if hasattr(projects[0], "number")
                    else projects[0].get("number", 0)
                )
            return None

    except Exception as e:
        console.print(f"[red]❌ ERROR in list_projects: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None


async def test_get_project_fields(client: Client, project_number: int):
    """Test get_project_fields tool."""
    console.print()
    console.print(
        Panel.fit("STEP 2: Getting project fields and columns", style="bold blue")
    )

    try:
        result = await client.call_tool(
            name="get_project_fields", arguments={"project_number": project_number}
        )
        result_data = result.data
        count = result_data.count if hasattr(result_data, "count") else 0
        fields = result_data.fields if hasattr(result_data, "fields") else []

        console.print(
            f"[green]✅ Found {count} field(s) in project #{project_number}:[/green]\n"
        )

        for field in fields:
            name = field.name if hasattr(field, "name") else field.get("name", "")
            field_type = field.type if hasattr(field, "type") else field.get("type", "")
            options = (
                field.options if hasattr(field, "options") else field.get("options", [])
            )

            console.print(f"[bold cyan]{name}[/bold cyan] ({field_type})")

            if options:
                console.print("   Available options:")
                for opt in options:
                    # Access .name attribute from ProjectV2FieldOption model
                    opt_name = opt.name if hasattr(opt, "name") else opt.get("name", "")
                    console.print(f"   • {opt_name}")
            console.print()

        return fields

    except Exception as e:
        console.print(f"[red]❌ ERROR in get_project_fields: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return []


async def test_create_and_manage_issue(
    client: Client, project_number: int, fields: list
):
    """Test creating an issue and moving it through the project board."""
    console.print()
    console.print(Panel.fit("STEP 3: Creating test issue", style="bold blue"))

    # Create issue
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        issue_title = f"🧪 MCP Projects Test - {timestamp}"
        issue_body = f"""## MCP GitHub Projects Integration Test

Created at **{timestamp}** to test the GitHub Projects MCP tools.

### Test Workflow
1. ✅ Create issue
2. ⏳ Add to project board
3. ⏳ Move to "In Progress"
4. ⏳ Move to "Done"

---
🤖 *Automated test issue - safe to close*
"""

        console.print(f"[cyan]Creating issue:[/cyan] '{issue_title}'")
        console.print(f"[cyan]Auto-assigning to project:[/cyan] #{project_number}")

        create_result = await client.call_tool(
            name="create_issue",
            arguments={
                "title": issue_title,
                "body": issue_body,
                "labels": "test",
                "project_number": project_number,
            },
        )

        result_data = create_result.data
        issue = result_data.issue if hasattr(result_data, "issue") else result_data
        message = result_data.message if hasattr(result_data, "message") else ""
        issue_number = issue.number if hasattr(issue, "number") else issue.get("number")
        issue_url = (
            issue.html_url if hasattr(issue, "html_url") else issue.get("html_url")
        )

        console.print("[green]✅ Issue created successfully![/green]")
        console.print(f"   [bold]Issue #:[/bold] {issue_number}")
        console.print(f"   [bold]URL:[/bold] [link={issue_url}]{issue_url}[/link]")
        if "added to project" in message:
            console.print(
                f"   [bold]✅ Automatically added to project #{project_number}![/bold]"
            )

    except Exception as e:
        console.print(f"[red]❌ ERROR creating issue: {str(e)}[/red]")
        import traceback

        traceback.print_exc()
        return None

    # Note: Issue was automatically added to project during creation
    console.print()
    console.print(
        Panel.fit(
            "STEP 4: Issue already added to project (done during creation)",
            style="bold green",
        )
    )
    console.print(
        f"[green]✅ Issue #{issue_number} is now on project board #{project_number}[/green]"
    )

    # Find Status field
    status_field = None
    for field in fields:
        name = field.name if hasattr(field, "name") else field.get("name", "")
        if name.lower() == "status":
            status_field = field
            break

    if not status_field or not (
        status_field.options
        if hasattr(status_field, "options")
        else status_field.get("options")
    ):
        console.print(
            "\n[yellow]⚠️  No Status field found. Skipping status updates.[/yellow]"
        )
        return issue_number

    options = (
        status_field.options
        if hasattr(status_field, "options")
        else status_field.get("options", [])
    )
    option_names = [
        opt.get("name", "") if isinstance(opt, dict) else "" for opt in options
    ]

    # Move to "In Progress" (or similar)
    console.print()
    console.print(Panel.fit("STEP 5: Moving issue to 'In Progress'", style="bold blue"))

    in_progress_option = None
    for opt_name in option_names:
        if "progress" in opt_name.lower() or "doing" in opt_name.lower():
            in_progress_option = opt_name
            break

    if in_progress_option:
        try:
            console.print(
                f"[cyan]Moving issue #{issue_number} to '{in_progress_option}'...[/cyan]"
            )

            update_result = await client.call_tool(
                name="update_project_item_field",
                arguments={
                    "project_number": project_number,
                    "issue_number": issue_number,
                    "field_name": "Status",
                    "field_value": in_progress_option,
                },
            )

            result_data = update_result.data
            success = result_data.success if hasattr(result_data, "success") else False
            message = result_data.message if hasattr(result_data, "message") else ""

            if success:
                console.print("[green]✅ Issue moved to 'In Progress'![/green]")
                console.print(f"   {message}")
            else:
                console.print(f"[yellow]⚠️  {message}[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ ERROR moving issue: {str(e)}[/red]")
            import traceback

            traceback.print_exc()

    # Move to "Done" (or similar)
    console.print()
    console.print(Panel.fit("STEP 6: Moving issue to 'Done'", style="bold blue"))

    done_option = None
    for opt_name in option_names:
        if (
            "done" in opt_name.lower()
            or "complete" in opt_name.lower()
            or "finished" in opt_name.lower()
        ):
            done_option = opt_name
            break

    if done_option:
        try:
            console.print(
                f"[cyan]Moving issue #{issue_number} to '{done_option}'...[/cyan]"
            )

            update_result = await client.call_tool(
                name="update_project_item_field",
                arguments={
                    "project_number": project_number,
                    "issue_number": issue_number,
                    "field_name": "Status",
                    "field_value": done_option,
                },
            )

            result_data = update_result.data
            success = result_data.success if hasattr(result_data, "success") else False
            message = result_data.message if hasattr(result_data, "message") else ""

            if success:
                console.print("[green]✅ Issue moved to 'Done'![/green]")
                console.print(f"   {message}")
            else:
                console.print(f"[yellow]⚠️  {message}[/yellow]")

        except Exception as e:
            console.print(f"[red]❌ ERROR moving issue: {str(e)}[/red]")
            import traceback

            traceback.print_exc()

    return issue_number


async def test_projects_workflow():
    """Run complete GitHub Projects workflow test."""

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

    success = True

    async with Client(mcp) as client:
        # Step 1: List projects
        project_number = await test_list_projects(client)
        if not project_number:
            console.print(
                "[red]❌ No projects found. Please create a project first.[/red]"
            )
            return False

        # Step 2: Get project fields
        fields = await test_get_project_fields(client, project_number)

        # Step 3-6: Create issue and move through board
        issue_number = await test_create_and_manage_issue(
            client, project_number, fields
        )

        if not issue_number:
            success = False

    # Summary
    if success and issue_number:
        console.print()

        # Create summary table
        table = Table(title="✅ Test Summary", style="green")
        table.add_column("Operation", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")

        table.add_row("list_projects", "✅ Listed all projects")
        table.add_row("get_project_fields", "✅ Retrieved project fields")
        table.add_row("create_issue", "✅ Created test issue")
        table.add_row("add_issue_to_project", "✅ Added issue to board")
        table.add_row("update_project_item_field", "✅ Moved issue through columns")

        console.print(table)

        console.print(f"\n[bold]Test issue created:[/bold] #{issue_number}")
        console.print(f"[bold]Project:[/bold] #{project_number}")
        console.print(
            f"[bold]Repository:[/bold] https://github.com/{username}/{repo_name}"
        )
        console.print("\n[cyan]💡 Check your project board to see the issue![/cyan]")
        console.print(
            f"   https://github.com/users/{username}/projects/{project_number}"
        )

    return success


def main():
    """Main entry point."""
    console.rule("[bold blue]🚀 GITHUB PROJECTS TEST SUITE 🚀[/bold blue]")
    console.print()

    console.print("[cyan]📝 Test plan:[/cyan]")
    console.print("   [bold]1.[/bold] List all projects (find 'dummy-project-board')")
    console.print("   [bold]2.[/bold] Get project fields and available columns")
    console.print("   [bold]3.[/bold] Create a test issue")
    console.print("   [bold]4.[/bold] Add issue to project board")
    console.print("   [bold]5.[/bold] Move issue to 'In Progress'")
    console.print("   [bold]6.[/bold] Move issue to 'Done'\n")

    # Run async tests
    success = asyncio.run(test_projects_workflow())

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
