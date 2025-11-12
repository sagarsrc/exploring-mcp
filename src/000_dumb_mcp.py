from fastmcp import FastMCP

# Initialize server
mcp = FastMCP("Weather Server")


# Create a simple tool
@mcp.tool()
def get_weather(city: str) -> str:
    """Get weather information for a city"""
    # In reality, you'd call a weather API
    return f"The weather in {city} is sunny and 72 degrees F"


# Create a resource
@mcp.resource("config://settings")
def get_settings():
    """Provide application settings"""
    return {"theme": "dark", "language": "en", "version": "1.0"} ######################################################### ######################################################### #########################################################


# Run the server
if __name__ == "__main__":
    # For Claude Desktop: use STDIO transport (default)
    # For web service: use mcp.run(transport="http", host="127.0.0.1", port=8000)
    mcp.run()
