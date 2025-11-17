#!/usr/bin/env python3
"""
GitHub Project Setup Automation

This script automates the creation of a GitHub project with:
- Repository setup
- Labels
- Issues with assignments
- Pull requests
- Project board structure

Based on: src/datagen/INSTRUCTIONS.md
"""

import sys

from datagen.config import Config, LABELS
from datagen.github_client import GitHubClient
from datagen.project_manager import ProjectManager
from datagen.issues_manager import IssuesManager
from datagen.prs_manager import PRsManager


def main():
    """Main orchestrator for GitHub project setup."""
    print("=" * 60)
    print("GitHub Project Setup Automation")
    print("=" * 60)

    # Load configuration
    print("\n[1/6] Loading configuration...")
    try:
        config = Config()
        print("✓ Configuration loaded")
        print(f"  Repository: {config.repo_name}")
        print(f"  Team members: {len(config.get_all_members())}")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nMake sure your .env file contains:")
        print("  - GITHUB_TOKEN")
        print("  - GITHUB_USERNAME")
        print("  - REPO_NAME")
        print("  - TEAM_* variables")
        return 1

    # Initialize GitHub client
    print("\n[2/6] Connecting to GitHub...")
    try:
        client = GitHubClient(config.github_token, config.github_username)
        print(f"✓ Connected as {config.github_username}")
    except Exception as e:
        print(f"✗ Failed to connect to GitHub: {e}")
        return 1

    # Initialize managers
    project_manager = ProjectManager(client, config)
    issues_manager = IssuesManager(client, config)
    prs_manager = PRsManager(client, config)

    # Setup repository
    print("\n[3/6] Setting up repository...")
    try:
        repo = project_manager.setup_repository(LABELS)
    except Exception as e:
        print(f"✗ Failed to setup repository: {e}")
        return 1

    # Cleanup existing resources
    print("\n[4/6] Checking for existing issues/PRs...")
    try:
        # Check if there are existing issues or PRs
        existing_issues = list(repo.get_issues(state="open"))
        existing_prs = list(repo.get_pulls(state="open"))

        if existing_issues or existing_prs:
            print(
                f"⚠ Found {len(existing_issues)} open issues and {len(existing_prs)} open PRs"
            )
            response = input(
                "Do you want to clean up (close all issues/PRs and delete branches)? [y/N]: "
            )

            if response.lower() in ["y", "yes"]:
                print("\n🧹 Cleaning up repository...")
                client.cleanup_repository(repo)
            else:
                print("⚠ Skipping cleanup - this may result in duplicates")
        else:
            print("✓ No cleanup needed")
    except Exception as e:
        print(f"⚠ Cleanup check failed: {e}")
        # Continue anyway

    # Create issues
    print("\n[5/6] Creating issues...")
    try:
        issues = issues_manager.create_all_issues(repo)
        status_mapping = issues_manager.get_issue_status_mapping()
    except Exception as e:
        print(f"✗ Failed to create issues: {e}")
        return 1

    # Create pull requests
    print("\n[6/6] Creating pull requests...")
    try:
        prs = prs_manager.create_all_prs(repo)
    except Exception as e:
        print(f"✗ Failed to create pull requests: {e}")
        return 1

    # Create project board (informational only)
    project_manager.create_project_board(repo, issues, status_mapping)

    # Print summary
    project_manager.print_summary(repo, issues, prs)

    return 0


if __name__ == "__main__":
    sys.exit(main())
