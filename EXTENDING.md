# Developer Extensibility Guide: Connecting Your Own Data Sources

This guide walks you through replacing the sample in-memory `ASSET_DB` with production data sources (PostgreSQL, Redis, Datadog, Prometheus, or internal REST APIs) in under 5 minutes.

---

## Architecture Overview

`Enterprise Asset OS` is built on **FastMCP 4** and the **2026-07-28 Stateless MCP Specification**. Every tool function is an asynchronous coroutine that receives:
1. Typed input arguments (validated automatically via Pydantic/type hints).
2. The `Context` object (for progress reporting, user-facing notifications, and logging).

```
[ AI Host (Claude / Cursor / Antigravity) ]
                     │  (JSON-RPC 2.0 via stdio or Streamable HTTP)
                     ▼
             [ server.py Core ]
                     │  (Async Coroutines)
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  [ PostgreSQL ]  [ Redis ]  [ REST / SRE APIs ]
```

---

## Step 1: Add Your Database Drivers

Add your required database or API client dependencies using `uv`:

```bash
# For PostgreSQL (asyncpg)
uv add asyncpg

# For Redis
uv add redis

# For External REST / HTTP APIs
uv add httpx
```

---

## Step 2: Replace `ASSET_DB` with Your Data Layer

Open [`server.py`](server.py) and update the `query_telemetry` tool:

### Example A: Connecting to PostgreSQL (asyncpg)

```python
import asyncpg
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

# Database connection pool lifecycle
DB_POOL = None

async def get_db_pool():
    global DB_POOL
    if DB_POOL is None:
        DB_POOL = await asyncpg.create_pool(os.environ.get("DATABASE_URL"))
    return DB_POOL

@mcp.tool(
    annotations=ToolAnnotations(
        title="Query Telemetry",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def query_telemetry(asset_id: str, ctx: Context) -> dict:
    """Retrieve live infrastructure telemetry from PostgreSQL."""
    clean_id = asset_id.strip().lower()
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT status, load_pct, region FROM assets WHERE asset_id = $1", 
            clean_id
        )
    
    if not row:
        raise ToolError(f"Asset ID '{asset_id}' not found in cluster database.")
        
    await ctx.report_progress(progress=1, total=1)
    return {
        "asset_id": clean_id,
        "telemetry": dict(row)
    }
```

### Example B: Connecting to an External REST / Cloud API (httpx)

```python
import httpx
from fastmcp import FastMCP, Context
from fastmcp.exceptions import ToolError

API_BASE_URL = os.environ.get("MONITORING_API_URL", "https://api.internal.company.com/v1")
API_KEY = os.environ.get("MONITORING_API_KEY")

@mcp.tool(
    annotations=ToolAnnotations(
        title="Query Telemetry",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def query_telemetry(asset_id: str, ctx: Context) -> dict:
    """Retrieve telemetry metrics via internal SRE monitoring API."""
    clean_id = asset_id.strip().lower()
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(
            f"{API_BASE_URL}/nodes/{clean_id}",
            headers={"Authorization": f"Bearer {API_KEY}"}
        )
        
    if response.status_code == 404:
        raise ToolError(f"Asset ID '{asset_id}' does not exist.")
    elif response.status_code != 200:
        raise ToolError(f"Upstream monitoring service error: {response.status_code}")
        
    await ctx.report_progress(progress=1, total=1)
    return {
        "asset_id": clean_id,
        "telemetry": response.json()
    }
```

---

## Step 3: Add New Tools in 10 Seconds

To add a new tool, simply use the `@mcp.tool` decorator with appropriate metadata hints:

```python
@mcp.tool(
    annotations=ToolAnnotations(
        title="Restart Node Service",
        readOnlyHint=False,      # Warning: mutating action
        idempotentHint=False,
        openWorldHint=False,
    )
)
async def restart_service(asset_id: str, service_name: str, ctx: Context) -> dict:
    """Safely trigger a remote service restart on a given infrastructure node."""
    logger.info("Restarting service %s on %s", service_name, asset_id)
    # Your execution logic here...
    return {"status": "restarted", "asset_id": asset_id, "service": service_name}
```

---

## Testing Your Changes

Run the test suite to ensure your new database logic passes validation:

```bash
uv run pytest
```
