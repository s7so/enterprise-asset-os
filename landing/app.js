/**
 * Enterprise Asset OS — Interactive Web Application Logic
 * Strictly adhering to UI/UX Pro Max Accessibility & Interaction Guidelines
 */

document.addEventListener('DOMContentLoaded', () => {
  initTerminalSimulator();
  initHostProfileSwitcher();
  initFaqAccordion();
  initClipboardHandlers();
});

/* ==========================================================================
   1. Interactive Live MCP Terminal Simulator
   ========================================================================== */
function initTerminalSimulator() {
  const terminalBody = document.getElementById('terminal-body');
  const latencyDisplay = document.getElementById('terminal-latency-val');
  const queryBtn1 = document.getElementById('btn-query-01');
  const queryBtn2 = document.getElementById('btn-query-02');
  const injectBtn = document.getElementById('btn-query-inject');
  const stdoutToggle = document.getElementById('btn-toggle-stdout');

  if (!terminalBody) return;

  let stdoutIsolationEnabled = true;

  const sampleResponses = {
    'server-01': {
      request: { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-01" } } },
      stderr: "[2026-09-17 14:30:12] INFO [EnterpriseAssetMCP]: query_telemetry called for server-01",
      response: {
        jsonrpc: "2.0",
        id: 1,
        result: {
          content: [{ type: "text", text: JSON.stringify({ asset_id: "server-01", telemetry: { status: "active", load_pct: 34.5, region: "us-east-1" } }, null, 2) }]
        }
      },
      latency: "14ms"
    },
    'server-02': {
      request: { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-02" } } },
      stderr: "[2026-09-17 14:30:15] INFO [EnterpriseAssetMCP]: query_telemetry called for server-02",
      response: {
        jsonrpc: "2.0",
        id: 2,
        result: {
          content: [{ type: "text", text: JSON.stringify({ asset_id: "server-02", telemetry: { status: "degraded", load_pct: 89.2, region: "eu-west-1" } }, null, 2) }]
        }
      },
      latency: "18ms"
    },
    'injection': {
      request: { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-01' OR '1'='1" } } },
      stderr: "[2026-09-17 14:30:20] WARNING [EnterpriseAssetMCP]: Input sanitization triggered on key traversal attempt",
      response: {
        jsonrpc: "2.0",
        id: 3,
        error: {
          code: -32602,
          message: "ToolError: Asset ID 'server-01\\' OR \\'1\\'=\\'1' not found. Valid IDs: ['server-01', 'server-02']"
        }
      },
      latency: "9ms"
    }
  };

  function executeSimulation(key) {
    const data = sampleResponses[key];
    if (!data) return;

    terminalBody.innerHTML = '';
    latencyDisplay.textContent = 'executing...';

    // 1. Host call line
    const line1 = createLogLine('tag-host', 'AI-HOST', `-> Sending JSON-RPC call: tools/call ("${data.request.params.name}")`);
    terminalBody.appendChild(line1);

    setTimeout(() => {
      // 2. Stderr diagnostic log (Clean isolation)
      if (stdoutIsolationEnabled) {
        const line2 = createLogLine('tag-stderr', 'STDERR', data.stderr);
        terminalBody.appendChild(line2);
      } else {
        // Simulating the disastrous failure when stdout is poisoned
        const corruptedLine = createLogLine('tag-error', 'STDOUT CORRUPT', `[FATAL] print() leaked into stdout: "Connected to database..."`);
        const crashLine = createLogLine('tag-error', 'AI-HOST CRASH', `Client parse failure: SyntaxError: Unexpected token 'C' in JSON at position 0`);
        terminalBody.appendChild(corruptedLine);
        terminalBody.appendChild(crashLine);
        latencyDisplay.textContent = 'CONNECTION DROPPED';
        latencyDisplay.style.color = 'var(--color-rose)';
        return;
      }

      setTimeout(() => {
        // 3. Pristine JSON-RPC stdout frame
        const line3 = createLogLine('tag-stdout', 'STDOUT-RPC', '');
        const pre = document.createElement('pre');
        pre.textContent = JSON.stringify(data.response, null, 2);
        line3.querySelector('.log-content').appendChild(pre);
        terminalBody.appendChild(line3);

        latencyDisplay.textContent = data.latency;
        latencyDisplay.style.color = 'var(--color-emerald)';
        terminalBody.scrollTop = terminalBody.scrollHeight;
      }, 150);
    }, 150);
  }

  function createLogLine(tagClass, tagText, contentText) {
    const div = document.createElement('div');
    div.className = 'log-line';
    div.innerHTML = `<span class="log-tag ${tagClass}">${tagText}</span><span class="log-content">${escapeHTML(contentText)}</span>`;
    return div;
  }

  function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, tag => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      "'": '&#39;',
      '"': '&quot;'
    }[tag] || tag));
  }

  // Bind Buttons
  if (queryBtn1) queryBtn1.addEventListener('click', () => executeSimulation('server-01'));
  if (queryBtn2) queryBtn2.addEventListener('click', () => executeSimulation('server-02'));
  if (injectBtn) injectBtn.addEventListener('click', () => executeSimulation('injection'));

  if (stdoutToggle) {
    stdoutToggle.addEventListener('click', () => {
      stdoutIsolationEnabled = !stdoutIsolationEnabled;
      if (stdoutIsolationEnabled) {
        stdoutToggle.textContent = 'Stdout Isolation: ON (Guaranteed)';
        stdoutToggle.classList.add('active');
        executeSimulation('server-01');
      } else {
        stdoutToggle.textContent = 'Stdout Isolation: OFF (Simulate Crash)';
        stdoutToggle.classList.remove('active');
        executeSimulation('server-01');
      }
    });
  }

  // Initial execution
  executeSimulation('server-01');
}

/* ==========================================================================
   2. Multi-Host Profile Switcher
   ========================================================================== */
function initHostProfileSwitcher() {
  const hostConfigs = {
    antigravity: {
      title: "Google Antigravity IDE & 2.0 (.agents/mcp_config.json)",
      snippet: `{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": [
        "run",
        "server.py"
      ],
      "env": {
        "LOG_LEVEL": "INFO"
      }
    }
  }
}`
    },
    cursor: {
      title: "Cursor IDE (.cursor/mcp.json)",
      snippet: `{
  "mcpServers": {
    "enterprise-asset-os": {
      "command": "uv",
      "args": [
        "run",
        "server.py"
      ]
    }
  }
}`
    },
    vscode: {
      title: "Visual Studio Code (.vscode/mcp.json)",
      snippet: `{
  "servers": {
    "enterprise-asset-os": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "server.py"
      ]
    }
  }
}`
    },
    claude: {
      title: "Claude Desktop (claude_desktop_config.json)",
      snippet: `{
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
}`
    },
    windsurf: {
      title: "Windsurf (windsurf_config.json)",
      snippet: `{
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
}`
    },
    docker: {
      title: "Docker Streamable HTTP Microservice (Dockerfile / Cloud Run)",
      snippet: `# Build and run horizontally scalable MCP microservice
docker build -t enterprise-asset-os .
docker run -p 8000:8000 -e MCP_TRANSPORT=http enterprise-asset-os

# Connect from remote AI hosts via Streamable HTTP
# endpoint: http://localhost:8000/mcp (Stateless 2026-07-28)`
    }
  };

  const tabs = document.querySelectorAll('.host-tab-btn');
  const codeBlock = document.getElementById('host-code-display');

  if (!tabs.length || !codeBlock) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.getAttribute('data-host');
      if (hostConfigs[target]) {
        codeBlock.textContent = hostConfigs[target].snippet;
      }
    });
  });
}

/* ==========================================================================
   3. Accessible FAQ Accordion
   ========================================================================== */
function initFaqAccordion() {
  const triggers = document.querySelectorAll('.faq-trigger');

  triggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.faq-item');
      const content = item.querySelector('.faq-content');
      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

      // Close all other accordions for clean single disclosure
      document.querySelectorAll('.faq-item').forEach(other => {
        if (other !== item) {
          other.classList.remove('active');
          const otherTrigger = other.querySelector('.faq-trigger');
          const otherContent = other.querySelector('.faq-content');
          if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
          if (otherContent) otherContent.style.maxHeight = null;
        }
      });

      if (isExpanded) {
        item.classList.remove('active');
        trigger.setAttribute('aria-expanded', 'false');
        content.style.maxHeight = null;
      } else {
        item.classList.add('active');
        trigger.setAttribute('aria-expanded', 'true');
        content.style.maxHeight = content.scrollHeight + 'px';
      }
    });
  });
}

/* ==========================================================================
   4. One-Click Copy & Toast System
   ========================================================================== */
function initClipboardHandlers() {
  const copyBtn = document.getElementById('copy-host-btn');
  const codeBlock = document.getElementById('host-code-display');
  const toast = document.getElementById('toast-notification');

  if (!copyBtn || !codeBlock || !toast) return;

  copyBtn.addEventListener('click', async () => {
    const text = codeBlock.textContent;
    try {
      await navigator.clipboard.writeText(text);
      showToast('Configuration copied to clipboard!');
    } catch (err) {
      // Fallback
      const textArea = document.createElement('textarea');
      textArea.value = text;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      showToast('Configuration copied to clipboard!');
    }
  });

  function showToast(message) {
    toast.querySelector('.toast-text').textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 2800);
  }
}
