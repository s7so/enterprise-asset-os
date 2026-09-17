/**
 * البرمجة بالبلدي (Programming Bel-Balady)
 * المنطق التفاعلي لنظام Enterprise Asset OS
 * النمط النيو-بروتاليست الحيوي عالي الطاقة
 */

document.addEventListener('DOMContentLoaded', () => {
  initTerminalSimulator();
  initHostProfileSwitcher();
  initFaqAccordion();
  initClipboardHandlers();
  initMobileMenu();
});

/* ==========================================================================
   1. وحدة محاكاة بروتوكول MCP الحية التفاعلية
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
  let activeTimers = [];

  function clearPendingTimers() {
    activeTimers.forEach(id => clearTimeout(id));
    activeTimers = [];
  }

  const sampleResponses = {
    'server-01': {
      request: { jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-01" } } },
      stderr: "[2026-09-17 14:30:12] INFO [BelBaladyMCP]: استدعاء query_telemetry للأصل server-01",
      response: {
        jsonrpc: "2.0",
        id: 1,
        result: {
          content: [{ type: "text", text: JSON.stringify({ asset_id: "server-01", telemetry: { status: "active", load_pct: 34.5, region: "me-central-1" } }, null, 2) }]
        }
      },
      latency: "14ms"
    },
    'server-02': {
      request: { jsonrpc: "2.0", id: 2, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-02" } } },
      stderr: "[2026-09-17 14:30:15] INFO [BelBaladyMCP]: استدعاء query_telemetry للأصل server-02",
      response: {
        jsonrpc: "2.0",
        id: 2,
        result: {
          content: [{ type: "text", text: JSON.stringify({ asset_id: "server-02", telemetry: { status: "degraded", load_pct: 89.2, region: "me-central-1" } }, null, 2) }]
        }
      },
      latency: "18ms"
    },
    'injection': {
      request: { jsonrpc: "2.0", id: 3, method: "tools/call", params: { name: "query_telemetry", arguments: { asset_id: "server-01' OR '1'='1" } } },
      stderr: "[2026-09-17 14:30:20] WARNING [BelBaladyMCP]: تم رفض المدخل الأمني غير المطابق: server-01' OR '1'='1",
      response: {
        jsonrpc: "2.0",
        id: 3,
        result: {
          isError: true,
          content: [{
            type: "text",
            text: "ToolError: Invalid asset ID format: 'server-01\\' OR \\'1\\'=\\'1'. Must be 2-64 lowercase alphanumeric characters or hyphens."
          }]
        }
      },
      latency: "9ms"
    }
  };

  function updateActiveButton(activeBtn) {
    [queryBtn1, queryBtn2, injectBtn].forEach(btn => {
      if (!btn) return;
      if (btn === activeBtn) {
        btn.classList.add('bg-[#FFE600]', 'text-black', 'shadow-[2px_2px_0px_0px_#000]', 'translate-x-[2px]', 'translate-y-[2px]');
        btn.classList.remove('bg-white', 'text-slate-800', 'shadow-[4px_4px_0px_0px_#000]', 'translate-x-0', 'translate-y-0');
      } else {
        btn.classList.remove('bg-[#FFE600]', 'text-black', 'shadow-[2px_2px_0px_0px_#000]', 'translate-x-[2px]', 'translate-y-[2px]');
        btn.classList.add('bg-white', 'text-slate-800', 'shadow-[4px_4px_0px_0px_#000]', 'translate-x-0', 'translate-y-0');
      }
    });
  }

  function executeSimulation(key, sourceBtn) {
    const data = sampleResponses[key];
    if (!data) return;

    if (sourceBtn) updateActiveButton(sourceBtn);

    clearPendingTimers();
    terminalBody.innerHTML = '';
    latencyDisplay.textContent = 'جاري التنفيذ...';
    latencyDisplay.className = 'px-2.5 py-0.5 rounded bg-yellow-300 border-2 border-black text-black font-black text-xs font-mono';

    // 1. Host call line
    const line1 = createLogLine(
      'bg-[#00C2FF] text-black border-2 border-black font-black',
      'AI-HOST',
      `← إرسال نداء JSON-RPC معتمد: tools/call ("${data.request.params.name}")`
    );
    terminalBody.appendChild(line1);

    const timer1 = setTimeout(() => {
      // 2. Stderr diagnostic log (Clean isolation)
      if (stdoutIsolationEnabled) {
        const line2 = createLogLine(
          'bg-[#FFE600] text-black border-2 border-black font-black',
          'STDERR سجلات',
          data.stderr
        );
        terminalBody.appendChild(line2);
      } else {
        // Simulating the disastrous failure when stdout is poisoned
        const corruptedLine = createLogLine(
          'bg-[#FF007A] text-white border-2 border-black font-black',
          'تلوث STDOUT',
          `[خطأ فادح] تسريب أمر print() في مخرج البيانات: "Connected to database..."`
        );
        const crashLine = createLogLine(
          'bg-black text-[#FF007A] border-2 border-[#FF007A] font-black',
          'انهيار العميل',
          `فشل تحليل البيانات: SyntaxError: Unexpected token 'C' in JSON at position 0`
        );
        terminalBody.appendChild(corruptedLine);
        terminalBody.appendChild(crashLine);
        latencyDisplay.textContent = 'انقطع الاتصال (انهيار)';
        latencyDisplay.className = 'px-2.5 py-0.5 rounded bg-[#FF007A] border-2 border-black text-white font-black text-xs font-mono animate-bounce';
        return;
      }

      const timer2 = setTimeout(() => {
        // 3. Pristine JSON-RPC stdout frame
        const line3 = document.createElement('div');
        line3.className = 'flex flex-col gap-2 py-2 font-mono text-xs';
        line3.innerHTML = `
          <div class="flex items-center gap-2">
            <span class="px-2.5 py-0.5 rounded-md text-[11px] font-black tracking-wider bg-[#00F59B] text-black border-2 border-black">STDOUT-RPC</span>
            <span class="text-slate-800 font-bold text-xs">إطار استجابة JSON-RPC 2.0 سليم ونقي بنسبة 100%</span>
          </div>
          <pre class="p-3.5 mt-1 rounded-xl bg-slate-900 border-3 border-black text-emerald-300 overflow-x-auto text-xs leading-relaxed font-mono shadow-[4px_4px_0px_0px_#000]" dir="ltr">${escapeHTML(JSON.stringify(data.response, null, 2))}</pre>
        `;
        terminalBody.appendChild(line3);

        latencyDisplay.textContent = `السرعة: ${data.latency}`;
        latencyDisplay.className = 'px-2.5 py-0.5 rounded bg-[#00F59B] border-2 border-black text-black font-black text-xs font-mono';
        terminalBody.scrollTop = terminalBody.scrollHeight;
      }, 150);
      activeTimers.push(timer2);
    }, 150);
    activeTimers.push(timer1);
  }

  function createLogLine(badgeClasses, tagText, contentText) {
    const div = document.createElement('div');
    div.className = 'flex items-start gap-2.5 py-1 text-xs font-mono';
    div.innerHTML = `
      <span class="shrink-0 px-2 py-0.5 rounded-md text-[11px] tracking-wider ${badgeClasses}">${tagText}</span>
      <span class="text-slate-900 font-bold break-all leading-normal py-0.5">${escapeHTML(contentText)}</span>
    `;
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

  // Bind simulation buttons
  if (queryBtn1) queryBtn1.addEventListener('click', () => executeSimulation('server-01', queryBtn1));
  if (queryBtn2) queryBtn2.addEventListener('click', () => executeSimulation('server-02', queryBtn2));
  if (injectBtn) injectBtn.addEventListener('click', () => executeSimulation('injection', injectBtn));

  if (stdoutToggle) {
    stdoutToggle.addEventListener('click', () => {
      stdoutIsolationEnabled = !stdoutIsolationEnabled;
      if (stdoutIsolationEnabled) {
        stdoutToggle.textContent = 'عزل مخرجات Stdout: مفعل (مضمون 100%)';
        stdoutToggle.className = 'px-3 py-1.5 rounded-xl text-xs font-black border-2 border-black transition-all bg-[#00F59B] text-black shadow-[3px_3px_0px_0px_#000] hover:translate-x-0.5 hover:translate-y-0.5';
        executeSimulation('server-01', queryBtn1);
      } else {
        stdoutToggle.textContent = 'عزل مخرجات Stdout: معطل (محاكاة الانهيار)';
        stdoutToggle.className = 'px-3 py-1.5 rounded-xl text-xs font-black border-2 border-black transition-all bg-[#FF007A] text-white shadow-[3px_3px_0px_0px_#000] hover:translate-x-0.5 hover:translate-y-0.5 animate-pulse';
        executeSimulation('server-01', queryBtn1);
      }
    });
  }

  // Initial trigger
  executeSimulation('server-01', queryBtn1);
}

/* ==========================================================================
   2. محول إعدادات منصات الذكاء الاصطناعي الست
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
      snippet: `# بناء وتشغيل حاوية خادم MCP القابلة للتوسع سحابياً
docker build -t enterprise-asset-os .
docker run -p 8000:8000 -e MCP_TRANSPORT=http enterprise-asset-os

# الاتصال من عملاء الذكاء الاصطناعي عبر بروتوكول HTTP الانسيابي
# endpoint: http://localhost:8000/mcp (Stateless 2026-07-28)`
    },
    chatgpt: {
      title: "ChatGPT Developer Mode (Streamable HTTP / Remote MCP)",
      snippet: `# 1. تشغيل الخادم بنمط HTTP لنقل البيانات الانسيابي:
MCP_TRANSPORT=http PORT=8000 uv run server.py

# 2. إنشاء نفق عام (Tunnel) للاختبار المحلي عبر ngrok أو cloudflared:
ngrok http 8000

# 3. في واجهة شات جي بي تي (ChatGPT):
# الإعدادات (Settings) > الأمان وتسجيل الدخول > تفعيل وضع المطورين (Developer Mode)
# أضف رابط خادم MCP الجديد:
https://<your-subdomain>.ngrok-free.app/mcp

# المصدر الرسمي المعتمد لعام 2026:
# OpenAI Developer Platform — Model Context Protocol in ChatGPT`
    },
    grok: {
      title: "xAI Grok Connectors & CLI (~/.grok/config.toml)",
      snippet: `# 1. الربط عبر واجهة ويب Grok Connectors:
# افتح الرابط: https://grok.com/connectors
# اضغط "Add Custom MCP Connector" ثم ضع رابط الخادم:
https://<your-server-domain-or-tunnel>/mcp

# 2. أو الربط الفوري عبر موجه أوامر Grok CLI:
grok mcp add enterprise-asset-os https://<your-server-domain-or-tunnel>/mcp

# 3. أو عبر ملف الإعداد المحلي (~/.grok/config.toml):
[mcp_servers.enterprise_asset_os]
name = "enterprise-asset-os"
transport = "http"
url = "https://<your-server-domain-or-tunnel>/mcp"
timeout = 30

# المصدر الرسمي المعتمد لعام 2026:
# xAI Developer Documentation (docs.x.ai) — Remote MCP Tools Specification`
    }
  };

  const tabs = document.querySelectorAll('.host-tab-btn');
  const codeBlock = document.getElementById('host-code-display');

  if (!tabs.length || !codeBlock) return;

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('bg-[#00C2FF]', 'text-black', 'shadow-[2px_2px_0px_0px_#000]', 'translate-x-0.5', 'translate-y-0.5');
        t.classList.add('bg-white', 'text-black', 'shadow-[4px_4px_0px_0px_#000]');
        t.setAttribute('aria-selected', 'false');
      });

      tab.classList.remove('bg-white', 'shadow-[4px_4px_0px_0px_#000]');
      tab.classList.add('bg-[#00C2FF]', 'text-black', 'shadow-[2px_2px_0px_0px_#000]', 'translate-x-0.5', 'translate-y-0.5');
      tab.setAttribute('aria-selected', 'true');

      const target = tab.getAttribute('data-host');
      if (hostConfigs[target]) {
        codeBlock.textContent = hostConfigs[target].snippet;
      }
    });
  });
}

/* ==========================================================================
   3. أكورديون الأسئلة الشائعة
   ========================================================================== */
function initFaqAccordion() {
  const triggers = document.querySelectorAll('.faq-trigger');

  triggers.forEach(trigger => {
    trigger.addEventListener('click', () => {
      const item = trigger.closest('.faq-item');
      const content = item.querySelector('.faq-content');
      const icon = trigger.querySelector('.faq-icon');
      const isExpanded = trigger.getAttribute('aria-expanded') === 'true';

      // Close all other accordions for single disclosure
      document.querySelectorAll('.faq-item').forEach(other => {
        if (other !== item) {
          const otherTrigger = other.querySelector('.faq-trigger');
          const otherContent = other.querySelector('.faq-content');
          const otherIcon = other.querySelector('.faq-icon');
          if (otherTrigger) otherTrigger.setAttribute('aria-expanded', 'false');
          if (otherContent) otherContent.classList.add('hidden');
          if (otherIcon) otherIcon.style.transform = 'rotate(0deg)';
        }
      });

      if (isExpanded) {
        trigger.setAttribute('aria-expanded', 'false');
        content.classList.add('hidden');
        if (icon) icon.style.transform = 'rotate(0deg)';
      } else {
        trigger.setAttribute('aria-expanded', 'true');
        content.classList.remove('hidden');
        if (icon) icon.style.transform = 'rotate(180deg)';
      }
    });
  });
}

/* ==========================================================================
   4. نظام نسخ الإعدادات والتنبيه التفاعلي
   ========================================================================== */
function initClipboardHandlers() {
  const copyBtn = document.getElementById('copy-host-btn');
  const codeBlock = document.getElementById('host-code-display');
  const toast = document.getElementById('toast-notification');

  if (!copyBtn || !codeBlock || !toast) return;

  copyBtn.addEventListener('click', async () => {
    const text = codeBlock.textContent;
    let copied = false;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      try {
        await navigator.clipboard.writeText(text);
        copied = true;
      } catch {
        copied = false;
      }
    }

    if (!copied) {
      try {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        copied = document.execCommand('copy');
        document.body.removeChild(textArea);
      } catch {
        copied = false;
      }
    }

    if (copied) {
      showToast('★ تم نسخ الإعدادات بنجاح للحافظة! جاهز للتشغيل مباشرة في بيئتك');
    } else {
      showToast('تعذر النسخ التلقائي. يرجى تحديد النص ونسخه يدوياً.');
    }
  });

  function showToast(message) {
    const toastText = toast.querySelector('.toast-text');
    if (toastText) toastText.textContent = message;
    toast.classList.remove('opacity-0', 'translate-y-6', 'pointer-events-none');
    toast.classList.add('opacity-100', 'translate-y-0');

    setTimeout(() => {
      toast.classList.add('opacity-0', 'translate-y-6', 'pointer-events-none');
      toast.classList.remove('opacity-100', 'translate-y-0');
    }, 2800);
  }
}

/* ==========================================================================
   5. القائمة المنسدلة للشاشات الصغيرة
   ========================================================================== */
function initMobileMenu() {
  const toggleBtn = document.getElementById('mobile-menu-btn');
  const menu = document.getElementById('mobile-menu');

  if (!toggleBtn || !menu) return;

  toggleBtn.addEventListener('click', () => {
    const isOpen = !menu.classList.contains('hidden');
    if (isOpen) {
      menu.classList.add('hidden');
      toggleBtn.setAttribute('aria-expanded', 'false');
    } else {
      menu.classList.remove('hidden');
      toggleBtn.setAttribute('aria-expanded', 'true');
    }
  });

  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', () => {
      menu.classList.add('hidden');
      toggleBtn.setAttribute('aria-expanded', 'false');
    });
  });
}
