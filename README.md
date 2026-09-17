# Enterprise Asset OS — Model Context Protocol (MCP) Server

Production-grade Model Context Protocol (MCP) server built with **FastMCP 4** and **MCP Python SDK v2**, fully aligned with the **MCP 2026-07-28 Specification Baseline**.

## Architecture & Features
- **Stateless Core (2026-07-28)**: Zero handshake overhead, no `Mcp-Session-Id`, and no connection-lifetime state. Every request is self-contained via `_meta`.
- **Dual Transport Engine**:
  - **stdio**: Default local transport for AI hosts with strict **Stdout Isolation** (stdout reserved strictly for UTF-8 newline-delimited JSON-RPC 2.0 frames; all diagnostics directed to `stderr`).
  - **Streamable HTTP**: Stateless HTTP POST/SSE endpoint (`MCP_TRANSPORT=http`) scalable behind round-robin load balancers without session affinity.
- **MCP Primitives**:
  - **Tools**:
    - `query_telemetry`: Server infrastructure monitoring with strict `readOnlyHint` and `idempotentHint`.
    - `query_store_inventory`: E-commerce catalog and stock replenishment analyzer with zero-network offline fallback.
    - `get_unpaid_invoices`: Accounts receivable and overdue invoice aging audit for ERP/SME accounting (Odoo / Daftra schema).
    - `get_cash_flow_summary`: Executive cash flow, collection rates, aging distribution, and top debtor ranking.
  - **Resource Template**: `config://schemas/{schema_type}` with parameter traversal protection.
  - **Prompt**: `incident_triage_prompt` for automated SRE incident diagnostics.

## Quickstart

### Prerequisites
- Python 3.10+
- Astral `uv` 0.12+

### Run Locally (stdio)
```bash
uv run server.py
```

### Run as Streamable HTTP Service
```bash
export MCP_TRANSPORT=http
export PORT=8000
uv run server.py
```

### Run Tests
```bash
uv run pytest -q
```

## Multi-Client Integration

Pre-built host profiles are provided for all major AI environments:
- **Google Antigravity IDE & 2.0**: [`.agents/mcp_config.json`](.agents/mcp_config.json) (Auto-discovered)
- **Cursor IDE**: [`.cursor/mcp.json`](.cursor/mcp.json)
- **Visual Studio Code**: [`.vscode/mcp.json`](.vscode/mcp.json)
- **Claude Desktop**: [`configs/claude_desktop_config.json`](configs/claude_desktop_config.json)
- **Windsurf**: [`configs/windsurf_config.json`](configs/windsurf_config.json)
- **ChatGPT (OpenAI Developer Mode)**: [`configs/chatgpt_config.json`](configs/chatgpt_config.json)
- **Grok (xAI Connectors & CLI)**: [`configs/grok_config.toml`](configs/grok_config.toml)

For detailed host setup and troubleshooting, see [`configs/README.md`](configs/README.md).

## Customization & Production Deployment

To connect live PostgreSQL databases, Redis clusters, or proprietary SRE APIs, follow the comprehensive [Developer Extensibility Guide (`EXTENDING.md`)](EXTENDING.md).

## Docker Deployment
```bash
docker build -t enterprise-asset-os .
docker run -p 8000:8000 -e MCP_TRANSPORT=http enterprise-asset-os
```

## License
Commercial Software License. See [`LICENSE`](LICENSE) for complete terms.
