"""
Multi-Service MCP Server - Main entry point.

FastMCP server providing GitHub, Notion, and Slack integration tools.
Enables natural language issue management, repository operations,
Notion workspace management, and Slack notifications.
"""

import os
import logging
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server.config import Config
from mcp_server.api_clients.github_client import GitHubAPIClient
from mcp_server.api_clients.notion_client import NotionAPIClient
from mcp_server.api_clients.slack_client import SlackAPIClient
from mcp_server.tools.github_tools import create_github_tools
from mcp_server.tools.notion_tools import create_notion_tools
from mcp_server.tools.slack_tools import create_slack_tools
from mcp_server.middleware.logging import LoggingMiddleware

# Configure root logger for server
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def create_server() -> FastMCP:
    """
    Create and configure the multi-service MCP server.

    Returns:
        Configured FastMCP server instance
    """
    # Validate configuration
    logger.info("Validating configuration...")
    Config.validate()
    logger.info("Configuration validated successfully")

    # Initialize API clients
    logger.info("Initializing API clients...")
    github_client = GitHubAPIClient(
        token=Config.GITHUB_TOKEN,
        repo_owner=Config.GITHUB_USERNAME,
        repo_name=Config.REPO_NAME,
    )
    logger.info(f"GitHub client initialized for {Config.get_full_repo_name()}")

    notion_client = NotionAPIClient(token=Config.NOTION_TOKEN)
    logger.info("Notion client initialized")

    slack_client = SlackAPIClient(token=Config.SLACK_TOKEN)
    logger.info("Slack client initialized")

    # Create main MCP server
    mcp = FastMCP(Config.SERVER_NAME, version=Config.SERVER_VERSION)
    logger.info(f"Created MCP server: {Config.SERVER_NAME} v{Config.SERVER_VERSION}")

    # Add logging middleware
    mcp.add_middleware(LoggingMiddleware())
    logger.info("Logging middleware enabled")

    # Mount GitHub tools
    github_mcp = create_github_tools(github_client)
    mcp.mount(github_mcp, prefix="github")
    logger.info("GitHub tools mounted")

    # Mount Notion tools
    notion_mcp = create_notion_tools(notion_client)
    mcp.mount(notion_mcp, prefix="notion")
    logger.info("Notion tools mounted")

    # Mount Slack tools
    slack_mcp = create_slack_tools(slack_client)
    mcp.mount(slack_mcp, prefix="slack")
    logger.info("Slack tools mounted")

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        """Health check for monitoring and load balancers."""
        github_healthy = github_client.health_check()
        notion_healthy = notion_client.health_check()
        slack_healthy = slack_client.health_check()

        return JSONResponse(
            {
                "status": (
                    "healthy"
                    if (github_healthy and notion_healthy and slack_healthy)
                    else "unhealthy"
                ),
                "service": Config.SERVER_NAME,
                "version": Config.SERVER_VERSION,
                "repository": Config.get_full_repo_name(),
                "github_api": "connected" if github_healthy else "disconnected",
                "notion_api": "connected" if notion_healthy else "disconnected",
                "slack_api": "connected" if slack_healthy else "disconnected",
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

    logger.info("=" * 60)
    logger.info(f"Starting {Config.SERVER_NAME} v{Config.SERVER_VERSION}")
    logger.info(f"Repository: {Config.get_full_repo_name()}")
    logger.info("=" * 60)

    # Get ASGI app
    app = mcp.http_app()

    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))

    logger.info(f"Server binding to http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Root endpoint: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("Server ready to accept connections")

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
