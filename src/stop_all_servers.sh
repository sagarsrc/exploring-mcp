#!/bin/bash
#
# Stop All MCP Servers
#
# This script stops all running MCP servers (GitHub, Notion, Slack).
#
# Usage:
#   ./stop_all_servers.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log directory and PID file
LOG_DIR="logs"
PID_FILE="$LOG_DIR/mcp_servers.pid"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Stopping All MCP Servers${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if PID file exists
if [ ! -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  No PID file found at $PID_FILE${NC}"
    echo -e "${YELLOW}Attempting to find and kill MCP server processes...${NC}"
    echo ""

    # Try to find and kill processes by name
    PIDS=$(pgrep -f "mcp_server_" || true)
    if [ -z "$PIDS" ]; then
        echo -e "${GREEN}✅ No MCP server processes found${NC}"
        exit 0
    else
        echo -e "${YELLOW}Found MCP server processes: $PIDS${NC}"
        echo "$PIDS" | xargs kill 2>/dev/null || true
        sleep 2
        echo -e "${GREEN}✅ Killed MCP server processes${NC}"
        exit 0
    fi
fi

# Read PIDs from file
echo -e "${YELLOW}Reading PIDs from $PID_FILE...${NC}"
source "$PID_FILE"

# Function to kill a process and check if it's dead
kill_process() {
    local name=$1
    local pid=$2

    if [ -z "$pid" ]; then
        echo -e "${YELLOW}⚠️  No PID found for $name${NC}"
        return
    fi

    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  $name (PID: $pid) is not running${NC}"
        return
    fi

    echo -e "${BLUE}🛑 Stopping $name (PID: $pid)...${NC}"
    kill "$pid" 2>/dev/null || true

    # Wait up to 5 seconds for graceful shutdown
    for i in {1..5}; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}✅ $name stopped${NC}"
            return
        fi
        sleep 1
    done

    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${RED}⚠️  Force killing $name...${NC}"
        kill -9 "$pid" 2>/dev/null || true
        echo -e "${GREEN}✅ $name force stopped${NC}"
    fi
}

# Stop all servers
kill_process "GitHub MCP Server" "$GITHUB_PID"
kill_process "Notion MCP Server" "$NOTION_PID"
kill_process "Slack MCP Server" "$SLACK_PID"

# Also kill any tail processes that might be hanging around
pkill -f "tail -f.*mcp.log" 2>/dev/null || true

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✅ All MCP Servers Stopped!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Remove PID file
rm -f "$PID_FILE"
echo -e "${GREEN}Removed PID file${NC}"
echo ""
