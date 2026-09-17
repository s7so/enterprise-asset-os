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

---

## Step 6: Testing with Synthetic & Research-Licensed Datasets (Fetch-on-Demand)

`Enterprise Asset OS` follows strict license compliance and distribution boundaries:
- **Default Offline Tests**: Run against `tests/data/synthetic_fixtures.json` (production-format-mimicking samples with zero restricted data).
- **Research Benchmarks (Loghub)**: Never bundled in distributed artifacts; acquired strictly fetch-on-demand via pinned cryptographic hashes.

### 1. Default Offline CI Suite
Runs out-of-the-box with full network isolation:
```bash
uv run pytest -v
```

### 2. Fetching Real Research Datasets (Opt-In)
To download and verify canonical Loghub benchmarks under the **Loghub Research/Academic License** (arXiv:2308.07703):
```bash
uv run tests/data/fetch_real_fixtures.py
```

### 3. Running Opt-In Real Data Benchmarks
Once fetched, execute the full test suite including verified Loghub incident evaluations:
```bash
# On Linux/macOS
RUN_REAL_DATA=1 uv run pytest -v

# On Windows (PowerShell)
$env:RUN_REAL_DATA="1"; uv run pytest -v
```

### 4. Activating Live Enterprise Prometheus Telemetry
To point your server to your own corporate Prometheus monitoring deployment:
```bash
export TELEMETRY_BACKEND="prometheus"
export TELEMETRY_PROMETHEUS_URL="http://your-internal-prometheus:9090"
uv run server.py
```

---

## Step 7: Connecting Live ERP & Accounting Systems (Odoo / Daftra / PostgreSQL)

The built-in accounting engine (`src/enterprise_asset_os/accounting.py`) powers `get_unpaid_invoices` and `get_cash_flow_summary` with zero-configuration SQLite benchmark data out-of-the-box. To route queries directly to live production accounting databases:

### Option A: Direct PostgreSQL (Odoo ERP `account_move` table)
```python
import asyncpg

async def get_odoo_unpaid_invoices(min_days_overdue: int = 0):
    conn = await asyncpg.connect("postgresql://odoo_user:password@localhost:5432/odoo_db")
    query = """
        SELECT m.name AS invoice_number, p.name AS client_name, 
               m.invoice_date_due AS due_date, m.amount_total, 
               m.amount_residual AS amount_due,
               CURRENT_DATE - m.invoice_date_due AS days_overdue
        FROM account_move m
        JOIN res_partner p ON p.id = m.partner_id
        WHERE m.state = 'posted' AND m.payment_state IN ('not_paid', 'partial')
          AND (CURRENT_DATE - m.invoice_date_due) >= $1
        ORDER BY days_overdue DESC;
    """
    rows = await conn.fetch(query, min_days_overdue)
    await conn.close()
    return [dict(r) for r in rows]
```

### Option B: REST API (Daftra Cloud Invoicing)
```python
import httpx

async def get_daftra_unpaid_invoices(api_key: str, subdomain: str):
    headers = {"API-KEY": api_key, "Accept": "application/json"}
    url = f"https://{subdomain}.daftra.com/api2/v2/invoices?status=unpaid"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, headers=headers)
        data = resp.json()
        return data.get("data", [])
```


