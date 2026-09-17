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
