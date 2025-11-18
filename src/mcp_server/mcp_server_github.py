"""
GitHub MCP Server - Standalone server for GitHub integration tools.

FastMCP server providing GitHub-specific tools for issue management,
repository operations, and GitHub Projects v2 integration.
"""

import os
import logging
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server.config import Config
from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.tools.github_tools import create_github_tools
from mcp_server.middleware.logging import LoggingMiddleware

# Configure root logger for server
# Only configure if not already configured
if not logging.root.handlers:
        logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        )
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """
    Create and configure the GitHub MCP server.

    Returns:
        Configured FastMCP server instance
    """
    # Validate configuration
    logger.info("Validating GitHub configuration...")
    if not Config.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN is required")
    if not Config.GITHUB_USERNAME:
        raise ValueError("GITHUB_USERNAME is required")
    if not Config.REPO_NAME:
        raise ValueError("REPO_NAME is required")
    logger.info("GitHub configuration validated successfully")

    # Initialize GitHub API client
    logger.info("Initializing GitHub API client...")
    github_client = GitHubAPIClient(
        token=Config.GITHUB_TOKEN,
        repo_owner=Config.GITHUB_USERNAME,
        repo_name=Config.REPO_NAME,
    )
    logger.info(f"GitHub client initialized for {Config.get_full_repo_name()}")

    # Create MCP server
    mcp = create_github_tools(github_client)
    logger.info("GitHub MCP server created")

    # Add logging middleware
    mcp.add_middleware(LoggingMiddleware())
    logger.info("Logging middleware enabled")

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        """Health check for monitoring and load balancers."""
        github_healthy = github_client.health_check()

        return JSONResponse(
            {
                "status": "healthy" if github_healthy else "unhealthy",
                "service": "GitHub MCP Server",
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
                "service": "GitHub MCP Server",
                "version": Config.SERVER_VERSION,
                "repository": Config.get_full_repo_name(),
                "status": "ok",
                "tools": "available",
            }
        )

    return mcp


# Create server instance
mcp = create_server()


if __name__ == "__main__":
    """Run the GitHub MCP server via HTTP using uvicorn."""
    import uvicorn

    logger.info("=" * 60)
    logger.info("Starting GitHub MCP Server")
    logger.info(f"Repository: {Config.get_full_repo_name()}")
    logger.info("=" * 60)

    # Get ASGI app
    app = mcp.http_app()

    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("GITHUB_MCP_PORT", "8001"))

    logger.info(f"Server binding to http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Root endpoint: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("GitHub MCP Server ready to accept connections")

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
