"""
Pydantic schemas for GitHub API responses.

These models define the structure of data returned from GitHub API
and used throughout the MCP server.
"""

from typing import List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_serializer


class User(BaseModel):
    """GitHub user model."""

    login: str = Field(..., description="Username")
    id: int = Field(..., description="User ID")
    avatar_url: Optional[str] = Field(None, description="Avatar URL")
    html_url: Optional[str] = Field(None, description="Profile URL")


class Label(BaseModel):
    """GitHub label model."""

    name: str = Field(..., description="Label name")
    color: str = Field(..., description="Label color (hex without #)")
    description: Optional[str] = Field(None, description="Label description")


class Issue(BaseModel):
    """GitHub issue model."""

    number: int = Field(..., description="Issue number")
    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue body/description")
    state: Literal["open", "closed"] = Field(..., description="Issue state")
    labels: List[str] = Field(default_factory=list, description="Label names")
    assignee: Optional[str] = Field(None, description="Assignee username")
    assignees: List[str] = Field(
        default_factory=list, description="All assignee usernames"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closed timestamp")
    html_url: str = Field(..., description="Issue URL")
    comments_count: int = Field(0, description="Number of comments")

    @field_serializer("created_at", "updated_at", "closed_at", when_used="json")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class Comment(BaseModel):
    """GitHub issue comment model."""

    id: int = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment text")
    user: str = Field(..., description="Comment author username")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    html_url: str = Field(..., description="Comment URL")

    @field_serializer("created_at", "updated_at", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class PullRequest(BaseModel):
    """GitHub pull request model."""

    number: int = Field(..., description="PR number")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(None, description="PR description")
    state: Literal["open", "closed"] = Field(..., description="PR state")
    draft: bool = Field(False, description="Draft status")
    merged: bool = Field(False, description="Merged status")
    head_ref: str = Field(..., description="Source branch")
    base_ref: str = Field(..., description="Target branch")
    user: str = Field(..., description="PR author username")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    merged_at: Optional[datetime] = Field(None, description="Merged timestamp")
    html_url: str = Field(..., description="PR URL")
    comments_count: int = Field(0, description="Number of comments")

    @field_serializer("created_at", "updated_at", "merged_at", when_used="json")
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None


class Commit(BaseModel):
    """GitHub commit model."""

    sha: str = Field(..., description="Commit SHA")
    message: str = Field(..., description="Commit message")
    author: str = Field(..., description="Commit author username")
    date: datetime = Field(..., description="Commit timestamp")
    html_url: str = Field(..., description="Commit URL")

    @field_serializer("date", when_used="json")
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class Repository(BaseModel):
    """GitHub repository model."""

    name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner username")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    html_url: str = Field(..., description="Repository URL")
    description: Optional[str] = Field(None, description="Repository description")
    default_branch: str = Field("main", description="Default branch name")
    open_issues_count: int = Field(0, description="Number of open issues")
    forks_count: int = Field(0, description="Number of forks")
    stargazers_count: int = Field(0, description="Number of stars")
    private: bool = Field(False, description="Private repository flag")


# Request models for API operations


class IssueFilters(BaseModel):
    """Filters for listing issues."""

    assignee: Optional[str] = Field(None, description="Filter by assignee username")
    labels: Optional[List[str]] = Field(None, description="Filter by label names")
    state: Literal["open", "closed", "all"] = Field(
        "open", description="Filter by state"
    )
    sort: Literal["created", "updated", "comments"] = Field(
        "created", description="Sort field"
    )
    direction: Literal["asc", "desc"] = Field("desc", description="Sort direction")


class IssueCreate(BaseModel):
    """Model for creating a new issue."""

    title: str = Field(..., description="Issue title")
    body: Optional[str] = Field(None, description="Issue description")
    assignees: Optional[List[str]] = Field(None, description="Assignee usernames")
    labels: Optional[List[str]] = Field(None, description="Label names")


class IssueUpdate(BaseModel):
    """Model for updating an issue."""

    title: Optional[str] = Field(None, description="New title")
    body: Optional[str] = Field(None, description="New description")
    state: Optional[Literal["open", "closed"]] = Field(None, description="New state")
    assignees: Optional[List[str]] = Field(None, description="New assignees")
    labels: Optional[List[str]] = Field(None, description="New labels")


class CommentCreate(BaseModel):
    """Model for creating a comment."""

    body: str = Field(..., description="Comment text")


# ============================================================================
# Tool Input/Output Schemas
# ============================================================================


class ListIssuesInput(BaseModel):
    """Input schema for list_issues tool."""

    assignee: Optional[str] = Field(
        default=None, description="Filter by assignee username"
    )
    labels: Optional[str] = Field(
        default=None, description="Comma-separated label names to filter by"
    )
    state: Literal["open", "closed", "all"] = Field(
        default="open", description="Filter by state"
    )
    sort: Literal["created", "updated", "comments"] = Field(
        default="created", description="Sort by field"
    )
    direction: Literal["asc", "desc"] = Field(
        default="desc", description="Sort direction"
    )


class ListIssuesOutput(BaseModel):
    """Output schema for list_issues tool."""

    count: int = Field(..., description="Number of issues found")
    issues: List[Issue] = Field(..., description="List of issues")


class GetIssueInput(BaseModel):
    """Input schema for get_issue tool."""

    issue_number: int = Field(..., description="Issue number", gt=0)


class GetIssueOutput(BaseModel):
    """Output schema for get_issue tool."""

    issue: Optional[Issue] = Field(..., description="Issue details, null if not found")


class UpdateIssueStatusInput(BaseModel):
    """Input schema for update_issue_status tool."""

    issue_number: int = Field(..., description="Issue number", gt=0)
    new_state: Literal["open", "closed"] = Field(..., description="New state")


class UpdateIssueStatusOutput(BaseModel):
    """Output schema for update_issue_status tool."""

    success: bool = Field(..., description="Whether update was successful")
    issue: Optional[Issue] = Field(None, description="Updated issue details")
    message: str = Field(..., description="Status message")


class AddIssueCommentInput(BaseModel):
    """Input schema for add_issue_comment tool."""

    issue_number: int = Field(..., description="Issue number", gt=0)
    comment: str = Field(..., description="Comment text", min_length=1)


class AddIssueCommentOutput(BaseModel):
    """Output schema for add_issue_comment tool."""

    success: bool = Field(..., description="Whether comment was added successfully")
    comment: Optional[Comment] = Field(None, description="Created comment details")
    message: str = Field(..., description="Status message")


class GetIssueCommentsInput(BaseModel):
    """Input schema for get_issue_comments tool."""

    issue_number: int = Field(..., description="Issue number", gt=0)


class GetIssueCommentsOutput(BaseModel):
    """Output schema for get_issue_comments tool."""

    count: int = Field(..., description="Number of comments")
    comments: List[Comment] = Field(..., description="List of comments")


class GetRepositoryInfoOutput(BaseModel):
    """Output schema for get_repository_info tool."""

    repository: Repository = Field(..., description="Repository information")


class ListLabelsOutput(BaseModel):
    """Output schema for list_labels tool."""

    count: int = Field(..., description="Number of labels")
    labels: List[Label] = Field(..., description="List of labels")


class ListCommitsInput(BaseModel):
    """Input schema for list_commits tool."""

    author: Optional[str] = Field(default=None, description="Filter by author username")
    since: Optional[str] = Field(
        default=None, description="ISO datetime string - only commits after this date"
    )
    limit: int = Field(
        default=10, description="Maximum number of commits to return", gt=0, le=100
    )


class ListCommitsOutput(BaseModel):
    """Output schema for list_commits tool."""

    count: int = Field(..., description="Number of commits returned")
    commits: List[Commit] = Field(..., description="List of commits")
