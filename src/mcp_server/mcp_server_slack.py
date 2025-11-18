"""
Slack MCP Server - Standalone server for Slack integration tools.

FastMCP server providing Slack-specific tools for channel management,
message posting, and workspace operations.
"""

import os
import logging
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server.config import Config
from mcp_server.api_clients.slack_client import SlackAPIClient
from mcp_server.tools.slack_tools import create_slack_tools
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
    Create and configure the Slack MCP server.

    Returns:
        Configured FastMCP server instance
    """
    # Validate configuration
    logger.info("Validating Slack configuration...")
    if not Config.SLACK_TOKEN:
        raise ValueError("SLACK_TOKEN is required")
    logger.info("Slack configuration validated successfully")

    # Initialize Slack API client
    logger.info("Initializing Slack API client...")
    slack_client = SlackAPIClient(token=Config.SLACK_TOKEN)
    logger.info("Slack client initialized")

    # Create MCP server
    mcp = create_slack_tools(slack_client)
    logger.info("Slack MCP server created")

    # Add logging middleware
    mcp.add_middleware(LoggingMiddleware())
    logger.info("Logging middleware enabled")

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        """Health check for monitoring and load balancers."""
        slack_healthy = slack_client.health_check()

        return JSONResponse(
            {
                "status": "healthy" if slack_healthy else "unhealthy",
                "service": "Slack MCP Server",
                "version": Config.SERVER_VERSION,
                "slack_api": "connected" if slack_healthy else "disconnected",
            }
        )

    # Root endpoint
    @mcp.custom_route("/", methods=["GET"])
    async def root(request):
        """Root endpoint showing server info."""
        return JSONResponse(
            {
                "service": "Slack MCP Server",
                "version": Config.SERVER_VERSION,
                "status": "ok",
                "tools": "available",
            }
        )

    return mcp


# Create server instance
mcp = create_server()


if __name__ == "__main__":
    """Run the Slack MCP server via HTTP using uvicorn."""
    import uvicorn

    logger.info("=" * 60)
    logger.info("Starting Slack MCP Server")
    logger.info("=" * 60)

    # Get ASGI app
    app = mcp.http_app()

    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("SLACK_MCP_PORT", "8003"))

    logger.info(f"Server binding to http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Root endpoint: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("Slack MCP Server ready to accept connections")

    # Run with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
    )
