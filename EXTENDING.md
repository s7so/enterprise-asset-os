# Developer Extensibility & Production Customization Guide

This guide provides step-by-step instructions for adapting, extending, and integrating `Enterprise Asset OS` into your existing corporate infrastructure (PostgreSQL, Redis, Datadog, Prometheus, or internal REST APIs) in under 5 minutes.

---

## ⚠️ The Golden Rule: Stdout Isolation

Before writing any custom code, you **must** understand the fundamental constraint of Model Context Protocol (MCP) servers:

> [!CAUTION]
> **NEVER USE `print()` OR ALLOW LOGS ON `STDOUT`**
> 
> The `stdout` stream is reserved **exclusively** for newline-delimited JSON-RPC 2.0 protocol frames. 
> - If any library, database driver, or diagnostic statement writes to `stdout` (e.g. `print()`, SQLAlchemy `echo=True`, or default unconfigured `logging`), the JSON-RPC stream is corrupted.
> - This causes Claude Desktop, Cursor, and Antigravity to silently disconnect or crash with `Unexpected token in JSON-RPC stream`.
> - **Always** route all diagnostic outputs to `stderr` using `logger.info()` or `sys.stderr.write()`.

---

## Architecture Overview

`Enterprise Asset OS` is powered by **FastMCP 4** and the **2026-07-28 Stateless MCP Baseline**. Each tool is an asynchronous Python coroutine that receives strongly-typed arguments and an optional `Context` object for client feedback.

```
┌─────────────────────────────────────────────────────────┐
│     AI Hosts (Claude Desktop / Cursor / Antigravity)     │
└────────────────────────────┬────────────────────────────┘
                             │  Clean JSON-RPC 2.0 (stdio or Streamable HTTP)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   server.py Core Engine                 │
│  - Stdout Isolation (Logs strictly to stderr)           │
│  - Input Sanitization & Path Traversal Guards           │
│  - Automated Tool Annotations (readOnlyHint, etc.)      │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
               ▼                           ▼
      [ Database Layer ]           [ Upstream APIs ]
      - PostgreSQL (asyncpg)       - REST / SRE APIs (httpx)
      - Redis Cache (redis-py)     - CloudWatch / Datadog
```

---

## Step 1: Add Dependencies

Use Astral `uv` to add your desired drivers:

```bash
# PostgreSQL async driver
uv add asyncpg

# Redis async client
uv add redis

# High-performance async HTTP client
uv add httpx
```

---

## Step 2: Configure Host Environment Variables

Desktop AI hosts (like Claude Desktop and Cursor) run in GUI process spaces and **do not automatically inherit your terminal's shell environment variables**. 

Always inject your connection strings directly into the host configuration's `"env"` block:

### For Antigravity (`.agents/mcp_config.json`):
```json
{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": ["run", "server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/telemetry_db",
        "MONITORING_API_KEY": "sec_live_example_token"
      }
    }
  }
}
```

### For Claude Desktop (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": ["--directory", "/path/to/enterprise-asset-os", "run", "server.py"],
      "env": {
        "LOG_LEVEL": "INFO",
        "DATABASE_URL": "postgresql://user:password@localhost:5432/telemetry_db"
      }
    }
  }
}
```

---

## Step 3: Replace `ASSET_DB` with Live Data

Below are production-ready, fully self-contained examples to replace the sample dictionary.

### Example A: Live PostgreSQL Integration (`asyncpg`)

```python
import logging
import os
import sys
import asyncpg
from fastmcp import Context
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

logger = logging.getLogger("EnterpriseAssetMCP")

# Global connection pool with lazy initialization
_DB_POOL: asyncpg.Pool | None = None

async def get_db_pool() -> asyncpg.Pool:
    global _DB_POOL
    if _DB_POOL is None:
        db_url = os.environ.get("DATABASE_URL")
        if not db_url:
            raise ToolError("Configuration error: 'DATABASE_URL' environment variable is missing.")
        try:
            _DB_POOL = await asyncpg.create_pool(db_url, min_size=2, max_size=10)
            logger.info("PostgreSQL connection pool initialized successfully.")
        except Exception as exc:
            logger.error("Failed to connect to PostgreSQL: %s", exc)
            raise ToolError(f"Database connection failure: {exc}")
    return _DB_POOL

# Replace the existing query_telemetry tool in server.py:
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
    logger.info("Executing PostgreSQL query for asset: %s", clean_id)
    
    pool = await get_db_pool()
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT status, load_pct, region FROM server_nodes WHERE asset_id = $1", 
                clean_id
            )
    except Exception as exc:
        logger.error("SQL execution error: %s", exc)
        raise ToolError(f"Query execution failed: {exc}")
        
    if not row:
        raise ToolError(f"Asset ID '{clean_id}' not found in active cluster.")
        
    await ctx.report_progress(progress=1, total=1)
    return {
        "asset_id": clean_id,
        "telemetry": dict(row)
    }
```

---

### Example B: Live REST / SRE Monitoring API Integration (`httpx`)

```python
import logging
import os
import sys
import httpx
from fastmcp import Context
from fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

logger = logging.getLogger("EnterpriseAssetMCP")

API_BASE = os.environ.get("MONITORING_API_URL", "https://api.internal.company.com/v1")
API_KEY = os.environ.get("MONITORING_API_KEY", "")

@mcp.tool(
    annotations=ToolAnnotations(
        title="Query Telemetry",
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )
)
async def query_telemetry(asset_id: str, ctx: Context) -> dict:
    """Retrieve live telemetry from upstream SRE monitoring API."""
    clean_id = asset_id.strip().lower()
    
    headers = {"Accept": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
        
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"{API_BASE}/telemetry/{clean_id}", headers=headers)
    except httpx.TimeoutException:
        raise ToolError(f"Monitoring service timed out while querying node '{clean_id}'.")
    except httpx.RequestError as exc:
        raise ToolError(f"Network error communicating with monitoring API: {exc}")

    if resp.status_code == 404:
        raise ToolError(f"Node '{clean_id}' does not exist.")
    elif resp.status_code != 200:
        raise ToolError(f"Monitoring API error ({resp.status_code}): {resp.text}")

    await ctx.report_progress(progress=1, total=1)
    return {
        "asset_id": clean_id,
        "telemetry": resp.json()
    }
```

---

## Step 4: Adding New MCP Primitives

### 1. Adding an Action Tool (with safety annotations)
```python
@mcp.tool(
    annotations=ToolAnnotations(
        title="Restart Node Service",
        readOnlyHint=False,      # Informs the AI that this action mutates state
        idempotentHint=False,    # Calling twice may restart twice
        openWorldHint=False,     # Internal closed domain
    )
)
async def restart_service(asset_id: str, service_name: str, ctx: Context) -> dict:
    """Restart a specific system daemon on a target infrastructure node."""
    logger.info("Requested service restart: %s on node %s", service_name, asset_id)
    # Perform service restart logic here...
    return {"status": "success", "asset_id": asset_id, "service": service_name}
```

### 2. Adding a Dynamic Resource Template
```python
@mcp.resource("config://nodes/{asset_id}/specs")
async def get_node_specs(asset_id: str) -> str:
    """Read-only dynamic resource returning hardware specifications."""
    clean_id = asset_id.strip().lower()
    # Fetch hardware specifications...
    return json.dumps({"asset_id": clean_id, "cores": 16, "ram_gb": 64})
```

---

## Step 5: Updating Tests

Whenever you customize database queries, update your tests in `tests/test_server.py`. You can use `unittest.mock` or `pytest-asyncio` to mock external database pools or HTTP calls, ensuring your CI pipeline remains fast and deterministic:

```bash
uv run pytest -v
```
