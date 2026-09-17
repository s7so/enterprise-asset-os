"""
Enterprise Asset & Telemetry MCP Server — Root Execution Shim
Delegates to the canonical enterprise_asset_os package implementation.
"""
from enterprise_asset_os.server import (
    mcp,
    run_server,
    query_telemetry,
    query_store_inventory,
    get_unpaid_invoices,
    get_cash_flow_summary,
    get_config_schema,
    incident_triage_prompt,
    ASSET_DB,
    CLUSTER_DB,
)

if __name__ == "__main__":
    run_server()
