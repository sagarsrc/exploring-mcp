"""
Configuration for GitHub MCP Server.

Assumes environment variables are already exported:
- GITHUB_TOKEN: Personal access token for GitHub API
- GITHUB_USERNAME: GitHub username (repository owner)
- REPO_NAME: Repository name
"""

import os


class Config:
    """Configuration class for GitHub MCP server."""

    # Server Configuration
    SERVER_NAME: str = "GitHub MCP Server"
    SERVER_VERSION: str = "1.0.0"

    # GitHub Configuration
    GITHUB_TOKEN: str = os.getenv("GITHUB_TOKEN", "")
    GITHUB_USERNAME: str = os.getenv("GITHUB_USERNAME", "")
    REPO_NAME: str = os.getenv("REPO_NAME", "")

    @classmethod
    def validate(cls) -> None:
        """
        Validate required GitHub configuration.

        Raises:
            ValueError: If any required environment variables are missing
        """
        errors = []
        if not cls.GITHUB_TOKEN:
            errors.append("GITHUB_TOKEN")
        if not cls.GITHUB_USERNAME:
            errors.append("GITHUB_USERNAME")
        if not cls.REPO_NAME:
            errors.append("REPO_NAME")

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
