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

    return mcp
