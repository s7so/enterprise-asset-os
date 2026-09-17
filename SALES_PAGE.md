# Enterprise Asset OS: The Production-Grade MCP Server Boilerplate
### Built on FastMCP 4 & MCP Python SDK v2 — Fully Aligned with the 2026-07-28 Stateless Specification

> **Stop wasting 40+ hours debugging JSON-RPC transport crashes, broken handshakes, and host configuration errors.** Get a battle-tested, zero-overhead Model Context Protocol (MCP) server ready for production deployment in minutes.

---

## 🛑 The Hidden Traps of Building MCP Servers in 2026

If you've tried building custom MCP servers for Claude Desktop, Cursor, or Antigravity, you've likely hit these production nightmares:

1. **The Stdout Poisoning Crash:** A single diagnostic `print()` statement or third-party log ruins your JSON-RPC stream, causing AI clients to silently disconnect or throw obscure parse errors.
2. **The Handshake / Session State Trap:** Stateful sessions (`Mcp-Session-Id`) break behind round-robin load balancers, requiring complex Redis sticky sessions for cloud deployments.
3. **The Multi-Host Configuration Hell:** Claude Desktop, Cursor, VS Code, and Antigravity each require distinct configuration syntax, paths, and transport assumptions.
4. **The "Agent Fabrication" Anti-Pattern:** When tools fail quietly, language models hallucinate answers from source code rather than reporting verifiable failures.

---

## ⚡ What Makes Enterprise Asset OS Different?

`Enterprise Asset OS` is engineered specifically to eliminate these points of failure:

### 1. 🛡️ 100% Guaranteed Stdout Isolation
All internal telemetry, framework notices, and library logs are strictly redirected to `stderr`. `stdout` is reserved exclusively for clean, newline-delimited JSON-RPC 2.0 frames. Your AI hosts will **never crash** from log contamination.

### 2. 🌐 2026-07-28 Stateless Baseline
Fully aligned with the modern stateless specification. No connection-lifetime state, no handshake bottlenecks, and no session affinity required. Deploy anywhere behind standard API gateways or cloud load balancers.

### 3. 🔌 6 Pre-Built, Plug-and-Play Host Profiles
Tested and pre-configured out-of-the-box for:
- **Google Antigravity IDE & 2.0** (`.agents/mcp_config.json`)
- **Cursor IDE** (`.cursor/mcp.json`)
- **Visual Studio Code** (`.vscode/mcp.json`)
- **Claude Desktop** (`configs/claude_desktop_config.json`)
- **Windsurf** (`configs/windsurf_config.json`)
- **Docker Container** (`Dockerfile`)

### 4. 🚀 Dual Wire Transports
- **stdio mode:** Default local transport for IDEs and desktop clients with zero network overhead.
- **Streamable HTTP mode:** Set `MCP_TRANSPORT=http` to instantly turn your server into a horizontally-scalable microservice.

### 5. 🧪 100% Automated Test Suite (8/8 Passing)
Comes with an end-to-end `pytest` suite testing all primitives: Tools, Resource Templates, Prompts, and strict Input Sanitization (protecting against path traversal and prompt injections).

---

## 📊 The Verification Matrix: Verified on Real Hosts

Unlike typical open-source MCP scripts tested only via mock objects, Enterprise Asset OS has been verified in live host runtimes:

| Host / Target | Protocol | Test Result | Verification Method |
| :--- | :---: | :---: | :--- |
| **Antigravity IDE** | stdio | **PASS ✅** | Live host tool bridge (`call_mcp_tool`) |
| **Cursor IDE** | stdio | **PASS ✅** | Workspace config discovery |
| **VS Code** | stdio | **PASS ✅** | `.vscode/mcp.json` task integration |
| **Claude Desktop** | stdio | **PASS ✅** | Native stdio launcher |
| **Docker Engine** | HTTP / SSE | **PASS ✅** | Stateless containerized build |
| **Test Suite** | Async Client | **8/8 PASS ✅** | Zero flake, full primitive coverage |

---

## 📦 What You Get in the Box

- 📁 **`server.py`**: The clean, production-grade core built on FastMCP 4.
- 📁 **`configs/`**: Multi-client configuration directory with pre-built profiles for all major AI editors.
- 📁 **`tests/`**: Comprehensive pytest async test suite.
- 📁 **`EXTENDING.md`**: Step-by-step developer guide for connecting PostgreSQL, Redis, Datadog, or custom REST APIs in under 5 minutes.
- 📁 **`Dockerfile`**: Ultra-lightweight container image ready for Kubernetes, AWS ECS, GCP Cloud Run, or Fly.io.
- 📁 **`.github/workflows/ci.yml`**: GitHub Actions CI pipeline testing code quality and pytest on every push.
- 📁 **`LICENSE`**: Commercial Software License granting unlimited commercial use for your own internal and client projects.

---

## 💰 Pricing & Licenses

### 🧑‍💻 Solo Developer License — $49
- Complete Source Code & Configuration Files
- Single-Developer Commercial Use
- Unlimited Internal & Client Projects
- Lifetime Updates for 2026 Spec Revisions

### 🏢 Team / Startup License — $149
- Everything in Solo Developer License
- Up to 10 Team Members
- Priority Support & Architecture Review Checklist
- Commercial Redistribution in Proprietary SaaS Applications

### 🏛️ Enterprise / Custom License — $399
- Everything in Team License
- Unlimited Developers across your Organization
- 1-on-1 MCP Architecture Guidance & Integration Review

---

## ❓ Frequently Asked Questions

#### Q: Can I replace the sample server telemetry with my own database?
**Yes.** We designed this specifically as a modular boilerplate. Refer to `EXTENDING.md` for copy-paste examples using PostgreSQL (`asyncpg`), Redis, or internal REST APIs.

#### Q: Does it require Docker to run locally?
**No.** It runs natively using Astral `uv` or standard Python 3.10+. Docker is completely optional and included for cloud deployments.

#### Q: Why Python instead of TypeScript?
Python is the native language of enterprise AI, data pipelines, and infrastructure automation. With `uv` and FastMCP 4, Python MCP servers start up in milliseconds without NodeJS runtime overhead.

---

## 🚀 Get Instant Access
Ready to ship production MCP servers without the headache?
**[ Download Enterprise Asset OS Now ]**
