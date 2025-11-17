"""
GitHub API Stub for isolated testing of MCP tools.

This module provides stub implementations of GitHub API operations
required for core MCP tools. These stubs simulate GitHub API responses
without making actual API calls, enabling fast, isolated testing.

Usage:
    from stubs.github import GitHubStub

    stub = GitHubStub()
    issues = stub.list_issues(assignee="sagarsrc", state="open")
"""

from typing import Dict, List, Optional, Literal
from datetime import datetime, timedelta
from dataclasses import dataclass, field


# ============================================================================
# Data Models (matching GitHub API structure)
# ============================================================================


@dataclass
class User:
    """GitHub user model"""

    login: str
    id: int
    type: str = "User"


@dataclass
class Label:
    """GitHub label model"""

    name: str
    color: str
    description: str = ""


@dataclass
class Issue:
    """GitHub issue model"""

    number: int
    title: str
    body: str
    state: Literal["open", "closed"]
    labels: List[Label]
    assignee: Optional[User]
    created_at: str
    updated_at: str
    html_url: str
    comments: int = 0


@dataclass
class Comment:
    """GitHub issue comment model"""

    id: int
    body: str
    user: User
    created_at: str
    html_url: str


@dataclass
class Commit:
    """GitHub commit model"""

    sha: str
    message: str
    author: User
    date: str
    html_url: str


# ============================================================================
# GitHub Stub Implementation
# ============================================================================


class GitHubStub:
    """
    Stub implementation of GitHub API for testing.

    Maintains in-memory state of issues, comments, and commits
    that can be manipulated through API-like methods.
    """

    def __init__(self, repo_owner: str = "sagarsrc", repo_name: str = "ai-dummy-app"):
        """
        Initialize GitHub stub with default repository.

        Args:
            repo_owner: Repository owner username
            repo_name: Repository name
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name

        # In-memory storage
        self._issues: Dict[int, Issue] = {}
        self._comments: Dict[int, List[Comment]] = {}  # issue_number -> comments
        self._commits: List[Commit] = []
        self._labels: Dict[str, Label] = {}

        # Auto-increment counters
        self._next_issue_number = 1
        self._next_comment_id = 1

        # Initialize with demo data
        self._initialize_demo_data()

    def _initialize_demo_data(self):
        """Initialize stub with demo data matching the datagen output."""
        # Create labels
        self._create_label("P0", "b60205", "Critical")
        self._create_label("P1", "d93f0b", "High priority")
        self._create_label("P2", "fbca04", "Normal priority")
        self._create_label("bug", "d73a4a", "Bug fix")
        self._create_label("feature", "0e8a16", "New feature")
        self._create_label("improvement", "1d76db", "Enhancement")
        self._create_label("team-ai", "5319e7", "AI team")
        self._create_label("team-backend", "0052cc", "Backend team")
        self._create_label("team-frontend", "bfdadc", "Frontend team")

        # Create users
        sagar = User(login="sagarsrc", id=1)
        zeeshan = User(login="zeeshan-bandar", id=2)
        swathi = User(login="Swathipoojari", id=3)

        # Create demo issues (matching the datagen)
        now = datetime.now()

        # Issue 1: Add streaming support (In Progress)
        self._create_issue(
            title="Add streaming support for LLM responses",
            body="Users want to see responses appear word-by-word instead of waiting for complete response.",
            labels=["feature", "team-ai", "P1"],
            assignee=sagar,
            state="open",
        )

        # Issue 2: Fix chat history (In Review)
        self._create_issue(
            title="Fix chat history not loading on page refresh",
            body="When user refreshes page, chat history disappears. Should persist in localStorage.",
            labels=["bug", "team-frontend", "P1"],
            assignee=zeeshan,
            state="open",
        )

        # Issue 3: Add rate limiting (In Progress)
        self._create_issue(
            title="Add rate limiting to prevent abuse",
            body="Need to prevent users from spamming the API and racking up LLM costs.",
            labels=["feature", "team-backend", "P1"],
            assignee=swathi,
            state="open",
        )

        # Issue 4: Improve prompt template (Backlog)
        self._create_issue(
            title="Improve system prompt template",
            body="Current system prompt is generic. Need to make it more specific to our use case.",
            labels=["improvement", "team-ai", "P2"],
            assignee=sagar,
            state="open",
        )

        # Issue 5: Dark mode (Backlog)
        self._create_issue(
            title="Add dark mode toggle to UI",
            body="Users requesting dark mode for late-night usage.",
            labels=["feature", "team-frontend", "P2"],
            assignee=zeeshan,
            state="open",
        )

        # Issue 6: Deploy to production (In Review)
        self._create_issue(
            title="Deploy v1.0 to production",
            body="First production deployment.",
            labels=["P0", "team-backend"],
            assignee=swathi,
            state="open",
        )

        # Issue 7: User authentication (Done)
        self._create_issue(
            title="Add basic user authentication with Google OAuth",
            body="Implemented Google OAuth for user login.",
            labels=["feature", "team-backend", "P1"],
            assignee=swathi,
            state="closed",
        )

        # Issue 8: Export chat history (Backlog)
        self._create_issue(
            title="Allow users to export chat history as PDF",
            body="Users want to save/share their conversations.",
            labels=["feature", "team-frontend", "P2"],
            assignee=zeeshan,
            state="open",
        )

        # Create some demo commits
        self._add_commit(
            message="feat(ai): Add SSE streaming for LLM responses",
            author=sagar,
            date=(now - timedelta(hours=2)).isoformat(),
        )
        self._add_commit(
            message="fix(frontend): Persist chat history in localStorage",
            author=zeeshan,
            date=(now - timedelta(hours=1)).isoformat(),
        )

    def _create_label(self, name: str, color: str, description: str):
        """Internal: Create a label"""
        self._labels[name] = Label(name=name, color=color, description=description)

    def _create_issue(
        self,
        title: str,
        body: str,
        labels: List[str],
        assignee: Optional[User],
        state: Literal["open", "closed"] = "open",
    ) -> Issue:
        """Internal: Create an issue"""
        issue_number = self._next_issue_number
        self._next_issue_number += 1

        now = datetime.now().isoformat()
        issue = Issue(
            number=issue_number,
            title=title,
            body=body,
            state=state,
            labels=[self._labels[l] for l in labels if l in self._labels],
            assignee=assignee,
            created_at=now,
            updated_at=now,
            html_url=f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{issue_number}",
        )
        self._issues[issue_number] = issue
        self._comments[issue_number] = []
        return issue

    def _add_commit(self, message: str, author: User, date: str) -> Commit:
        """Internal: Add a commit"""
        sha = f"abc{len(self._commits):04d}"
        commit = Commit(
            sha=sha,
            message=message,
            author=author,
            date=date,
            html_url=f"https://github.com/{self.repo_owner}/{self.repo_name}/commit/{sha}",
        )
        self._commits.append(commit)
        return commit

    # ========================================================================
    # Public API Methods (Core Functions)
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
            assignee: Filter by assignee username (e.g., "sagarsrc")
            labels: Filter by labels (e.g., ["team-ai", "P1"])
            state: Filter by state ("open", "closed", "all")

        Returns:
            List of matching issues
        """
        results = []

        for issue in self._issues.values():
            # State filter
            if state != "all" and issue.state != state:
                continue

            # Assignee filter
            if assignee and (not issue.assignee or issue.assignee.login != assignee):
                continue

            # Labels filter
            if labels:
                issue_label_names = {l.name for l in issue.labels}
                if not all(label in issue_label_names for label in labels):
                    continue

            results.append(issue)

        # Sort by issue number descending (newest first)
        return sorted(results, key=lambda x: x.number, reverse=True)

    def get_issue(self, issue_number: int) -> Optional[Issue]:
        """
        Get a specific issue by number.

        Args:
            issue_number: Issue number

        Returns:
            Issue object or None if not found
        """
        return self._issues.get(issue_number)

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
        issue = self._issues.get(issue_number)
        if not issue:
            return None

        issue.state = new_state
        issue.updated_at = datetime.now().isoformat()
        return issue

    def add_issue_comment(
        self, issue_number: int, comment_body: str, author: User
    ) -> Optional[Comment]:
        """
        Add a comment to an issue.

        Args:
            issue_number: Issue number
            comment_body: Comment text
            author: User adding the comment

        Returns:
            Created comment or None if issue not found
        """
        if issue_number not in self._issues:
            return None

        comment_id = self._next_comment_id
        self._next_comment_id += 1

        comment = Comment(
            id=comment_id,
            body=comment_body,
            user=author,
            created_at=datetime.now().isoformat(),
            html_url=f"https://github.com/{self.repo_owner}/{self.repo_name}/issues/{issue_number}#issuecomment-{comment_id}",
        )

        self._comments[issue_number].append(comment)
        self._issues[issue_number].comments += 1
        self._issues[issue_number].updated_at = datetime.now().isoformat()

        return comment

    def list_commits(
        self, author: Optional[str] = None, since: Optional[str] = None, limit: int = 10
    ) -> List[Commit]:
        """
        List recent commits.

        Args:
            author: Filter by author username
            since: ISO datetime string - only commits after this date
            limit: Maximum number of commits to return

        Returns:
            List of commits
        """
        results = []

        for commit in reversed(self._commits):  # Newest first
            # Author filter
            if author and commit.author.login != author:
                continue

            # Date filter
            if since and commit.date < since:
                continue

            results.append(commit)

            if len(results) >= limit:
                break

        return results

    def get_repository_info(self) -> Dict:
        """
        Get repository metadata.

        Returns:
            Repository information dict
        """
        return {
            "name": self.repo_name,
            "owner": self.repo_owner,
            "full_name": f"{self.repo_owner}/{self.repo_name}",
            "html_url": f"https://github.com/{self.repo_owner}/{self.repo_name}",
            "description": "Demo SaaS app for MCP blog - AI-powered content platform",
            "default_branch": "main",
            "open_issues_count": sum(
                1 for i in self._issues.values() if i.state == "open"
            ),
            "total_issues_count": len(self._issues),
        }

    def list_labels(self) -> List[Label]:
        """
        Get all available labels.

        Returns:
            List of labels
        """
        return list(self._labels.values())

    def get_issue_comments(self, issue_number: int) -> List[Comment]:
        """
        Get all comments for an issue.

        Args:
            issue_number: Issue number

        Returns:
            List of comments for the issue
        """
        return self._comments.get(issue_number, [])

    # ========================================================================
    # Utility Methods for Testing
    # ========================================================================

    def reset(self):
        """Reset stub to initial state with demo data."""
        self._issues.clear()
        self._comments.clear()
        self._commits.clear()
        self._labels.clear()
        self._next_issue_number = 1
        self._next_comment_id = 1
        self._initialize_demo_data()

    def get_stats(self) -> Dict:
        """Get statistics about current stub state."""
        return {
            "total_issues": len(self._issues),
            "open_issues": sum(1 for i in self._issues.values() if i.state == "open"),
            "closed_issues": sum(
                1 for i in self._issues.values() if i.state == "closed"
            ),
            "total_comments": sum(
                len(comments) for comments in self._comments.values()
            ),
            "total_commits": len(self._commits),
            "total_labels": len(self._labels),
        }


# ============================================================================
# Example Usage
# ============================================================================


if __name__ == "__main__":
    # Create stub
    stub = GitHubStub()

    print("=== GitHub Stub Demo ===\n")

    # List all open issues
    print("1. All open issues:")
    issues = stub.list_issues(state="open")
    for issue in issues:
        assignee = issue.assignee.login if issue.assignee else "Unassigned"
        print(f"  #{issue.number}: {issue.title} (@{assignee})")

    # Filter by assignee
    print("\n2. Issues assigned to sagarsrc:")
    sagar_issues = stub.list_issues(assignee="sagarsrc")
    for issue in sagar_issues:
        print(f"  #{issue.number}: {issue.title}")

    # Filter by team
    print("\n3. Frontend team issues:")
    frontend_issues = stub.list_issues(labels=["team-frontend"])
    for issue in frontend_issues:
        print(f"  #{issue.number}: {issue.title}")

    # Get specific issue
    print("\n4. Details of issue #1:")
    issue = stub.get_issue(1)
    if issue:
        print(f"  Title: {issue.title}")
        print(f"  State: {issue.state}")
        print(f"  Labels: {', '.join(l.name for l in issue.labels)}")
        print(f"  URL: {issue.html_url}")

    # Update issue status
    print("\n5. Moving issue #1 to closed:")
    updated = stub.update_issue_status(1, "closed")
    if updated:
        print(f"  ✓ Issue #{updated.number} is now {updated.state}")

    # Add comment
    print("\n6. Adding comment to issue #2:")
    author = User(login="sagarsrc", id=1)
    comment = stub.add_issue_comment(2, "LGTM! Ready to merge.", author)
    if comment:
        print(f"  ✓ Comment added by @{comment.user.login}")
        print(f"     Body: {comment.body}")
        print(f"     Comment ID: {comment.id}")

    # Verify comments were stored
    print("\n6b. Verify comment was stored in issue #2:")
    comments = stub.get_issue_comments(2)
    print(f"  Total comments on issue #2: {len(comments)}")
    for c in comments:
        print(f"    - @{c.user.login}: {c.body}")

    # List recent commits
    print("\n7. Recent commits:")
    commits = stub.list_commits(limit=5)
    for commit in commits:
        print(f"  {commit.sha[:7]}: {commit.message} (@{commit.author.login})")

    # Get stats
    print("\n8. Repository stats:")
    stats = stub.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✓ GitHub stub demo complete!")
