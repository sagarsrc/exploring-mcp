"""Project manager for creating and managing GitHub projects."""

import time
from typing import List, Dict, Optional
from github import GithubException
from datagen.github_client import GitHubClient
from datagen.config import Config


class ProjectManager:
    """Manager for creating and organizing GitHub projects."""

    def __init__(self, client: GitHubClient, config: Config):
        """Initialize project manager.

        Args:
            client: GitHub client instance
            config: Configuration instance
        """
        self.client = client
        self.config = config

    def setup_repository(self, labels: Dict[str, Dict[str, str]]) -> object:
        """Set up repository with initial structure and labels.

        Args:
            labels: Dict of label configurations

        Returns:
            Repository object
        """
        print("\n" + "="*60)
        print("Setting up Repository")
        print("="*60)

        # Create or get repository
        repo = self.client.get_or_create_repo(
            name=self.config.repo_name,
            description=self.config.repo_description,
            private=(self.config.repo_visibility == 'private')
        )

        # Create labels
        self.client.create_labels(repo, labels)

        # Create basic folder structure
        self._create_folder_structure(repo)

        return repo

    def _create_folder_structure(self, repo) -> None:
        """Create basic folder structure in repository.

        Args:
            repo: Repository object
        """
        print("\nCreating folder structure...")

        default_branch = self.client.get_default_branch(repo)

        folders = [
            ('backend/.gitkeep', 'Create backend directory'),
            ('frontend/.gitkeep', 'Create frontend directory'),
            ('ai-service/.gitkeep', 'Create ai-service directory'),
            ('docs/.gitkeep', 'Create docs directory'),
        ]

        for path, message in folders:
            try:
                self.client.create_file(
                    repo=repo,
                    path=path,
                    content='',
                    message=message,
                    branch=default_branch
                )
            except Exception as e:
                # Folder might already exist, continue
                pass

        # Update README if needed
        readme_content = f"""# {self.config.repo_name}

{self.config.repo_description}

## Team
- **AI Team**: {', '.join(m['nickname'] for m in self.config.team_ai)}
- **Backend Team**: {', '.join(m['nickname'] for m in self.config.team_backend)}
- **Frontend Team**: {', '.join(m['nickname'] for m in self.config.team_frontend)}
- **Managers**: {', '.join(m['nickname'] for m in self.config.managers)}

## Structure
```
{self.config.repo_name}/
├── backend/        # FastAPI backend
├── frontend/       # React frontend
├── ai-service/     # LLM integration
└── docs/
```
"""

        try:
            self.client.create_file(
                repo=repo,
                path='README.md',
                content=readme_content,
                message='Update README with project info',
                branch=default_branch
            )
        except Exception:
            # README might already exist with different content
            pass

    def create_project_board(self, repo, issues: List[object],
                            status_mapping: Dict[int, str]) -> Optional[object]:
        """Create GitHub project board and add issues.

        Note: GitHub Projects V2 API requires different approach.
        This method provides a basic implementation that may need
        manual adjustment via web UI.

        Args:
            repo: Repository object
            issues: List of issue objects
            status_mapping: Dict mapping issue number to status column

        Returns:
            Project object or None if creation fails
        """
        print("\n" + "="*60)
        print("Creating Project Board")
        print("="*60)

        print("\n⚠ Note: GitHub Projects V2 requires manual setup via web UI")
        print("  You can add issues to the project board using:")
        print(f"  gh project item-add <PROJECT_NUMBER> --owner {self.config.github_username} --url <ISSUE_URL>")
        print("\n  Issue status mapping:")

        for issue in issues:
            status = status_mapping.get(issue.number, 'Backlog')
            print(f"  - Issue #{issue.number}: {status}")

        # Return None as V2 projects require GraphQL API
        # Users should use gh CLI or web UI to create and manage projects
        return None

    def print_summary(self, repo, issues: List[object], prs: List[object]) -> None:
        """Print summary of created resources.

        Args:
            repo: Repository object
            issues: List of created issues
            prs: List of created PRs
        """
        print("\n" + "="*60)
        print("Setup Complete!")
        print("="*60)

        print(f"\n✓ Repository: {repo.html_url}")
        print(f"✓ Issues created: {len(issues)}")
        print(f"✓ Pull requests created: {len(prs)}")

        print("\n📋 Next steps:")
        print("1. Create a GitHub Project board via web UI or gh CLI:")
        print(f"   gh project create --owner {self.config.github_username} --title \"{self.config.project_name}\"")
        print("\n2. Add issues to the project:")
        for issue in issues:
            print(f"   gh project item-add <PROJECT_NUM> --owner {self.config.github_username} --url {issue.html_url}")

        print("\n3. Organize issues into columns:")
        print("   - Backlog: Issues #4, #5, #8")
        print("   - In Progress: Issues #1, #3")
        print("   - In Review: Issues #2, #6")
        print("   - Done: Issue #7")

        print("\n🎯 MCP Demo Queries:")
        print('   - "What commits were made today? Create a summary in Notion."')
        print('   - "Which issues moved to \'In Review\' today? Send update to Slack."')
        print('   - "Give me a weekly summary of what the team completed this week."')
