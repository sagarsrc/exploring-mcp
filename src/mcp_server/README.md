# GitHub MCP Server

FastMCP-based server providing GitHub integration tools for natural language issue management.

## Architecture

```
mcp_server/
├── config.py              # Server configuration
├── server.py              # Main server entry point
├── api_clients/           # API client layer
│   ├── base_client.py     # Abstract HTTP client base
│   └── github_client.py   # GitHub API client (PyGithub)
├── schemas/               # Pydantic data models
│   └── github_schemas.py  # GitHub API schemas
├── tools/                 # MCP tool definitions
│   └── github_tools.py    # GitHub MCP tools
└── middleware/            # Middleware (future)
```

## Available Tools

### Issue Management
- `list_issues` - List issues with filters (assignee, labels, state)
- `get_issue` - Get detailed issue information
- `update_issue_status` - Open or close an issue
- `add_issue_comment` - Add a comment to an issue
- `get_issue_comments` - Get all comments on an issue

### Repository Operations
- `get_repository_info` - Get repository metadata
- `list_labels` - List all repository labels

### Commit Operations
- `list_commits` - List recent commits with filters

## Setup

### Environment Variables

Export the following environment variables before running:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
export GITHUB_USERNAME="your_username"
export REPO_NAME="your_repo"
```

### Installation

Install dependencies using uv:

```bash
uv pip install fastmcp pygithub python-dotenv pydantic httpx
```

## Running the Server

```bash
# From project root
python -m mcp_server.server
```

Or using the installed package:

```bash
# If installed with uv
python src/mcp_server/server.py
```

## Usage Example

The server exposes tools via the MCP protocol. Example interactions:

**List open issues:**
```
Tool: github/list_issues
Args: {"state": "open"}
```

**Get specific issue:**
```
Tool: github/get_issue
Args: {"issue_number": 1}
```

**Add comment:**
```
Tool: github/add_issue_comment
Args: {
  "issue_number": 1,
  "comment": "Working on this now"
}
```

**Close issue:**
```
Tool: github/update_issue_status
Args: {
  "issue_number": 1,
  "new_state": "closed"
}
```

## Health Check

The server provides a health check resource:

```
Resource: health://status
```

Returns server status and GitHub API connectivity.

## Design Principles

1. **Separation of Concerns**: API clients, schemas, and tools are separate
2. **Type Safety**: Pydantic models for all data structures
3. **Clean Configuration**: Environment-based config without hardcoded paths
4. **Extensibility**: Easy to add Notion, Slack, and workflow tools later
5. **Error Handling**: Graceful handling of missing issues and API errors

## Next Steps

Phase 2 will add:
- Notion integration tools
- Slack integration tools
- Composite workflow tools (e.g., create_issue_with_notifications)
- Advanced filtering and search
- Batch operations
