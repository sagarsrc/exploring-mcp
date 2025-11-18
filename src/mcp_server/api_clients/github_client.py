"""
GitHub API client for MCP server.

Provides GitHub API operations using PyGithub library.
Implements core functions needed for GitHub MCP tools.
"""

from typing import List, Optional, Literal, Dict, Any
from github import Github, GithubException, Auth
import requests

from mcp_server.schemas.github_schemas import (
    Issue,
    Comment,
    PullRequest,
    Commit,
    Repository,
    Label,
    IssueFilters,
    ProjectV2,
    ProjectV2Field,
    ProjectV2FieldOption,
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

    # ========================================================================
    # GitHub Projects (v2) Operations
    # ========================================================================

    def _graphql_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query against GitHub API.

        Args:
            query: GraphQL query string
            variables: Optional query variables

        Returns:
            Query result data
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        result = response.json()

        if "errors" in result:
            raise Exception(f"GraphQL errors: {result['errors']}")

        return result["data"]

    def list_projects(self) -> List[ProjectV2]:
        """
        List all projects for the user (owner).

        This queries user-level projects, which includes all projects
        created by the user regardless of repository association.

        Returns:
            List of projects
        """
        query = """
        query($login: String!) {
            user(login: $login) {
                projectsV2(first: 20) {
                    nodes {
                        id
                        number
                        title
                        url
                        closed
                    }
                }
            }
        }
        """

        variables = {
            "login": self.repo_owner,
        }

        data = self._graphql_query(query, variables)
        projects_data = data.get("user", {}).get("projectsV2", {}).get("nodes", [])

        return [
            ProjectV2(
                id=p["id"],
                number=p["number"],
                title=p["title"],
                url=p["url"],
                closed=p["closed"],
            )
            for p in projects_data
            if p
        ]

    def get_project_fields(self, project_id: str) -> List[ProjectV2Field]:
        """
        Get all fields for a project, including their options.

        Uses GraphQL API with __typename to detect field types:
        - ProjectV2Field: Basic text fields
        - ProjectV2SingleSelectField: Single-select fields with options
        - ProjectV2IterationField: Iteration fields with sprint/iteration options

        IMPORTANT: Options must be converted to ProjectV2FieldOption objects,
        not plain dicts, for proper FastMCP serialization.

        Args:
            project_id: Project ID (starts with "PVT_")

        Returns:
            List of ProjectV2Field objects with properly typed options
        """
        query = """
        query($projectId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    fields(first: 20) {
                        nodes {
                            __typename
                            ... on ProjectV2Field {
                                id
                                name
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                                configuration {
                                    iterations {
                                        id
                                        title
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"projectId": project_id}
        data = self._graphql_query(query, variables)
        fields_data = data.get("node", {}).get("fields", {}).get("nodes", [])

        fields = []
        for field in fields_data:
            if not field:
                continue

            # Use __typename to determine field type
            typename = field.get("__typename", "ProjectV2Field")

            if typename == "ProjectV2SingleSelectField":
                field_type = "single_select"
                options_data = field.get("options", [])
                # Convert dicts to ProjectV2FieldOption objects
                options = (
                    [
                        ProjectV2FieldOption(id=opt["id"], name=opt["name"])
                        for opt in options_data
                    ]
                    if options_data
                    else None
                )
            elif typename == "ProjectV2IterationField":
                field_type = "iteration"
                # Convert iterations to options format for consistency
                iterations = field.get("configuration", {}).get("iterations", [])
                options = (
                    [
                        ProjectV2FieldOption(id=it["id"], name=it.get("title", ""))
                        for it in iterations
                    ]
                    if iterations
                    else None
                )
            else:
                field_type = "text"
                options = None

            fields.append(
                ProjectV2Field(
                    id=field["id"],
                    name=field["name"],
                    type=field_type,
                    options=options,
                )
            )

        return fields

    def add_issue_to_project(self, project_id: str, issue_id: str) -> Optional[str]:
        """
        Add an issue to a project.

        Args:
            project_id: Project ID
            issue_id: Issue node ID (from GraphQL)

        Returns:
            Project item ID if successful, None otherwise
        """
        query = """
        mutation($projectId: ID!, $contentId: ID!) {
            addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
                item {
                    id
                }
            }
        }
        """

        variables = {
            "projectId": project_id,
            "contentId": issue_id,
        }

        try:
            data = self._graphql_query(query, variables)
            return data.get("addProjectV2ItemById", {}).get("item", {}).get("id")
        except Exception:
            return None

    def get_issue_node_id(self, issue_number: int) -> Optional[str]:
        """
        Get the GraphQL node ID for an issue.

        Args:
            issue_number: Issue number

        Returns:
            GraphQL node ID
        """
        query = """
        query($owner: String!, $repo: String!, $number: Int!) {
            repository(owner: $owner, name: $repo) {
                issue(number: $number) {
                    id
                }
            }
        }
        """

        variables = {
            "owner": self.repo_owner,
            "repo": self.repo_name,
            "number": issue_number,
        }

        try:
            data = self._graphql_query(query, variables)
            return data.get("repository", {}).get("issue", {}).get("id")
        except Exception:
            return None

    def update_project_item_field(
        self,
        project_id: str,
        item_id: str,
        field_id: str,
        option_id: str,
    ) -> bool:
        """
        Update a field value for a project item.

        Args:
            project_id: Project ID
            item_id: Project item ID
            field_id: Field ID
            option_id: Option ID (for single-select fields)

        Returns:
            True if successful, False otherwise
        """
        query = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: ProjectV2FieldValue!) {
            updateProjectV2ItemFieldValue(
                input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: $value
                }
            ) {
                projectV2Item {
                    id
                }
            }
        }
        """

        variables = {
            "projectId": project_id,
            "itemId": item_id,
            "fieldId": field_id,
            "value": {"singleSelectOptionId": option_id},
        }

        try:
            self._graphql_query(query, variables)
            return True
        except Exception:
            return False

    def get_project_item_for_issue(
        self, project_id: str, issue_number: int
    ) -> Optional[str]:
        """
        Get the project item ID for an issue in a project.

        Args:
            project_id: Project ID
            issue_number: Issue number

        Returns:
            Project item ID if found, None otherwise
        """
        query = """
        query($projectId: ID!) {
            node(id: $projectId) {
                ... on ProjectV2 {
                    items(first: 100) {
                        nodes {
                            id
                            content {
                                ... on Issue {
                                    number
                                }
                            }
                        }
                    }
                }
            }
        }
        """

        variables = {"projectId": project_id}

        try:
            data = self._graphql_query(query, variables)
            items = data.get("node", {}).get("items", {}).get("nodes", [])

            for item in items:
                if not item or not item.get("content"):
                    continue
                if item["content"].get("number") == issue_number:
                    return item["id"]

            return None
        except Exception:
            return None
