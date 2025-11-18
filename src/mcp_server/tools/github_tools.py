"""
Tools for GitHub - Issue management, repository operations, and commit tracking

IMPORTANT: Type Annotation Guidelines
--------------------------------------
When defining tool parameters with Field():
- If Field has `default=None`, the parameter type MUST be `Optional[Type]`
- If Field has a non-None default, the parameter type can be just `Type`
- Example CORRECT:
    assignee: Optional[str] = Field(default=None, ...)
- Example WRONG:
    assignee: str = Field(default=None, ...)  # Type error! str can't be None

This applies to all optional parameters including filters, search fields, etc.
Pydantic will raise ValidationError if type annotations don't match Field defaults.
"""

from typing import Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import Field

from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.schemas.github_schemas import (
    IssueFilters,
    ListIssuesInput,
    ListIssuesOutput,
    GetIssueInput,
    GetIssueOutput,
    CreateIssueInput,
    CreateIssueOutput,
    UpdateIssueStatusInput,
    UpdateIssueStatusOutput,
    AddIssueCommentInput,
    AddIssueCommentOutput,
    GetIssueCommentsInput,
    GetIssueCommentsOutput,
    GetRepositoryInfoOutput,
    ListLabelsOutput,
    ListCommitsInput,
    ListCommitsOutput,
    ListProjectsOutput,
    GetProjectFieldsInput,
    GetProjectFieldsOutput,
    AddIssueToProjectInput,
    AddIssueToProjectOutput,
    UpdateProjectItemInput,
    UpdateProjectItemOutput,
)


def create_github_tools(github_client: GitHubAPIClient) -> FastMCP:
    """
    Create FastMCP instance with GitHub tools.

    Args:
        github_client: Initialized GitHub API client

    Returns:
        FastMCP instance with registered GitHub tools
    """
    mcp = FastMCP("github")

    # ========================================================================
    # Issue Management Tools
    # ========================================================================

    @mcp.tool(tags={"github", "issues", "search"})
    def list_issues(
        assignee: Optional[str] = Field(
            default=None, description="Filter by assignee username (e.g., 'octocat')"
        ),
        labels: Optional[str] = Field(
            default=None,
            description="Comma-separated label names to filter by (e.g., 'bug,enhancement')",
        ),
        state: str = Field(
            default="open",
            description="Filter by state: 'open', 'closed', or 'all' (default: 'open')",
        ),
        sort: str = Field(
            default="created",
            description="Sort by: 'created', 'updated', or 'comments' (default: 'created')",
        ),
        direction: str = Field(
            default="desc",
            description="Sort direction: 'asc' or 'desc' (default: 'desc')",
        ),
    ) -> ListIssuesOutput:
        """
        List GitHub issues with comprehensive filtering and sorting options.

        Retrieves issues from the repository with support for filtering by assignee,
        labels, and state. Results can be sorted by creation date, update date, or
        comment count in ascending or descending order.

        Args:
            assignee: Filter by assignee username (e.g., 'octocat')
            labels: Comma-separated label names to filter by (e.g., 'bug,enhancement')
            state: Filter by state: 'open', 'closed', or 'all' (default: 'open')
            sort: Sort by: 'created', 'updated', or 'comments' (default: 'created')
            direction: Sort direction: 'asc' or 'desc' (default: 'desc')

        Returns:
            Response containing:
            - count: Number of issues found
            - issues: List of issue objects with number, title, state, labels, assignees,
                     timestamps, and URL
        """
        try:
            params = ListIssuesInput(
                assignee=assignee,
                labels=labels,
                state=state,
                sort=sort,
                direction=direction,
            )

            label_list = (
                [label.strip() for label in params.labels.split(",")]
                if params.labels
                else None
            )

            filters = IssueFilters(
                assignee=params.assignee,
                labels=label_list,
                state=params.state,
                sort=params.sort,
                direction=params.direction,
            )

            issues = github_client.list_issues(filters)

            return ListIssuesOutput(
                count=len(issues),
                issues=issues,
            )

        except Exception as e:
            raise ToolError(f"Failed to list issues: {str(e)}")

    @mcp.tool(tags={"github", "issues", "read"})
    def get_issue(
        issue_number: int = Field(..., description="Issue number to retrieve", gt=0),
    ) -> GetIssueOutput:
        """
        Get detailed information about a specific GitHub issue.

        Retrieves comprehensive details for a single issue including title, description,
        state, labels, assignees, comments count, and all timestamps. Returns null if
        the issue is not found.

        Args:
            issue_number: Issue number to retrieve (must be greater than 0)

        Returns:
            Response containing:
            - issue: Issue object with full details or null if not found
        """
        try:
            params = GetIssueInput(issue_number=issue_number)
            issue = github_client.get_issue(params.issue_number)

            return GetIssueOutput(issue=issue)

        except Exception as e:
            raise ToolError(f"Failed to get issue #{issue_number}: {str(e)}")

    @mcp.tool(tags={"github", "issues", "write"})
    def create_issue(
        title: str = Field(..., description="Issue title (required)", min_length=1),
        body: Optional[str] = Field(
            default=None, description="Issue description/body (supports Markdown)"
        ),
        assignees: Optional[str] = Field(
            default=None,
            description="Comma-separated usernames to assign (e.g., 'user1,user2')",
        ),
        labels: Optional[str] = Field(
            default=None,
            description="Comma-separated label names to apply (e.g., 'bug,priority:high')",
        ),
        project_number: Optional[int] = Field(
            default=None,
            description="Project number to automatically add issue to (optional)",
            gt=0,
        ),
    ) -> CreateIssueOutput:
        """
        Create a new GitHub issue and optionally add it to a project.

        Creates a new issue in the repository with the specified title and optional
        description, assignees, labels, and project assignment. The title is required
        and must not be empty. Body supports full Markdown formatting including code
        blocks and links.

        IMPORTANT:
        - Assignees must have write access to the repository
        - Labels must already exist in the repository (use list_labels to see available labels)
        - If project_number is provided, the issue will be automatically added to that project

        Args:
            title: Issue title (required, must not be empty)
            body: Issue description/body (supports Markdown formatting)
            assignees: Comma-separated usernames to assign (e.g., 'user1,user2')
                      Note: Users must have write access to the repository
            labels: Comma-separated label names to apply (e.g., 'bug,priority:high')
                   Note: Labels must already exist in the repository
            project_number: Project number to add issue to (optional)

        Returns:
            Response containing:
            - success: Boolean indicating if issue was created successfully
            - issue: Created issue object with number, title, state, and URL
            - message: Status message with issue number, URL, and project info if applicable
        """
        try:
            params = CreateIssueInput(
                title=title,
                body=body,
                assignees=(
                    [a.strip() for a in assignees.split(",")] if assignees else None
                ),
                labels=(
                    [label.strip() for label in labels.split(",")] if labels else None
                ),
                project_number=project_number,
            )

            issue = github_client.create_issue(
                title=params.title,
                body=params.body,
                assignees=params.assignees,
                labels=params.labels,
            )

            message = f"Successfully created issue #{issue.number}: {issue.html_url}"

            # If project_number is provided, add issue to project
            if project_number:
                try:
                    github_client.add_issue_to_project(
                        project_number=project_number, issue_number=issue.number
                    )
                    message += f" and added to project #{project_number}"
                except Exception as project_error:
                    # Don't fail the entire operation if project add fails
                    message += f" (Warning: Failed to add to project #{project_number}: {str(project_error)})"

            return CreateIssueOutput(
                success=True,
                issue=issue,
                message=message,
            )

        except Exception as e:
            error_msg = str(e)

            # Provide helpful error messages for common issues
            if "422" in error_msg and "assignees" in error_msg.lower():
                raise ToolError(
                    f"Failed to create issue: Invalid assignees. "
                    f"Assignees must have write access to the repository. "
                    f"GitHub error: {error_msg}"
                )
            elif "422" in error_msg and "label" in error_msg.lower():
                raise ToolError(
                    f"Failed to create issue: Invalid labels. "
                    f"Labels must exist in the repository. "
                    f"Use list_labels tool to see available labels. "
                    f"GitHub error: {error_msg}"
                )
            else:
                raise ToolError(f"Failed to create issue: {error_msg}")

    @mcp.tool(tags={"github", "issues", "write"})
    def update_issue_status(
        issue_number: int = Field(..., description="Issue number to update", gt=0),
        new_state: str = Field(..., description="New state: 'open' or 'closed'"),
    ) -> UpdateIssueStatusOutput:
        """
        Update the state of a GitHub issue (open or close it).

        Changes the state of an existing issue. Use this to close completed issues
        or reopen issues that need further work. Returns success status, updated
        issue details, and a confirmation message.

        Args:
            issue_number: Issue number to update (must be greater than 0)
            new_state: New state: 'open' or 'closed'

        Returns:
            Response containing:
            - success: Boolean indicating if update was successful
            - issue: Updated issue object or null if not found
            - message: Status message describing the result
        """
        try:
            params = UpdateIssueStatusInput(
                issue_number=issue_number, new_state=new_state
            )
            issue = github_client.update_issue_status(
                params.issue_number, params.new_state
            )

            if not issue:
                return UpdateIssueStatusOutput(
                    success=False,
                    issue=None,
                    message=f"Issue #{params.issue_number} not found",
                )

            return UpdateIssueStatusOutput(
                success=True,
                issue=issue,
                message=f"Successfully updated issue #{issue.number} to '{params.new_state}' state",
            )

        except Exception as e:
            raise ToolError(f"Failed to update issue #{issue_number} status: {str(e)}")

    @mcp.tool(tags={"github", "issues", "comments", "write"})
    def add_issue_comment(
        issue_number: int = Field(..., description="Issue number to comment on", gt=0),
        comment: str = Field(
            ..., description="Comment text to add (supports Markdown formatting)"
        ),
    ) -> AddIssueCommentOutput:
        """
        Add a comment to a GitHub issue.

        Posts a new comment to an existing issue. Comments support Markdown formatting
        including code blocks, links, and mentions. Returns success status, created
        comment details, and confirmation message.

        Args:
            issue_number: Issue number to comment on (must be greater than 0)
            comment: Comment text to add (supports Markdown formatting)

        Returns:
            Response containing:
            - success: Boolean indicating if comment was added successfully
            - comment: Created comment object with ID, body, user, timestamps, and URL
            - message: Status message describing the result
        """
        try:
            params = AddIssueCommentInput(issue_number=issue_number, comment=comment)
            comment_obj = github_client.add_issue_comment(
                params.issue_number, params.comment
            )

            if not comment_obj:
                return AddIssueCommentOutput(
                    success=False,
                    comment=None,
                    message=f"Issue #{params.issue_number} not found",
                )

            return AddIssueCommentOutput(
                success=True,
                comment=comment_obj,
                message=f"Successfully added comment to issue #{params.issue_number}",
            )

        except Exception as e:
            raise ToolError(f"Failed to add comment to issue #{issue_number}: {str(e)}")

    @mcp.tool(tags={"github", "issues", "comments", "read"})
    def get_issue_comments(
        issue_number: int = Field(
            ..., description="Issue number to get comments for", gt=0
        ),
    ) -> GetIssueCommentsOutput:
        """
        Get all comments for a GitHub issue.

        Retrieves the complete comment thread for an issue in chronological order.
        Each comment includes the author, body text, timestamps, and URL. Returns
        an empty list if there are no comments.

        Args:
            issue_number: Issue number to get comments for (must be greater than 0)

        Returns:
            Response containing:
            - count: Number of comments found
            - comments: List of comment objects with ID, body, user, timestamps, and URL
        """
        try:
            params = GetIssueCommentsInput(issue_number=issue_number)
            comments = github_client.get_issue_comments(params.issue_number)

            return GetIssueCommentsOutput(
                count=len(comments),
                comments=comments,
            )

        except Exception as e:
            raise ToolError(
                f"Failed to get comments for issue #{issue_number}: {str(e)}"
            )

    # ========================================================================
    # Repository Information Tools
    # ========================================================================

    @mcp.tool(tags={"github", "repository", "metadata"})
    def get_repository_info() -> GetRepositoryInfoOutput:
        """
        Get comprehensive information about the GitHub repository.

        Retrieves metadata including repository name, owner, description, default
        branch, issue counts, stars, forks, and privacy status. Useful for displaying
        repository overview or checking repository state.

        Returns:
            Response containing:
            - repository: Repository object with:
                - name: Repository name
                - owner: Repository owner username
                - full_name: Full repository name (owner/repo)
                - description: Repository description
                - default_branch: Default branch name (usually 'main' or 'master')
                - open_issues_count: Number of open issues
                - stargazers_count: Number of stars
                - forks_count: Number of forks
                - private: Boolean indicating if repository is private
                - html_url: Repository URL
        """
        try:
            repo = github_client.get_repository_info()

            return GetRepositoryInfoOutput(repository=repo)

        except Exception as e:
            raise ToolError(f"Failed to get repository information: {str(e)}")

    @mcp.tool(tags={"github", "repository", "labels"})
    def list_labels() -> ListLabelsOutput:
        """
        List all labels available in the GitHub repository.

        Retrieves all issue labels configured for the repository. Labels include
        name, color (hex code), and optional description. Useful for discovering
        available labels before creating or filtering issues.

        Returns:
            Response containing:
            - count: Number of labels available
            - labels: List of label objects with:
                - name: Label name
                - color: Hex color code (without #)
                - description: Optional label description
        """
        try:
            labels = github_client.list_labels()

            return ListLabelsOutput(
                count=len(labels),
                labels=labels,
            )

        except Exception as e:
            raise ToolError(f"Failed to list repository labels: {str(e)}")

    # ========================================================================
    # Commit History Tools
    # ========================================================================

    @mcp.tool(tags={"github", "commits", "history"})
    def list_commits(
        author: Optional[str] = Field(
            default=None, description="Filter by author username (e.g., 'octocat')"
        ),
        since: Optional[str] = Field(
            default=None,
            description="ISO datetime string - only commits after this date (e.g., '2024-01-01T00:00:00Z')",
        ),
        limit: int = Field(
            default=10,
            description="Maximum number of commits to return (1-100, default: 10)",
        ),
    ) -> ListCommitsOutput:
        """
        List recent commits in the GitHub repository with filtering options.

        Retrieves commit history with support for filtering by author and date range.
        Each commit includes SHA, message, author, timestamp, and URL. Results are
        returned in reverse chronological order (newest first).

        Args:
            author: Filter by author username (e.g., 'octocat')
            since: ISO datetime string - only commits after this date (e.g., '2024-01-01T00:00:00Z')
            limit: Maximum number of commits to return (1-100, default: 10)

        Returns:
            Response containing:
            - count: Number of commits returned
            - commits: List of commit objects with:
                - sha: Commit SHA hash
                - message: Commit message
                - author: Commit author username
                - date: Commit timestamp
                - html_url: Commit URL
        """
        try:
            params = ListCommitsInput(author=author, since=since, limit=limit)
            commits = github_client.list_commits(
                author=params.author,
                since=params.since,
                limit=params.limit,
            )

            return ListCommitsOutput(
                count=len(commits),
                commits=commits,
            )

        except Exception as e:
            raise ToolError(f"Failed to list commits: {str(e)}")

    # ========================================================================
    # GitHub Projects (v2) Tools
    # ========================================================================

    @mcp.tool(tags={"github", "projects", "read"})
    def list_projects() -> ListProjectsOutput:
        """
        List all GitHub Projects (v2) for the repository.

        Retrieves all projects associated with the repository including project number,
        title, URL, and status. Use this to discover available projects before adding
        issues to them.

        Returns:
            Response containing:
            - count: Number of projects found
            - projects: List of project objects with:
                - id: Project ID (used for GraphQL operations)
                - number: Project number (used for tool operations)
                - title: Project title
                - url: Project URL
                - closed: Boolean indicating if project is closed
        """
        try:
            projects = github_client.list_projects()

            return ListProjectsOutput(
                count=len(projects),
                projects=projects,
            )

        except Exception as e:
            raise ToolError(f"Failed to list projects: {str(e)}")

    @mcp.tool(tags={"github", "projects", "read"})
    def get_project_fields(
        project_number: int = Field(..., description="Project number", gt=0),
    ) -> GetProjectFieldsOutput:
        """
        Get all fields and their available options for a GitHub Project.

        Shows all fields (columns) in a project and their available values. This is essential
        for discovering what Status values, Priority levels, or other custom field options
        you can use when moving issues around on the project board.

        Use this before update_project_item_field to see:
        - Available field names (e.g., "Status", "Priority", "Assignee")
        - Field types (single_select, text, etc.)
        - Available options for each field (e.g., "Todo", "In Progress", "Done")

        Args:
            project_number: Project number (use list_projects to find)

        Returns:
            Response containing:
            - count: Number of fields in the project
            - fields: List of field objects with:
                - id: Field ID (internal use)
                - name: Field name (e.g., "Status", "Priority")
                - type: Field type (e.g., "single_select", "text")
                - options: List of available options with id and name
                          (e.g., [{"id": "...", "name": "Todo"}, {"id": "...", "name": "Done"}])

        Example output for Status field:
            {
                "name": "Status",
                "type": "single_select",
                "options": [
                    {"id": "abc123", "name": "Todo"},
                    {"id": "def456", "name": "In Progress"},
                    {"id": "ghi789", "name": "Done"}
                ]
            }
        """
        try:
            params = GetProjectFieldsInput(project_number=project_number)

            # Get project
            projects = github_client.list_projects()
            project = next(
                (p for p in projects if p.number == params.project_number), None
            )

            if not project:
                raise ToolError(
                    f"Project #{params.project_number} not found. Use list_projects to see available projects."
                )

            # Get fields
            fields = github_client.get_project_fields(project.id)

            return GetProjectFieldsOutput(
                count=len(fields),
                fields=fields,
            )

        except ToolError:
            raise
        except Exception as e:
            raise ToolError(f"Failed to get project fields: {str(e)}")

    @mcp.tool(tags={"github", "projects", "write"})
    def add_issue_to_project(
        project_number: int = Field(
            ..., description="Project number to add issue to", gt=0
        ),
        issue_number: int = Field(..., description="Issue number to add", gt=0),
    ) -> AddIssueToProjectOutput:
        """
        Add an issue to a GitHub Project (v2).

        Adds an existing issue to a project board. The issue will appear in the project
        with default field values. Use update_project_item_field to move it to specific
        columns or set custom field values.

        IMPORTANT:
        - Use list_projects to find available project numbers
        - The issue must exist in the repository
        - The bot must have write access to the project

        Args:
            project_number: Project number to add issue to (use list_projects to find)
            issue_number: Issue number to add to the project

        Returns:
            Response containing:
            - success: Boolean indicating if issue was added successfully
            - item_id: Project item ID (used for updating field values)
            - message: Status message describing the result
        """
        try:
            params = AddIssueToProjectInput(
                project_number=project_number, issue_number=issue_number
            )

            # Get all projects to find the one with matching number
            projects = github_client.list_projects()
            project = next(
                (p for p in projects if p.number == params.project_number), None
            )

            if not project:
                return AddIssueToProjectOutput(
                    success=False,
                    item_id=None,
                    message=f"Project #{params.project_number} not found. Use list_projects to see available projects.",
                )

            # Get issue GraphQL node ID
            issue_node_id = github_client.get_issue_node_id(params.issue_number)
            if not issue_node_id:
                return AddIssueToProjectOutput(
                    success=False,
                    item_id=None,
                    message=f"Issue #{params.issue_number} not found",
                )

            # Add issue to project
            item_id = github_client.add_issue_to_project(project.id, issue_node_id)

            if not item_id:
                return AddIssueToProjectOutput(
                    success=False,
                    item_id=None,
                    message=f"Failed to add issue #{params.issue_number} to project #{params.project_number}",
                )

            return AddIssueToProjectOutput(
                success=True,
                item_id=item_id,
                message=f"Successfully added issue #{params.issue_number} to project '{project.title}'",
            )

        except Exception as e:
            raise ToolError(f"Failed to add issue to project: {str(e)}")

    @mcp.tool(tags={"github", "projects", "write"})
    def update_project_item_field(
        project_number: int = Field(..., description="Project number", gt=0),
        issue_number: int = Field(..., description="Issue number", gt=0),
        field_name: str = Field(
            ..., description="Field name (e.g., 'Status', 'Priority')"
        ),
        field_value: str = Field(
            ...,
            description="New field value (e.g., 'In Progress', 'Done', 'Todo')",
        ),
    ) -> UpdateProjectItemOutput:
        """
        Update a field value for an issue in a GitHub Project (v2).

        Changes the value of a project field (like Status, Priority, etc.) for an issue
        that's already in the project. This is how you move issues between columns on
        the project board.

        Common use cases:
        - Move issue from "Todo" to "In Progress"
        - Move issue from "In Progress" to "Done"
        - Change priority levels
        - Update custom field values

        IMPORTANT:
        - The issue must already be in the project (use add_issue_to_project first)
        - Field names are case-sensitive (e.g., "Status" not "status")
        - Field values must match exactly what's defined in the project
        - The bot must have write access to the project

        Args:
            project_number: Project number (use list_projects to find)
            issue_number: Issue number already in the project
            field_name: Field name to update (e.g., "Status", "Priority")
                       This is case-sensitive and must match the project field name
            field_value: New value for the field (e.g., "In Progress", "Done", "Todo")
                        Must match an option defined in the project

        Returns:
            Response containing:
            - success: Boolean indicating if field was updated successfully
            - message: Status message describing the result

        Examples:
            # Move issue from Todo to In Progress
            update_project_item_field(
                project_number=1,
                issue_number=42,
                field_name="Status",
                field_value="In Progress"
            )

            # Move issue to Done
            update_project_item_field(
                project_number=1,
                issue_number=42,
                field_name="Status",
                field_value="Done"
            )
        """
        try:
            params = UpdateProjectItemInput(
                project_number=project_number,
                issue_number=issue_number,
                field_name=field_name,
                field_value=field_value,
            )

            # Get project
            projects = github_client.list_projects()
            project = next(
                (p for p in projects if p.number == params.project_number), None
            )

            if not project:
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Project #{params.project_number} not found. Use list_projects to see available projects.",
                )

            # Get project fields
            fields = github_client.get_project_fields(project.id)
            field = next((f for f in fields if f.name == params.field_name), None)

            if not field:
                available_fields = ", ".join([f.name for f in fields])
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Field '{params.field_name}' not found in project. Available fields: {available_fields}",
                )

            # Get option ID for the field value
            if not field.options:
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Field '{params.field_name}' is not a single-select field",
                )

            option = next(
                (opt for opt in field.options if opt["name"] == params.field_value),
                None,
            )

            if not option:
                available_options = ", ".join([opt["name"] for opt in field.options])
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Option '{params.field_value}' not found for field '{params.field_name}'. Available options: {available_options}",
                )

            # Get project item for this issue
            item_id = github_client.get_project_item_for_issue(
                project.id, params.issue_number
            )

            if not item_id:
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Issue #{params.issue_number} not found in project #{params.project_number}. Use add_issue_to_project first.",
                )

            # Update the field
            success = github_client.update_project_item_field(
                project.id, item_id, field.id, option["id"]
            )

            if not success:
                return UpdateProjectItemOutput(
                    success=False,
                    message=f"Failed to update field '{params.field_name}' to '{params.field_value}'",
                )

            return UpdateProjectItemOutput(
                success=True,
                message=f"Successfully updated issue #{params.issue_number}: {params.field_name} → '{params.field_value}'",
            )

        except Exception as e:
            raise ToolError(f"Failed to update project item field: {str(e)}")

    return mcp
