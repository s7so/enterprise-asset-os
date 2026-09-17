# Multi-Client Host Configuration Guide

This directory provides pre-configured integration profiles for all supported MCP hosts.

## 1. Claude Desktop
- **Windows Target:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS Target:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- Copy the content of [`claude_desktop_config.json`](claude_desktop_config.json) into your Claude config file.
- Restart Claude Desktop completely from system tray.

## 2. Cursor IDE
- **Project-level:** Already configured in [`.cursor/mcp.json`](../.cursor/mcp.json).
- **Global:** `~/.cursor/mcp.json`.

## 3. Claude Code CLI
Run in terminal:
```bash
claude mcp add enterprise-asset-os -- uv --directory "D:/New folder/enterprise-asset-os" run server.py
```

## 4. Windsurf
- **Target:** `~/.codeium/windsurf/mcp_config.json`
- Copy the content of [`windsurf_config.json`](windsurf_config.json).

## 5. Visual Studio Code
- Project-level file configured in [`.vscode/mcp.json`](../.vscode/mcp.json).

## 6. Antigravity IDE & 2.0 (Official Documentation: [antigravity.google/docs/mcp](https://antigravity.google/docs/mcp))

Antigravity supports two discovery locations:

### Option A: Workspace Setup (Recommended for this Repo)
- **Path:** `.agents/mcp_config.json` (Already pre-configured in the repository root)
- Automatically discovered by Antigravity IDE and SDK whenever this workspace is opened:
```json
{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": ["run", "server.py"],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Option B: Global Setup
- **Path:** `~/.gemini/config/mcp_config.json` (on Windows: `%USERPROFILE%\.gemini\config\mcp_config.json`)
- Accessible via IDE UI: **Agent Panel `...` > MCP Servers > Manage MCP Servers > View raw config**
```json
{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/enterprise-asset-os",
        "run",
        "server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

> [!TIP]
> In Antigravity IDE, inspect active server health and reload connections via **Additional Options (...) > MCP Servers** or with `/mcp` in the CLI.

---

## 7. ChatGPT (OpenAI Developer Mode — 2026 Verified)
*Official Source: OpenAI Developer Platform — Model Context Protocol in ChatGPT*

- **Transport:** Streamable HTTP / SSE (`MCP_TRANSPORT=http PORT=8000 uv run server.py`)
- **Requirements:** ChatGPT Plus, Team, or Enterprise account with Developer Mode enabled.
- **Setup Steps:**
  1. Launch server in HTTP transport mode:
     ```bash
     export MCP_TRANSPORT=http
     export PORT=8000
     uv run server.py
     ```
  2. For local testing, expose port 8000 via a secure tunnel: `ngrok http 8000`.
  3. In ChatGPT: Go to **Settings > Security & login > Enable Developer mode**.
  4. Under Connected Apps / MCP Servers, add your endpoint URL: `https://<your-subdomain>.ngrok-free.app/mcp`.
  5. The tools (`query_telemetry`, `query_store_inventory`) become active directly inside ChatGPT chats.
- Pre-configured profile: [`chatgpt_config.json`](chatgpt_config.json).

---

## 8. Grok (xAI Remote Connectors & CLI — 2026 Verified)
*Official Source: xAI Documentation (docs.x.ai) — Remote MCP Tools Specification*

- **Transport:** Streamable HTTP / SSE.
- **Web UI Setup:**
  1. Navigate to [grok.com/connectors](https://grok.com/connectors).
  2. Click **Add Custom MCP Connector**.
  3. Enter your remote server URL (e.g. `https://<your-server-domain>/mcp`).
- **CLI Setup:**
  ```bash
  grok mcp add enterprise-asset-os https://<your-server-domain>/mcp
  ```
- **Configuration File:** Add to `~/.grok/config.toml`:
  ```toml
  [mcp_servers.enterprise_asset_os]
  url = "https://<your-server-domain>/mcp"
  transport = "http"
  ```
- Pre-configured profile: [`grok_config.toml`](grok_config.toml).
