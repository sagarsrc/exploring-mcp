"""
GitHub MCP Server - Main entry point.

FastMCP server providing GitHub integration tools.
Enables natural language issue management and repository operations.
"""

import os
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server.config import Config
from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.tools.github_tools import create_github_tools


def create_server() -> FastMCP:
    """
    Create and configure the GitHub MCP server.

    Returns:
        Configured FastMCP server instance
    """
    # Validate configuration
    Config.validate()

    # Initialize GitHub API client
    github_client = GitHubAPIClient(
        token=Config.GITHUB_TOKEN,
        repo_owner=Config.GITHUB_USERNAME,
        repo_name=Config.REPO_NAME,
    )

    # Create main MCP server
    mcp = FastMCP(Config.SERVER_NAME, version=Config.SERVER_VERSION)

    # Create and mount GitHub tools
    github_mcp = create_github_tools(github_client)
    mcp.mount(github_mcp, prefix="github")

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        """Health check for monitoring and load balancers."""
        github_healthy = github_client.health_check()

        return JSONResponse(
            {
                "status": "healthy" if github_healthy else "unhealthy",
                "service": Config.SERVER_NAME,
                "version": Config.SERVER_VERSION,
                "repository": Config.get_full_repo_name(),
                "github_api": "connected" if github_healthy else "disconnected",
            }
        )

    # Root endpoint
    @mcp.custom_route("/", methods=["GET"])
    async def root(request):
        """Root endpoint showing server info."""
        return JSONResponse(
            {
                "service": Config.SERVER_NAME,
                "version": Config.SERVER_VERSION,
                "repository": Config.get_full_repo_name(),
                "status": "ok",
            }
        )

    return mcp


# Create server instance
mcp = create_server()


if __name__ == "__main__":
    """Run the MCP server via HTTP using uvicorn."""
    import uvicorn

    print(f"Starting {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
    print(f"Repository: {Config.get_full_repo_name()}")
    print("-" * 60)

    # Get ASGI app
    app = mcp.http_app()

    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    print(f"Server starting on http://{host}:{port}")
    print(f"MCP endpoint: http://{host}:{port}/mcp")
    print(f"Health check: http://{host}:{port}/health")
    print(f"Root endpoint: http://{host}:{port}/")
    print("-" * 60)

    # Run with uvicorn using wsproto to avoid websockets deprecation warnings
    uvicorn.run(
        app,
        host=host,
        port=port,
    )
