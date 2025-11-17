"""GitHub API client wrapper using PyGithub."""

from github import Github, GithubException
from typing import Dict, List, Optional
import time


class GitHubClient:
    """Wrapper for GitHub API operations."""

    def __init__(self, token: str, username: str):
        """Initialize GitHub client.

        Args:
            token: GitHub personal access token
            username: GitHub username
        """
        self.token = token
        self.username = username
        self.client = Github(token)
        self.user = self.client.get_user(username)

    def create_label(self, repo, name: str, color: str, description: str) -> bool:
        """Create a label in the repository.

        Args:
            repo: Repository object
            name: Label name
            color: Label color (hex without #)
            description: Label description

        Returns:
            True if created successfully, False if already exists
        """
        try:
            repo.create_label(name=name, color=color, description=description)
            print(f"✓ Created label: {name}")
            return True
        except GithubException as e:
            if e.status == 422:  # Label already exists
                print(f"⚠ Label already exists: {name}")
                return False
            raise

    def create_labels(self, repo, labels: Dict[str, Dict[str, str]]):
        """Create multiple labels in the repository.

        Args:
            repo: Repository object
            labels: Dict of label configs {name: {color, description}}
        """
        print("\nCreating labels...")
        for name, config in labels.items():
            self.create_label(repo, name, config['color'], config['description'])
            time.sleep(0.1)  # Rate limiting

    def get_or_create_repo(self, name: str, description: str = "",
                           private: bool = False):
        """Get existing repo or create new one.

        Args:
            name: Repository name
            description: Repository description
            private: Whether repo should be private

        Returns:
            Repository object
        """
        try:
            repo = self.user.get_repo(name)
            print(f"✓ Repository '{name}' already exists")
            return repo
        except GithubException as e:
            if e.status == 404:
                print(f"Creating repository '{name}'...")
                repo = self.user.create_repo(
                    name=name,
                    description=description,
                    private=private,
                    auto_init=True
                )
                print(f"✓ Created repository: {name}")
                # Wait for repo to be ready
                time.sleep(2)
                return repo
            raise

    def create_issue(self, repo, title: str, body: str,
                    labels: List[str] = None,
                    assignee: str = None) -> object:
        """Create an issue in the repository.

        Args:
            repo: Repository object
            title: Issue title
            body: Issue body
            labels: List of label names
            assignee: GitHub username to assign

        Returns:
            Issue object
        """
        kwargs = {
            'title': title,
            'body': body,
        }

        if labels:
            kwargs['labels'] = labels

        if assignee:
            kwargs['assignee'] = assignee

        try:
            issue = repo.create_issue(**kwargs)
            print(f"✓ Created issue #{issue.number}: {title}")
            time.sleep(0.5)  # Rate limiting
            return issue
        except GithubException as e:
            # If assignment fails, try without assignee
            if e.status == 422 and assignee and 'assignee' in str(e):
                print(f"⚠ User {assignee} cannot be assigned, creating without assignee")
                kwargs.pop('assignee', None)
                try:
                    issue = repo.create_issue(**kwargs)
                    print(f"✓ Created issue #{issue.number}: {title}")
                    time.sleep(0.5)
                    return issue
                except GithubException as e2:
                    print(f"✗ Failed to create issue '{title}': {e2}")
                    raise
            print(f"✗ Failed to create issue '{title}': {e}")
            raise

    def close_issue(self, issue) -> None:
        """Close an issue.

        Args:
            issue: Issue object
        """
        issue.edit(state='closed')
        print(f"✓ Closed issue #{issue.number}")

    def create_branch(self, repo, branch_name: str,
                     from_branch: str = 'main') -> object:
        """Create a new branch from an existing branch.

        Args:
            repo: Repository object
            branch_name: Name of new branch
            from_branch: Source branch name

        Returns:
            Git reference object
        """
        try:
            # Try 'main' first, fallback to 'master'
            try:
                source = repo.get_branch(from_branch)
            except GithubException:
                source = repo.get_branch('master')

            ref = repo.create_git_ref(
                ref=f'refs/heads/{branch_name}',
                sha=source.commit.sha
            )
            print(f"✓ Created branch: {branch_name}")
            time.sleep(0.5)
            return ref
        except GithubException as e:
            if e.status == 422:  # Branch already exists
                print(f"⚠ Branch already exists: {branch_name}")
                return repo.get_git_ref(f'heads/{branch_name}')
            raise

    def create_file(self, repo, path: str, content: str,
                   message: str, branch: str = 'main') -> None:
        """Create or update a file in the repository.

        Args:
            repo: Repository object
            path: File path in repo
            content: File content
            message: Commit message
            branch: Branch name
        """
        try:
            # Try to get existing file
            try:
                contents = repo.get_contents(path, ref=branch)
                repo.update_file(
                    path=path,
                    message=message,
                    content=content,
                    sha=contents.sha,
                    branch=branch
                )
                print(f"✓ Updated file: {path}")
            except GithubException:
                # File doesn't exist, create it
                repo.create_file(
                    path=path,
                    message=message,
                    content=content,
                    branch=branch
                )
                print(f"✓ Created file: {path}")

            time.sleep(0.5)
        except GithubException as e:
            print(f"✗ Failed to create/update file '{path}': {e}")
            raise

    def create_pull_request(self, repo, title: str, body: str,
                           head: str, base: str = 'main',
                           draft: bool = False,
                           labels: List[str] = None) -> object:
        """Create a pull request.

        Args:
            repo: Repository object
            title: PR title
            body: PR body
            head: Branch to merge from
            base: Branch to merge to
            draft: Whether PR is a draft
            labels: List of label names

        Returns:
            PullRequest object
        """
        try:
            # Try main first, fallback to master
            try:
                repo.get_branch(base)
            except GithubException:
                base = 'master'

            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )

            if labels:
                pr.set_labels(*labels)

            print(f"✓ Created PR #{pr.number}: {title}")
            time.sleep(0.5)
            return pr
        except GithubException as e:
            print(f"✗ Failed to create PR '{title}': {e}")
            raise

    def get_default_branch(self, repo) -> str:
        """Get the default branch name for a repository.

        Args:
            repo: Repository object

        Returns:
            Default branch name (e.g., 'main' or 'master')
        """
        return repo.default_branch

    def cleanup_repository(self, repo) -> None:
        """Clean up all issues, PRs, and branches (except default) in repository.

        Args:
            repo: Repository object
        """
        default_branch = self.get_default_branch(repo)

        # Close and delete all pull requests
        print("\nClosing pull requests...")
        prs = list(repo.get_pulls(state='all'))
        for pr in prs:
            try:
                if pr.state == 'open':
                    pr.edit(state='closed')
                print(f"✓ Closed PR #{pr.number}: {pr.title}")
            except GithubException as e:
                print(f"⚠ Could not close PR #{pr.number}: {e}")
            time.sleep(0.2)

        # Close all issues (open and closed)
        print("\nClosing issues...")
        issues = list(repo.get_issues(state='all'))
        for issue in issues:
            # Skip pull requests (they show up in issues too)
            if issue.pull_request:
                continue
            try:
                if issue.state == 'open':
                    issue.edit(state='closed')
                print(f"✓ Closed issue #{issue.number}: {issue.title}")
            except GithubException as e:
                print(f"⚠ Could not close issue #{issue.number}: {e}")
            time.sleep(0.2)

        # Delete all branches except default
        print("\nDeleting branches...")
        branches = list(repo.get_branches())
        for branch in branches:
            if branch.name != default_branch:
                try:
                    ref = repo.get_git_ref(f'heads/{branch.name}')
                    ref.delete()
                    print(f"✓ Deleted branch: {branch.name}")
                    time.sleep(0.2)
                except GithubException as e:
                    print(f"⚠ Could not delete branch {branch.name}: {e}")

        print("\n✓ Repository cleaned up")
