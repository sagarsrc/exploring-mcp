"""
Configuration for MCP Server.

Assumes environment variables are already exported:
- GITHUB_TOKEN: Personal access token for GitHub API
- GITHUB_USERNAME: GitHub username (repository owner)
- REPO_NAME: Repository name
- NOTION_TOKEN: Notion integration token
- SLACK_TOKEN: Slack bot token (starts with xoxb-)
"""

import os


class Config:
    """Configuration class for MCP server."""

    # Server Configuration
    SERVER_NAME: str = "Multi-Service MCP Server"
    SERVER_VERSION: str = "1.0.0"

    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
    REPO_NAME: str = os.getenv("REPO_NAME", "")

    # Notion Configuration
    NOTION_TOKEN: str = os.getenv("NOTION_TOKEN", "")

    # Slack Configuration
    SLACK_TOKEN: str = os.getenv("SLACK_TOKEN", "")

    @classmethod
    def validate(cls) -> None:
        """
        Validate required configuration.

        Raises:
            ValueError: If any required environment variables are missing
        """
        errors = []

        # GitHub validation
        if not cls.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN")
        if not cls.GITHUB_USERNAME:
            errors.append("GITHUB_USERNAME")
        if not cls.REPO_NAME:
            errors.append("REPO_NAME")

        # Notion validation
        if not cls.NOTION_TOKEN:
            errors.append("NOTION_TOKEN")

        # Slack validation
        if not cls.SLACK_TOKEN:
            errors.append("SLACK_TOKEN")

        if errors:
            raise ValueError(
                f"Missing required environment variables: {', '.join(errors)}"
            )

    @classmethod
    def get_full_repo_name(cls) -> str:
        """
        Get full repository name in owner/repo format.

        Returns:
            Full repository name (e.g., "octocat/Hello-World")
        """
        return f"{cls.GITHUB_USERNAME}/{cls.REPO_NAME}"
