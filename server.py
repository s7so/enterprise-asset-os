"""
Enterprise Asset & Telemetry MCP Server — 2026-07-28 spec
Python 3.10+ / fastmcp 4.x / MCP Python SDK v2
"""
import json
import logging
import os
import sys

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

# Stdout Isolation: ALL logging to stderr, stdout stays pure JSON-RPC
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("EnterpriseAssetMCP")

# FastMCP 4 negotiates protocol era per-connection:
# modern (2026-07-28, stateless) AND legacy (handshake-era) clients both work
mcp = FastMCP(
    "Enterprise-Asset-OS",
    mask_error_details=True,
    cache_ttl=300,          # freshness hint on results (2026-07-28)
    cache_scope="private",
)

ASSET_DB = {
    "server-01": {"status": "active", "load_pct": 34.5, "region": "us-east-1"},
    "server-02": {"status": "degraded", "load_pct": 89.2, "region": "eu-west-1"},
}


@mcp.tool(
    annotations=ToolAnnotations(
        title="Query Telemetry",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def query_telemetry(asset_id: str, ctx: Context) -> dict:
    """Retrieve live telemetry metrics for an enterprise infrastructure node.

    Args:
        asset_id: Unique string identifier of the server node (e.g. 'server-01').
    """
    logger.info("query_telemetry called for %s", asset_id)


    clean_id = asset_id.strip().lower()
    if clean_id not in ASSET_DB:
        raise ToolError(
            f"Asset ID '{asset_id}' not found. Valid IDs: {sorted(ASSET_DB)}"
        )
    await ctx.report_progress(progress=1, total=1)
    return {"asset_id": clean_id, "telemetry": ASSET_DB[clean_id]}


@mcp.resource("config://schemas/{schema_type}")
def get_config_schema(schema_type: str) -> str:
    """Fetch read-only JSON schema specifications."""
    schemas = {
        "network": {"type": "object", "properties": {"ip": {"type": "string"}, "vlan": {"type": "integer"}}},
        "compute": {"type": "object", "properties": {"vcpus": {"type": "integer"}, "ram_gb": {"type": "number"}}},
    }
    key = schema_type.strip().lower()
    if key not in schemas:
        return json.dumps({"error": f"Unknown schema '{schema_type}'. Valid: {sorted(schemas)}"})
    return json.dumps(schemas[key])


@mcp.prompt()
def incident_triage_prompt(incident_log: str) -> str:
    """Structured diagnostic prompt for incident response."""
    return (
        "You are a Senior SRE. Analyze this log excerpt and output "
        f"a root-cause diagnosis and remediation plan:\n\n{incident_log}"
    )


if __name__ == "__main__":
    if os.environ.get("MCP_TRANSPORT") == "http":
        # Streamable HTTP — stateless, any replica serves any request
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    else:
        mcp.run()  # stdio by default
