"""
Custom logging middleware for MCP server
"""

import logging
from datetime import datetime
from fastmcp.server.middleware import Middleware, MiddlewareContext

# Configure logger
logger = logging.getLogger("workspace.mcp")
logger.setLevel(logging.INFO)

# Add console handler if not already present
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


class LoggingMiddleware(Middleware):
    """
    Logging middleware for workspace MCP server

    Logs all tool calls, their arguments, execution time, and results/errors.
    Focuses on operation-level logging rather than message-level logging.
    """

    async def on_call_tool(self, context: MiddlewareContext, call_next):
        """Log tool execution with timing and results"""
        tool_name = context.message.name
        arguments = context.message.arguments

        # Log tool invocation (hide sensitive data)
        safe_args = self._sanitize_args(arguments)
        logger.info(f"[TOOL CALL] {tool_name} - Arguments: {safe_args}")

        start_time = datetime.now()

        try:
            result = await call_next(context)

            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"[TOOL SUCCESS] {tool_name} - Completed in {execution_time:.2f}s"
            )

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.error(
                f"[TOOL ERROR] {tool_name} - "
                f"Failed after {execution_time:.2f}s - "
                f"Error: {type(e).__name__}: {str(e)}"
            )
            raise

    async def on_list_tools(self, context: MiddlewareContext, call_next):
        """Log tool listing requests"""
        logger.info("[LIST TOOLS] Client requested available tools")

        try:
            result = await call_next(context)
            tool_count = len(result) if result else 0
            logger.info(f"[LIST TOOLS] Returned {tool_count} tools")
            return result

        except Exception as e:
            logger.error(f"[LIST TOOLS ERROR] {type(e).__name__}: {str(e)}")
            raise

    def _sanitize_args(self, arguments: dict) -> dict:
        """
        Remove or mask sensitive information from arguments

        Args:
            arguments: Tool arguments dictionary

        Returns:
            Sanitized arguments safe for logging
        """
        if not arguments:
            return {}

        # Create a copy to avoid modifying original
        safe_args = arguments.copy()

        # List of sensitive keys to mask
        sensitive_keys = [
            "password",
            "token",
            "api_key",
            "secret",
            "authorization",
            "auth",
        ]

        for key in safe_args:
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_args[key] = "***REDACTED***"

        return safe_args
