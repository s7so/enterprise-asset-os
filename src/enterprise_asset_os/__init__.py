"""
Enterprise Asset OS Package Entrypoint
"""
import os
import sys

def main() -> None:
    """CLI script entrypoint for running the MCP server."""
    # Ensure server module can be imported from current working directory or package root
    sys.path.insert(0, os.path.abspath("."))
    from server import mcp

    if os.environ.get("MCP_TRANSPORT") == "http":
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    else:
        mcp.run()  # stdio transport by default
