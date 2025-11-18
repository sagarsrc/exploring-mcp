"""
Notion MCP Server - Standalone server for Notion integration tools.

FastMCP server providing Notion-specific tools for workspace management,
database operations, and page creation.
"""

import os
import logging
from fastmcp import FastMCP
from starlette.responses import JSONResponse

from mcp_server.config import Config
from mcp_server.api_clients.notion_client import NotionAPIClient
from mcp_server.tools.notion_tools import create_notion_tools
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
    Create and configure the Notion MCP server.

    Returns:
        Configured FastMCP server instance
    """
    # Validate configuration
    logger.info("Validating Notion configuration...")
    if not Config.NOTION_TOKEN:
        raise ValueError("NOTION_TOKEN is required")
    logger.info("Notion configuration validated successfully")

    # Initialize Notion API client
    logger.info("Initializing Notion API client...")
    notion_client = NotionAPIClient(token=Config.NOTION_TOKEN)
    logger.info("Notion client initialized")

    # Create MCP server
    mcp = create_notion_tools(notion_client)
    logger.info("Notion MCP server created")

    # Add logging middleware
    mcp.add_middleware(LoggingMiddleware())
    logger.info("Logging middleware enabled")

    # Health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request):
        """Health check for monitoring and load balancers."""
        notion_healthy = notion_client.health_check()

        return JSONResponse(
            {
                "status": "healthy" if notion_healthy else "unhealthy",
                "service": "Notion MCP Server",
                "version": Config.SERVER_VERSION,
                "notion_api": "connected" if notion_healthy else "disconnected",
            }
        )

    # Root endpoint
    @mcp.custom_route("/", methods=["GET"])
    async def root(request):
        """Root endpoint showing server info."""
        return JSONResponse(
            {
                "service": "Notion MCP Server",
                "version": Config.SERVER_VERSION,
                "status": "ok",
                "tools": "available",
            }
        )

    return mcp


# Create server instance
mcp = create_server()


if __name__ == "__main__":
    """Run the Notion MCP server via HTTP using FastMCP's built-in server."""
    # Get host and port from environment or use defaults
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("NOTION_MCP_PORT", "8002"))

    logger.info("=" * 60)
    logger.info("Starting Notion MCP Server")
    logger.info(f"Server binding to http://{host}:{port}")
    logger.info(f"MCP endpoint: http://{host}:{port}/mcp")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"Root endpoint: http://{host}:{port}/")
    logger.info("=" * 60)
    logger.info("Notion MCP Server ready to accept connections")

    # Run with FastMCP's built-in HTTP server
    mcp.run(transport="http", host=host, port=port)
