"""
Enterprise Asset OS Package Entrypoint
"""
from enterprise_asset_os.server import mcp, run_server


def main() -> None:
    """CLI script entrypoint for running the MCP server."""
    run_server()


__all__ = ["mcp", "main", "run_server"]
