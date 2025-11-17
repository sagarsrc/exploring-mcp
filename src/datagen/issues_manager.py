"""Issues manager for creating and managing GitHub issues."""

from typing import Dict, List, Optional
from datagen.github_client import GitHubClient
from datagen.config import Config


class IssuesManager:
    """Manager for creating and organizing GitHub issues."""

    def __init__(self, client: GitHubClient, config: Config):
        """Initialize issues manager.

        Args:
            client: GitHub client instance
            config: Configuration instance
        """
        self.client = client
        self.config = config

    def create_all_issues(self, repo) -> List[object]:
        """Create all issues as defined in the instructions.

        Args:
            repo: Repository object

        Returns:
            List of created issue objects
        """
        print("\n" + "=" * 60)
        print("Creating Issues")
        print("=" * 60)

        issues_data = self._get_issues_data()
        created_issues = []

        for issue_data in issues_data:
            try:
                issue = self.client.create_issue(
                    repo=repo,
                    title=issue_data["title"],
                    body=issue_data["body"],
                    labels=issue_data.get("labels", []),
                    assignee=issue_data.get("assignee"),
                )
                created_issues.append(issue)

                # Close issue if marked as done
                if issue_data.get("close", False):
                    self.client.close_issue(issue)

            except Exception as e:
                print(f"Error creating issue '{issue_data['title']}': {e}")
                continue

        print(f"\n✓ Created {len(created_issues)} issues")
        return created_issues

    def _get_issues_data(self) -> List[Dict]:
        """Get all issues data to create.

        Returns:
            List of issue configuration dicts
        """
        return [
            {
                "title": "Add streaming support for LLM responses",
                "labels": ["feature", "team-ai", "P1"],
                "assignee": self.config.get_username("Sagar"),
                "body": """## Description
Users want to see responses appear word-by-word instead of waiting for complete response.

## Tasks
- [ ] Implement SSE (Server-Sent Events) endpoint
- [ ] Update frontend to handle streaming
- [ ] Test with Anthropic API

## Effort: 5 points""",
            },
            {
                "title": "Fix chat history not loading on page refresh",
                "labels": ["bug", "team-frontend", "P1"],
                "assignee": self.config.get_username("Zeeshan"),
                "body": """## Description
When user refreshes page, chat history disappears. Should persist in localStorage.

## Tasks
- [x] Add localStorage save on new message
- [x] Load from localStorage on page load
- [ ] Add migration for existing users

## Effort: 3 points""",
            },
            {
                "title": "Add rate limiting to prevent abuse",
                "labels": ["feature", "team-backend", "P1"],
                "assignee": self.config.get_username("Swathi"),
                "body": """## Description
Need to prevent users from spamming the API and racking up LLM costs.

## Solution
- Use Redis for rate limit tracking
- 10 requests per minute per user
- Return 429 if limit exceeded

## Effort: 5 points""",
            },
            {
                "title": "Improve system prompt template",
                "labels": ["improvement", "team-ai", "P2"],
                "assignee": self.config.get_username("Sagar"),
                "body": """## Description
Current system prompt is generic. Need to make it more specific to our use case.

## Tasks
- [ ] Research best practices for chat prompts
- [ ] Test different templates
- [ ] A/B test with users

## Effort: 3 points""",
            },
            {
                "title": "Add dark mode toggle to UI",
                "labels": ["feature", "team-frontend", "P2"],
                "assignee": self.config.get_username("Zeeshan"),
                "body": """## Description
Users requesting dark mode for late-night usage.

## Tasks
- [ ] Design dark mode color scheme
- [ ] Implement theme toggle
- [ ] Persist preference in localStorage

## Effort: 3 points""",
            },
            {
                "title": "Deploy v1.0 to production",
                "labels": ["P0", "team-backend"],
                "assignee": self.config.get_username("Swathi"),
                "body": """## Description
First production deployment. Need to:
- [ ] Set up AWS infrastructure (ECS, RDS)
- [ ] Configure environment variables
- [ ] Set up monitoring (CloudWatch)
- [ ] Test with real users

## Effort: 8 points""",
            },
            {
                "title": "Add basic user authentication with Google OAuth",
                "labels": ["feature", "team-backend", "P1"],
                "assignee": self.config.get_username("Swathi"),
                "body": """## Description
Implemented Google OAuth for user login.

## What was done
- Added Google OAuth integration
- Created user database schema
- Added JWT token generation
- Updated frontend login flow

## Effort: 8 points""",
                "close": True,  # This issue should be closed immediately
            },
            {
                "title": "Allow users to export chat history as PDF",
                "labels": ["feature", "team-frontend", "P2"],
                "assignee": self.config.get_username("Zeeshan"),
                "body": """## Description
Users want to save/share their conversations.

## Tasks
- [ ] Add 'Export' button to UI
- [ ] Generate PDF using jsPDF
- [ ] Include timestamps and formatting

## Effort: 5 points""",
            },
        ]

    def get_issue_status_mapping(self) -> Dict[int, str]:
        """Get mapping of issue numbers to project board status.

        Returns:
            Dict mapping issue number to status column
        """
        # Based on the instructions:
        # Backlog: #4, #5, #8
        # In Progress: #1, #3
        # In Review: #2, #6
        # Done: #7
        return {
            1: "In Progress",
            2: "In Review",
            3: "In Progress",
            4: "Backlog",
            5: "Backlog",
            6: "In Review",
            7: "Done",
            8: "Backlog",
        }
