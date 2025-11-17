"""
GitHub API client for MCP server.

Provides GitHub API operations using PyGithub library.
Implements core functions needed for GitHub MCP tools.
"""

from typing import List, Optional, Literal
from github import Github, GithubException, Auth

from mcp_server.schemas.github_schemas import (
    Issue,
    Comment,
    PullRequest,
    Commit,
    Repository,
    Label,
    IssueFilters,
)


class GitHubAPIClient:
    """
    GitHub API client using PyGithub.

    Provides simplified interface for GitHub operations needed by MCP tools.
    """

    def __init__(self, token: str, repo_owner: str, repo_name: str):
        """
        Initialize GitHub API client.

        Args:
            token: GitHub personal access token
            repo_owner: Repository owner username
            repo_name: Repository name
        """
        self.token = token
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.full_repo_name = f"{repo_owner}/{repo_name}"

        # Initialize PyGithub client with new Auth pattern
        auth = Auth.Token(self.token)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(self.full_repo_name)

    def health_check(self) -> bool:
        """
        Check if GitHub API is accessible.

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            self.repo.get_labels()
            return True
        except Exception:
            return False

    def close(self):
        """Close GitHub API client."""
        self.gh.close()

    # ========================================================================
    # Issue Operations
    # ========================================================================

    def list_issues(self, filters: Optional[IssueFilters] = None) -> List[Issue]:
        """
        List issues with optional filters.

        Args:
            filters: Optional filters for issues

        Returns:
            List of issues matching filters
        """
        if filters is None:
            filters = IssueFilters()

        kwargs = {"state": filters.state}

        if filters.assignee:
            kwargs["assignee"] = filters.assignee
        if filters.labels:
            kwargs["labels"] = filters.labels
        if filters.sort:
            kwargs["sort"] = filters.sort
        if filters.direction:
            kwargs["direction"] = filters.direction

        issues = self.repo.get_issues(**kwargs)

        result = []
        for issue in issues:
            # Skip pull requests (they show up in issues)
            if issue.pull_request:
                continue
            result.append(self._convert_issue(issue))

        return result

    def get_issue(self, issue_number: int) -> Optional[Issue]:
        """
        Get a specific issue by number.

        Args:
            issue_number: Issue number

        Returns:
            Issue object or None if not found
        """
        try:
            issue = self.repo.get_issue(issue_number)
            # Skip if it's a pull request
            if issue.pull_request:
                return None
            return self._convert_issue(issue)
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def create_issue(
        self,
        title: str,
        body: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        labels: Optional[List[str]] = None,
    ) -> Issue:
        """
        Create a new issue.

        Args:
            title: Issue title (required)
            body: Issue description/body (optional)
            assignees: List of usernames to assign (optional)
            labels: List of label names to apply (optional)

        Returns:
            Created issue object
        """
        kwargs = {"title": title}

        if body:
            kwargs["body"] = body
        if assignees:
            kwargs["assignees"] = assignees
        if labels:
            kwargs["labels"] = labels

        issue = self.repo.create_issue(**kwargs)
        return self._convert_issue(issue)

    def update_issue_status(
        self, issue_number: int, new_state: Literal["open", "closed"]
    ) -> Optional[Issue]:
        """
        Update issue state.

        Args:
            issue_number: Issue number
            new_state: New state (open or closed)

        Returns:
            Updated issue or None if not found
        """
        try:
            issue = self.repo.get_issue(issue_number)
            issue.edit(state=new_state)
            return self._convert_issue(issue)
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def add_issue_comment(
        self, issue_number: int, comment_body: str
    ) -> Optional[Comment]:
        """
        Add a comment to an issue.

        Args:
            issue_number: Issue number
            comment_body: Comment text

        Returns:
            Created comment or None if issue not found
        """
        try:
            issue = self.repo.get_issue(issue_number)
            comment = issue.create_comment(comment_body)
            return self._convert_comment(comment)
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def get_issue_comments(self, issue_number: int) -> List[Comment]:
        """
        Get all comments for an issue.

        Args:
            issue_number: Issue number

        Returns:
            List of comments
        """
        try:
            issue = self.repo.get_issue(issue_number)
            comments = issue.get_comments()
            return [self._convert_comment(c) for c in comments]
        except GithubException as e:
            if e.status == 404:
                return []
            raise

    # ========================================================================
    # Repository Operations
    # ========================================================================

    def get_repository_info(self) -> Repository:
        """
        Get repository metadata.

        Returns:
            Repository information
        """
        return Repository(
            name=self.repo.name,
            owner=self.repo.owner.login,
            full_name=self.repo.full_name,
            html_url=self.repo.html_url,
            description=self.repo.description or "",
            default_branch=self.repo.default_branch,
            open_issues_count=self.repo.open_issues_count,
            forks_count=self.repo.forks_count,
            stargazers_count=self.repo.stargazers_count,
            private=self.repo.private,
        )

    def list_labels(self) -> List[Label]:
        """
        Get all repository labels.

        Returns:
            List of labels
        """
        labels = self.repo.get_labels()
        return [
            Label(
                name=label.name,
                color=label.color,
                description=label.description or "",
            )
            for label in labels
        ]

    # ========================================================================
    # Commit Operations
    # ========================================================================

    def list_commits(
        self, author: Optional[str] = None, since: Optional[str] = None, limit: int = 10
    ) -> List[Commit]:
        """
        List recent commits.

        Args:
            author: Filter by author username
            since: ISO datetime - only commits after this date
            limit: Maximum commits to return

        Returns:
            List of commits
        """
        from datetime import datetime

        kwargs = {}
        if since:
            kwargs["since"] = datetime.fromisoformat(since)
        if author:
            kwargs["author"] = author

        commits = self.repo.get_commits(**kwargs)

        result = []
        for commit in commits:
            if len(result) >= limit:
                break

            result.append(
                Commit(
                    sha=commit.sha,
                    message=commit.commit.message,
                    author=commit.author.login if commit.author else "unknown",
                    date=commit.commit.author.date,
                    html_url=commit.html_url,
                )
            )

        return result

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _convert_issue(self, issue) -> Issue:
        """Convert PyGithub Issue to Pydantic Issue model."""
        return Issue(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            labels=[label.name for label in issue.labels],
            assignee=issue.assignee.login if issue.assignee else None,
            assignees=[a.login for a in issue.assignees],
            created_at=issue.created_at,
            updated_at=issue.updated_at,
            closed_at=issue.closed_at,
            html_url=issue.html_url,
            comments_count=issue.comments,
        )

    def _convert_comment(self, comment) -> Comment:
        """Convert PyGithub Comment to Pydantic Comment model."""
        return Comment(
            id=comment.id,
            body=comment.body,
            user=comment.user.login,
            created_at=comment.created_at,
            updated_at=comment.updated_at,
            html_url=comment.html_url,
        )
