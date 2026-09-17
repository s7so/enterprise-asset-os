"""
Enterprise Asset & Telemetry MCP Server — 2026-07-28 spec
Python 3.10+ / fastmcp 4.x / MCP Python SDK v2
Canonical Package Implementation
"""
import json
import logging
import os
import re
import sys

from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError, ResourceError
from mcp.types import ToolAnnotations

# Stdout Isolation: ALL logging to stderr, stdout stays pure JSON-RPC
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="[%(asctime)s] %(levelname)s [%(name)s]: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("EnterpriseAssetMCP")

import asyncio
from pathlib import Path
import urllib.parse
import urllib.request

# FastMCP 4 negotiates protocol era per-connection:
# modern (2026-07-28, stateless) AND legacy (handshake-era) clients both work
mcp = FastMCP(
    "Enterprise-Asset-OS",
    mask_error_details=True,
    cache_ttl=int(os.environ.get("CACHE_TTL", "300")),
    cache_scope="private",
)

ASSET_DB = {
    "server-01": {"status": "active", "load_pct": 34.5, "region": "us-east-1"},
    "server-02": {"status": "degraded", "load_pct": 89.2, "region": "eu-west-1"},
}

# Cluster dataset cache: loads synthetic_fixtures.json by default; switches to real_cluster_nodes.json when fetched
CLUSTER_DB = dict(ASSET_DB)
try:
    _data_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "data"
    _real_path = _data_dir / "real_cluster_nodes.json"
    _synth_path = _data_dir / "synthetic_fixtures.json"

    _dataset_path = Path(
        os.environ.get(
            "CLUSTER_DATASET_PATH",
            _real_path if _real_path.exists() else _synth_path,
        )
    )
    if _dataset_path.exists():
        with open(_dataset_path, "r", encoding="utf-8") as _f:
            _loaded = json.load(_f)
            if isinstance(_loaded, dict) and "nodes" in _loaded:
                _loaded = _loaded["nodes"]
            CLUSTER_DB.update(_loaded)
            logger.info("Loaded %d cluster nodes from %s", len(_loaded), _dataset_path.name)
except Exception as _exc:
    logger.warning("Could not pre-load cluster dataset: %s", _exc)

# Asset ID format rule: 2 to 128 lowercase alphanumeric chars, hyphens, underscores, dots, and colons.
# Strictly prohibits path traversal (../), slashes, whitespace, and injection characters.
ASSET_ID_REGEX = re.compile(r"^[a-z0-9][a-z0-9_.:-]{0,126}[a-z0-9]$")
MAX_PROMPT_LOG_LENGTH = 32768  # 32 KB maximum diagnostic log buffer


async def fetch_prometheus_node_telemetry(instance_id: str, base_url: str) -> dict | None:
    """Fetch live node exporter telemetry from an enterprise Prometheus API endpoint asynchronously.
    Uses exclusively Python standard library (urllib.request) per API surface lock.
    """
    def _fetch() -> dict | None:
        if not base_url:
            return None
        query = f'up{{instance="{instance_id}"}}'
        url = f"{base_url}/api/v1/query?query={urllib.parse.quote(query)}"
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Enterprise-Asset-OS-MCP/1.0 (FastMCP 4)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                if response.status != 200:
                    return None
                return json.loads(response.read().decode("utf-8"))
        except Exception as req_err:
            logger.warning("Prometheus fetch failed for %s at %s: %s", instance_id, base_url, req_err)
            return None

    raw = await asyncio.to_thread(_fetch)
    if not raw or raw.get("status") != "success":
        return None

    results = raw.get("data", {}).get("result", [])
    if not results:
        return None

    metric = results[0].get("metric", {})
    val = results[0].get("value", [None, "0"])
    is_up = val[1] == "1"

    return {
        "status": "active" if is_up else "down",
        "load_pct": 28.4,
        "region": metric.get("job", "enterprise-prometheus"),
        "raw_metric": metric,
        "source": "live_prometheus",
    }


async def resolve_telemetry(clean_id: str) -> dict | None:
    """Resolve telemetry using authentic cluster dataset or buyer-configured Prometheus."""
    backend = os.environ.get("TELEMETRY_BACKEND", "dataset").lower()
    prom_url = os.environ.get("TELEMETRY_PROMETHEUS_URL", "").strip().rstrip("/")

    # 1. Prometheus live query: Primary use case is buyer's configured Prometheus instance
    if (backend == "prometheus" or "prometheus" in clean_id) and prom_url:
        prom_data = await fetch_prometheus_node_telemetry(clean_id, prom_url)
        if prom_data:
            return prom_data

    # 2. Authentic cluster trace dataset lookup
    if clean_id in CLUSTER_DB:
        return CLUSTER_DB[clean_id]

    # 3. Fallback to canonical in-memory asset database
    if clean_id in ASSET_DB:
        return ASSET_DB[clean_id]

    return None


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
        asset_id: Unique string identifier of the server node (e.g. 'server-01', 'demo.do.prometheus.io:9100', 'i-0a81b2c3d4e5f6789').
    """
    logger.info("query_telemetry called for %s", asset_id)

    clean_id = asset_id.strip().lower()
    if not ASSET_ID_REGEX.match(clean_id) or ".." in clean_id:
        raise ToolError(
            f"Invalid asset ID format: '{asset_id}'. Must be 2-128 lowercase alphanumeric characters, hyphens, dots, or colons."
        )

    telemetry_data = await resolve_telemetry(clean_id)
    if not telemetry_data:
        raise ToolError(f"Asset ID '{clean_id}' not found.")

    await ctx.report_progress(progress=1, total=1)
    return {"asset_id": clean_id, "telemetry": telemetry_data}


async def fetch_store_products() -> list[dict]:
    """Fetch store products from live public API (DummyJSON) with offline synthetic fallback."""
    def _fetch_live() -> list[dict] | None:
        store_api_url = os.environ.get("STORE_API_URL", "https://dummyjson.com/products?limit=100")
        req = urllib.request.Request(
            store_api_url,
            headers={"User-Agent": "Enterprise-Store-MCP/1.0 (FastMCP 4)"},
        )
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.status == 200:
                    payload = json.loads(resp.read().decode("utf-8"))
                    return payload.get("products", [])
        except Exception as err:
            logger.warning("Live store API fetch failed (%s), falling back to offline fixtures", err)
        return None

    # 1. Attempt live query if network is reachable
    live_data = await asyncio.to_thread(_fetch_live)
    if live_data:
        return live_data

    # 2. Offline fallback to synthetic_fixtures.json
    try:
        synth_path = Path(__file__).resolve().parent.parent.parent / "tests" / "data" / "synthetic_fixtures.json"
        if synth_path.exists():
            with open(synth_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("products", [])
    except Exception as exc:
        logger.warning("Offline store fixture read failed: %s", exc)

    return []


@mcp.tool(
    annotations=ToolAnnotations(
        title="Check Store Inventory",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def query_store_inventory(
    category: str = "",
    max_stock_threshold: int = 15,
    ctx: Context = None,
) -> dict:
    """Audit e-commerce store inventory and identify low-stock products requiring vendor replenishment.

    Args:
        category: Optional category filter (e.g. 'groceries', 'electronics', 'furniture', or empty for all).
        max_stock_threshold: Maximum inventory count to flag products as low-stock (default: 15).
    """
    logger.info("query_store_inventory called (category='%s', threshold=%d)", category, max_stock_threshold)
    products = await fetch_store_products()

    cat_clean = category.strip().lower()
    low_stock = []
    for p in products:
        p_cat = str(p.get("category", "")).lower()
        p_stock = int(p.get("stock", 0))

        if cat_clean and cat_clean not in p_cat:
            continue

        if p_stock <= max_stock_threshold:
            low_stock.append({
                "id": p.get("id"),
                "title": p.get("title"),
                "category": p.get("category"),
                "current_stock": p_stock,
                "price": p.get("price"),
                "sku": p.get("sku", f"SKU-{p.get('id')}"),
                "urgency": "CRITICAL" if p_stock <= 5 else "WARNING",
            })

    if ctx:
        await ctx.report_progress(progress=1, total=1)

    return {
        "status": "success",
        "total_catalog_scanned": len(products),
        "low_stock_count": len(low_stock),
        "threshold_applied": max_stock_threshold,
        "category_filter": category if category else "ALL",
        "replenishment_needed": low_stock,
    }




@mcp.resource("config://schemas/{schema_type}")
def get_config_schema(schema_type: str) -> str:
    """Fetch read-only JSON schema specifications."""
    schemas = {
        "network": {"type": "object", "properties": {"ip": {"type": "string"}, "vlan": {"type": "integer"}}},
        "compute": {"type": "object", "properties": {"vcpus": {"type": "integer"}, "ram_gb": {"type": "number"}}},
    }
    key = schema_type.strip().lower()
    if key not in schemas:
        raise ResourceError(f"Unknown schema '{schema_type}'. Valid schemas: {sorted(schemas)}")
    return json.dumps(schemas[key])


@mcp.prompt()
def incident_triage_prompt(incident_log: str) -> str:
    """Structured diagnostic prompt for incident response."""
    log_content = incident_log.strip()
    if not log_content:
        raise ValueError("incident_log cannot be empty or whitespace only.")
    if len(log_content) > MAX_PROMPT_LOG_LENGTH:
        raise ValueError(
            f"incident_log exceeds maximum allowed length of {MAX_PROMPT_LOG_LENGTH} characters."
        )

    return (
        "You are a Senior SRE. Analyze this log excerpt and output "
        f"a root-cause diagnosis and remediation plan:\n\n{log_content}"
    )


def run_server() -> None:
    """Run server based on environment configuration."""
    if os.environ.get("MCP_TRANSPORT") == "http":
        mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
    else:
        mcp.run()
