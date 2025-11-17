"""Pull requests manager for creating and managing GitHub PRs."""

from typing import List
from datagen.github_client import GitHubClient
from datagen.config import Config


class PRsManager:
    """Manager for creating and organizing GitHub pull requests."""

    def __init__(self, client: GitHubClient, config: Config):
        """Initialize PRs manager.

        Args:
            client: GitHub client instance
            config: Configuration instance
        """
        self.client = client
        self.config = config

    def create_all_prs(self, repo) -> List[object]:
        """Create all pull requests as defined in the instructions.

        Args:
            repo: Repository object

        Returns:
            List of created PR objects
        """
        print("\n" + "="*60)
        print("Creating Pull Requests")
        print("="*60)

        default_branch = self.client.get_default_branch(repo)
        created_prs = []

        # PR 1: Streaming support
        try:
            pr1 = self._create_streaming_pr(repo, default_branch)
            if pr1:
                created_prs.append(pr1)
        except Exception as e:
            print(f"Error creating streaming PR: {e}")

        # PR 2: Chat history fix
        try:
            pr2 = self._create_chat_history_pr(repo, default_branch)
            if pr2:
                created_prs.append(pr2)
        except Exception as e:
            print(f"Error creating chat history PR: {e}")

        print(f"\n✓ Created {len(created_prs)} pull requests")
        return created_prs

    def _create_streaming_pr(self, repo, base_branch: str) -> object:
        """Create PR for streaming support feature.

        Args:
            repo: Repository object
            base_branch: Base branch name

        Returns:
            PullRequest object
        """
        branch_name = 'feat/streaming-support'

        # Create branch
        self.client.create_branch(repo, branch_name, base_branch)

        # Create file in branch
        file_content = '''from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import anthropic

async def stream_response(prompt: str):
    """Stream LLM responses using SSE"""
    client = anthropic.Anthropic()

    with client.messages.stream(
        model="claude-3-5-sonnet-20241022",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield f"data: {text}\\n\\n"
'''

        commit_message = """feat(ai): Add SSE streaming for LLM responses

- New /stream endpoint using Server-Sent Events
- Frontend React hook to handle streaming
- Tested with Claude API

Closes #1"""

        self.client.create_file(
            repo=repo,
            path='ai-service/streaming.py',
            content=file_content,
            message=commit_message,
            branch=branch_name
        )

        # Create PR
        pr_body = """## Changes
- New `/stream` endpoint using Server-Sent Events
- Frontend React hook to handle streaming
- Tested with Claude API

## Testing
- [x] Works in local development
- [ ] Needs testing in production
- [ ] Performance testing pending

## Review needed from
- Backend team: API endpoint design
- Frontend team: React integration

Closes #1"""

        pr = self.client.create_pull_request(
            repo=repo,
            title='feat(ai): Add SSE streaming for LLM responses',
            body=pr_body,
            head=branch_name,
            base=base_branch,
            draft=True,
            labels=['feature', 'team-ai']
        )

        return pr

    def _create_chat_history_pr(self, repo, base_branch: str) -> object:
        """Create PR for chat history persistence fix.

        Args:
            repo: Repository object
            base_branch: Base branch name

        Returns:
            PullRequest object
        """
        branch_name = 'fix/chat-history-persistence'

        # Create branch
        self.client.create_branch(repo, branch_name, base_branch)

        # Create file in branch
        file_content = """import { useEffect, useState } from 'react';

export function useChatHistory() {
  const [messages, setMessages] = useState([]);

  // Load from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('chat-history');
    if (saved) {
      setMessages(JSON.parse(saved));
    }
  }, []);

  // Save to localStorage whenever messages change
  useEffect(() => {
    localStorage.setItem('chat-history', JSON.stringify(messages));
  }, [messages]);

  return [messages, setMessages];
}
"""

        commit_message = """fix(frontend): Persist chat history in localStorage

- Save messages to localStorage on send
- Load from localStorage on component mount
- Clear history on logout

Closes #2"""

        self.client.create_file(
            repo=repo,
            path='frontend/src/useChatHistory.js',
            content=file_content,
            message=commit_message,
            branch=branch_name
        )

        # Create PR
        pr_body = f"""## Changes
- Save messages to localStorage on send
- Load from localStorage on component mount
- Clear history on logout

## Testing
- [x] Tested in Chrome, Firefox, Safari
- [x] Works across page refreshes
- [x] Handles large chat histories (100+ messages)

## Review needed from
- @{self.config.get_username('Sagar')} for approval

Closes #2"""

        pr = self.client.create_pull_request(
            repo=repo,
            title='fix(frontend): Persist chat history in localStorage',
            body=pr_body,
            head=branch_name,
            base=base_branch,
            draft=False,
            labels=['bug', 'team-frontend']
        )

        return pr
