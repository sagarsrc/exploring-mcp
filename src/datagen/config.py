"""Configuration module for GitHub project setup."""

import os
from typing import Dict, List, Tuple
from pathlib import Path
from dotenv import load_dotenv


class Config:
    """Configuration loader for GitHub automation."""

    def __init__(self, env_path: str = None):
        """Initialize configuration from environment file.

        Args:
            env_path: Path to .env file. If None, searches in parent directories.
        """
        if env_path:
            load_dotenv(env_path)
        else:
            # Search for .env in current and parent directories
            current = Path(__file__).resolve()
            for parent in [current.parent] + list(current.parents):
                env_file = parent / ".env"
                if env_file.exists():
                    load_dotenv(env_file)
                    break

        # GitHub credentials
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_username = os.getenv("GITHUB_USERNAME")

        # Repository configuration
        self.repo_name = os.getenv("REPO_NAME")
        self.repo_description = os.getenv("REPO_DESCRIPTION")
        self.repo_visibility = os.getenv("REPO_VISIBILITY", "public")

        # Project configuration
        self.project_name = os.getenv("PROJECT_NAME")
        self.project_description = os.getenv("PROJECT_DESCRIPTION")

        # Team members (parse from env)
        self.team_backend = self._parse_team_members(os.getenv("TEAM_BACKEND", ""))
        self.team_frontend = self._parse_team_members(os.getenv("TEAM_FRONTEND", ""))
        self.team_ai = self._parse_team_members(os.getenv("TEAM_AI", ""))
        self.managers = self._parse_team_members(os.getenv("MANAGERS", ""))

        # Validate required fields
        self._validate()

    def _parse_team_members(self, team_str: str) -> List[Dict[str, str]]:
        """Parse team member string into list of dicts.

        Format: "Nickname|username,Nickname2|username2"

        Args:
            team_str: Team member string from environment

        Returns:
            List of dicts with 'nickname' and 'username' keys
        """
        members = []
        if not team_str:
            return members

        for member in team_str.split(","):
            member = member.strip()
            if "|" in member:
                nickname, username = member.split("|", 1)
                members.append(
                    {"nickname": nickname.strip(), "username": username.strip()}
                )

        return members

    def _validate(self):
        """Validate required configuration fields."""
        required = {
            "GITHUB_TOKEN": self.github_token,
            "GITHUB_USERNAME": self.github_username,
            "REPO_NAME": self.repo_name,
        }

        missing = [key for key, value in required.items() if not value]
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    def get_all_members(self) -> List[Dict[str, str]]:
        """Get all team members across all teams.

        Returns:
            List of all team members
        """
        return self.team_backend + self.team_frontend + self.team_ai + self.managers

    def get_member_by_nickname(self, nickname: str) -> Dict[str, str]:
        """Get team member by nickname.

        Args:
            nickname: Member's nickname

        Returns:
            Member dict with nickname and username

        Raises:
            ValueError: If nickname not found
        """
        for member in self.get_all_members():
            if member["nickname"].lower() == nickname.lower():
                return member

        raise ValueError(f"Team member with nickname '{nickname}' not found")

    def get_username(self, nickname: str) -> str:
        """Get GitHub username for a nickname.

        Args:
            nickname: Member's nickname

        Returns:
            GitHub username
        """
        return self.get_member_by_nickname(nickname)["username"]


# Labels configuration
LABELS = {
    # Priority
    "P0": {"color": "b60205", "description": "Critical"},
    "P1": {"color": "d93f0b", "description": "High priority"},
    "P2": {"color": "fbca04", "description": "Normal priority"},
    # Type
    "bug": {"color": "d73a4a", "description": "Bug fix"},
    "feature": {"color": "0e8a16", "description": "New feature"},
    "improvement": {"color": "1d76db", "description": "Enhancement"},
    # Team
    "team-ai": {"color": "5319e7", "description": "AI team"},
    "team-backend": {"color": "0052cc", "description": "Backend team"},
    "team-frontend": {"color": "bfdadc", "description": "Frontend team"},
}


# Project board columns
PROJECT_COLUMNS = ["Backlog", "In Progress", "In Review", "Done"]
