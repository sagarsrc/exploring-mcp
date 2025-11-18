#!/bin/bash
#
# Start All MCP Servers
#
# This script starts all three MCP servers (GitHub, Notion, Slack) in the background
# and tails their logs to a single terminal for easy monitoring.
#
# Usage:
#   ./start_all_servers.sh
#
# To stop all servers:
#   ./stop_all_servers.sh
#   OR
#   Press Ctrl+C (this will stop log tailing but servers will keep running)
#   Then run: pkill -f "mcp_server_"

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Log directory
LOG_DIR="logs"
mkdir -p "$LOG_DIR"

# Log files
GITHUB_LOG="$LOG_DIR/github_mcp.log"
NOTION_LOG="$LOG_DIR/notion_mcp.log"
SLACK_LOG="$LOG_DIR/slack_mcp.log"
COMBINED_LOG="$LOG_DIR/combined_mcp.log"

# PID file to track running servers
PID_FILE="$LOG_DIR/mcp_servers.pid"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Starting All MCP Servers${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check if servers are already running
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}⚠️  Warning: MCP servers may already be running${NC}"
    echo -e "${YELLOW}Check $PID_FILE for PIDs${NC}"
    echo -e "${YELLOW}Run ./stop_all_servers.sh to stop them first${NC}"
    echo ""
    read -p "Continue anyway? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Clear old logs
> "$GITHUB_LOG"
> "$NOTION_LOG"
> "$SLACK_LOG"
> "$COMBINED_LOG"

# Clear old PID file
> "$PID_FILE"

# Start GitHub MCP Server
echo -e "${BLUE}🚀 Starting GitHub MCP Server (port 8001)...${NC}"
nohup python -m mcp_server.mcp_server_github > "$GITHUB_LOG" 2>&1 &
GITHUB_PID=$!
echo "GITHUB_PID=$GITHUB_PID" >> "$PID_FILE"
echo -e "${GREEN}✅ GitHub MCP Server started (PID: $GITHUB_PID)${NC}"
sleep 1

# Start Notion MCP Server
echo -e "${BLUE}🚀 Starting Notion MCP Server (port 8002)...${NC}"
nohup python -m mcp_server.mcp_server_notion > "$NOTION_LOG" 2>&1 &
NOTION_PID=$!
echo "NOTION_PID=$NOTION_PID" >> "$PID_FILE"
echo -e "${GREEN}✅ Notion MCP Server started (PID: $NOTION_PID)${NC}"
sleep 1

# Start Slack MCP Server
echo -e "${BLUE}🚀 Starting Slack MCP Server (port 8003)...${NC}"
nohup python -m mcp_server.mcp_server_slack > "$SLACK_LOG" 2>&1 &
SLACK_PID=$!
echo "SLACK_PID=$SLACK_PID" >> "$PID_FILE"
echo -e "${GREEN}✅ Slack MCP Server started (PID: $SLACK_PID)${NC}"
sleep 2

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${GREEN}✅ All MCP Servers Started!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo -e "${YELLOW}Server Information:${NC}"
echo -e "  GitHub MCP: ${GREEN}http://localhost:8001${NC} (PID: $GITHUB_PID)"
echo -e "  Notion MCP: ${GREEN}http://localhost:8002${NC} (PID: $NOTION_PID)"
echo -e "  Slack MCP:  ${GREEN}http://localhost:8003${NC} (PID: $SLACK_PID)"
echo ""
echo -e "${YELLOW}Log Files:${NC}"
echo -e "  GitHub: $GITHUB_LOG"
echo -e "  Notion: $NOTION_LOG"
echo -e "  Slack:  $SLACK_LOG"
echo -e "  Combined: $COMBINED_LOG"
echo ""
echo -e "${YELLOW}PIDs saved to: $PID_FILE${NC}"
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Monitoring Combined Logs...${NC}"
echo -e "${CYAN}Press Ctrl+C to stop log monitoring${NC}"
echo -e "${CYAN}(Servers will keep running in background)${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Function to add service prefix and color to log lines
tail_with_prefix() {
    local service=$1
    local color=$2
    local logfile=$3

    tail -f "$logfile" 2>/dev/null | while IFS= read -r line; do
        echo -e "${color}[$service]${NC} $line" | tee -a "$COMBINED_LOG"
    done &
}

# Tail all logs with colored prefixes
tail_with_prefix "GITHUB" "$BLUE" "$GITHUB_LOG"
tail_with_prefix "NOTION" "$GREEN" "$NOTION_LOG"
tail_with_prefix "SLACK" "$YELLOW" "$SLACK_LOG"

# Wait for user interrupt
wait
