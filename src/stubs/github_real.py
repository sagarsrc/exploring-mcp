"""
GitHub API Client for MCP tools - REAL API calls.

This module provides simplified GitHub API operations for testing MCP tools.
Makes actual API calls to GitHub using PyGithub.

Usage:
    from stubs.github_real import GitHubClient

    client = GitHubClient()  # Uses .env automatically
    issues = client.list_issues(assignee="sagarsrc")

    # Add comment to real GitHub issue
    client.add_issue_comment(21, "Testing comment via API")
"""

from typing import List, Optional, Literal, Dict
from dataclasses import dataclass
from datetime import datetime
import os
from github import Github, GithubException, Auth
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ============================================================================
# Data Models (simplified from GitHub API)
# ============================================================================


@dataclass
class User:
    """GitHub user"""

    login: str
    id: int


@dataclass
class Label:
    """GitHub label"""

    name: str
    color: str
    description: str = ""


@dataclass
class Issue:
    """GitHub issue"""

    number: int
    title: str
    body: str
    state: str
    labels: List[str]  # Just label names
    assignee: Optional[str]  # Just username
    created_at: str
    updated_at: str
    html_url: str
    comments_count: int = 0


@dataclass
class Comment:
    """GitHub issue comment"""

    id: int
    body: str
    user: str  # Just username
    created_at: str
    html_url: str


@dataclass
class Commit:
    """GitHub commit"""

    sha: str
    message: str
    author: str  # Just username
    date: str
    html_url: str


# ============================================================================
# GitHub Real API Client
# ============================================================================


class GitHubClient:
    """
    Real GitHub API client for MCP tools testing.

    Makes actual API calls to GitHub using PyGithub.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        repo_owner: Optional[str] = None,
        repo_name: Optional[str] = None,
    ):
        """
        Initialize GitHub client.

        Args:
            token: GitHub PAT (defaults to GITHUB_TOKEN env var)
            repo_owner: Repository owner (defaults to GITHUB_USERNAME env var)
            repo_name: Repository name (defaults to REPO_NAME env var)
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.repo_owner = repo_owner or os.getenv("GITHUB_USERNAME")
        self.repo_name = repo_name or os.getenv("REPO_NAME")

        if not self.token:
            raise ValueError("GitHub token not provided. Set GITHUB_TOKEN env var.")
        if not self.repo_owner:
            raise ValueError("Repo owner not provided. Set GITHUB_USERNAME env var.")
        if not self.repo_name:
            raise ValueError("Repo name not provided. Set REPO_NAME env var.")

        # Use new Auth.Token method (PyGithub 2.x)
        auth = Auth.Token(self.token)
        self.gh = Github(auth=auth)
        self.repo = self.gh.get_repo(f"{self.repo_owner}/{self.repo_name}")

    def _issue_to_dict(self, issue) -> Issue:
        """Convert PyGithub Issue to our Issue dataclass."""
        return Issue(
            number=issue.number,
            title=issue.title,
            body=issue.body or "",
            state=issue.state,
            labels=[label.name for label in issue.labels],
            assignee=issue.assignee.login if issue.assignee else None,
            created_at=issue.created_at.isoformat(),
            updated_at=issue.updated_at.isoformat(),
            html_url=issue.html_url,
            comments_count=issue.comments,
        )

    def _comment_to_dict(self, comment) -> Comment:
        """Convert PyGithub Comment to our Comment dataclass."""
        return Comment(
            id=comment.id,
            body=comment.body,
            user=comment.user.login,
            created_at=comment.created_at.isoformat(),
            html_url=comment.html_url,
        )

    # ========================================================================
    # Core API Methods
    # ========================================================================

    def list_issues(
        self,
        assignee: Optional[str] = None,
        labels: Optional[List[str]] = None,
        state: Literal["open", "closed", "all"] = "open",
    ) -> List[Issue]:
        """
        List issues with filters.

        Args:
            assignee: Filter by assignee username
            labels: Filter by label names
            state: Filter by state ("open", "closed", "all")

        Returns:
            List of issues matching filters
        """
        kwargs = {"state": state}

        if assignee:
            kwargs["assignee"] = assignee
        if labels:
            kwargs["labels"] = labels

        issues = self.repo.get_issues(**kwargs)

        # Filter out pull requests (they show up in issues)
        result = []
        for issue in issues:
            if not issue.pull_request:
                result.append(self._issue_to_dict(issue))

        return result

    def get_issue(self, issue_number: int) -> Optional[Issue]:
        """
        Get a specific issue.

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
            return self._issue_to_dict(issue)
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def update_issue_status(
        self, issue_number: int, new_state: Literal["open", "closed"]
    ) -> Optional[Issue]:
        """
        Update issue state.

        Args:
            issue_number: Issue number
            new_state: New state ("open" or "closed")

        Returns:
            Updated issue or None if not found
        """
        try:
            issue = self.repo.get_issue(issue_number)
            issue.edit(state=new_state)
            return self._issue_to_dict(issue)
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
            return self._comment_to_dict(comment)
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
            return [self._comment_to_dict(c) for c in comments]
        except GithubException as e:
            if e.status == 404:
                return []
            raise

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
                    date=commit.commit.author.date.isoformat(),
                    html_url=commit.html_url,
                )
            )

        return result

    def get_repository_info(self) -> Dict:
        """
        Get repository metadata.

        Returns:
            Repository information dict
        """
        return {
            "name": self.repo.name,
            "owner": self.repo.owner.login,
            "full_name": self.repo.full_name,
            "html_url": self.repo.html_url,
            "description": self.repo.description or "",
            "default_branch": self.repo.default_branch,
            "open_issues_count": self.repo.open_issues_count,
        }

    def list_labels(self) -> List[Label]:
        """
        Get all repository labels.

        Returns:
            List of labels
        """
        labels = self.repo.get_labels()
        return [
            Label(
                name=label.name, color=label.color, description=label.description or ""
            )
            for label in labels
        ]


# ============================================================================
# Example Usage
# ============================================================================


if __name__ == "__main__":
    print("=== Real GitHub API Client Demo ===\n")

    # Initialize client (uses .env automatically)
    client = GitHubClient()

    # Get repo info
    print("1. Repository information:")
    info = client.get_repository_info()
    print(f"  Name: {info['full_name']}")
    print(f"  URL: {info['html_url']}")
    print(f"  Open issues: {info['open_issues_count']}")

    # List open issues
    print("\n2. Open issues:")
    issues = client.list_issues(state="open")
    for issue in issues[:5]:  # Show first 5
        assignee = issue.assignee or "Unassigned"
        print(f"  #{issue.number}: {issue.title} (@{assignee})")

    # Filter by assignee
    print("\n3. Issues assigned to me:")
    my_username = client.repo_owner
    my_issues = client.list_issues(assignee=my_username)
    for issue in my_issues:
        print(f"  #{issue.number}: {issue.title}")

    # Get specific issue
    if issues:
        first_issue_num = issues[0].number
        print(f"\n4. Details of issue #{first_issue_num}:")
        issue = client.get_issue(first_issue_num)
        if issue:
            print(f"  Title: {issue.title}")
            print(f"  State: {issue.state}")
            print(f"  Labels: {', '.join(issue.labels)}")
            print(f"  Comments: {issue.comments_count}")

            # Add a test comment
            print(f"\n5. Adding test comment to issue #{first_issue_num}:")
            comment = client.add_issue_comment(
                first_issue_num, "🤖 Test comment from MCP GitHub client"
            )
            if comment:
                print(f"  ✓ Comment added: {comment.html_url}")
                print(f"     By: @{comment.user}")
                print(f"     Body: {comment.body}")

            # List all comments
            print(f"\n6. All comments on issue #{first_issue_num}:")
            comments = client.get_issue_comments(first_issue_num)
            for c in comments[-3:]:  # Show last 3
                print(f"  - @{c.user}: {c.body[:50]}...")

    # List recent commits
    print("\n7. Recent commits:")
    commits = client.list_commits(limit=3)
    for commit in commits:
        print(
            f"  {commit.sha[:7]}: {commit.message.split(chr(10))[0][:60]} (@{commit.author})"
        )

    print("\n✓ Real GitHub API client demo complete!")
    print(f"  Check your repo at: {client.repo.html_url}")
