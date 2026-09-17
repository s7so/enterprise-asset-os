# نظام Enterprise Asset OS — خادم بروتوكول سياق النموذج (MCP)

دليل التشغيل والاستخدام العربي لخادم بروتوكول سياق النموذج (MCP Server) المبني وفق معايير **FastMCP 4** و **MCP Python SDK v2** والمتوافق بالكامل مع مواصفة **2026-07-28**.

## بنية النظام والمميزات الأساسية

1. **بروتوكول عديم الحالة (Stateless Protocol)**:
   - تم إلغاء خطوة المصافحة الأولية (`initialize handshake`) بالكامل.
   - لا يتم استخدام معرفات الجلسات (`Mcp-Session-Id`).
   - كل طلب يحمل بيانات التعريف وقدرات العميل في الحقل `_meta`.

2. **عزل المخرجات القياسية (Stdout Isolation)**:
   - القناة القياسية `stdout` مخصصة حصرياً لرسائل JSON-RPC 2.0 المشفرة بـ UTF-8 ومفصولة بأسطر جديدة.
   - جميع سجلات التشخيص ومعلومات السجلات (`logs`) توجه حصراً إلى `stderr` لتفادي انهيار اتصال العميل.

3. **وسائط النقل الثنائية (Dual Wire Transports)**:
   - **stdio**: التشغيل المحلي الافتراضي لبيئات التطوير مثل Cursor و Claude Desktop و VS Code و Windsurf و Antigravity.
   - **Streamable HTTP**: التشغيل الموزع عبر الشبكة السحابية خلف موزعات الأحمال (Load Balancers) دون اشتراط استمرارية الجلسة (Session Affinity).

## مكونات البروتوكول المتاحة
- **أداة الاستعلام عن البنية التحتية (Tool)**: `query_telemetry` — استعلام عن قياسات وحالة خوادم البنية التحتية مع دعم وسوم الأمان (`readOnlyHint`, `idempotentHint`).
- **أداة تدقيق مخزون المتاجر (Tool)**: `query_store_inventory` — فحص منتجات المتجر واكتشاف النواقص والمستويات الحرجة مع دعم السقوط الاحتياطي دون انقطاع.
- **أداة تدقيق الفواتير غير المسددة (Tool)**: `get_unpaid_invoices` — فحص ديون وفواتير العملاء المتأخرة لنظم الـ ERP (أودو / دفترة) مع تصنيف التأخير (30+، 60+، 90+ يوماً).
- **أداة ملخص التدفق النقدي والمقبوضات (Tool)**: `get_cash_flow_summary` — تحليل فوري لحجم المبيعات والتحصيلات وأكبر 5 عملاء مدينين ومؤشر صحة التدفق النقدي.
- **مورد (Resource)**: `config://schemas/{schema_type}` — قراءة مواصفات ومخططات الإعدادات بصيغة JSON مع الحماية من هجمات تخطي المسار (Path Traversal).
- **موجه (Prompt)**: `incident_triage_prompt` — قالب تشخيصي متقدم لتحليل سجلات الأعطال وتقديم خطط الإصلاح لمهندسي استقرار الأنظمة (SRE).


## التشغيل السريع

### المتطلبات الأساسية
- بيئة بايثون الإصدار 3.10 فأحدث.
- أداة إدارة الحزم Astral `uv` الإصدار 0.12 فأحدث.

### التشغيل المحلي (stdio)
```bash
uv run server.py
```

### التشغيل كخدمة شبكية (HTTP)
- **أنظمة Linux / macOS (Bash):**
```bash
export MCP_TRANSPORT=http
export PORT=8000
uv run server.py
```
- **أنظمة Windows (PowerShell):**
```powershell
$env:MCP_TRANSPORT="http"
$env:PORT="8000"
uv run server.py
```

### تشغيل الاختبارات المؤتمتة ومنظومة التحقق
```bash
# 1. الاختبارات المعزولة الافتراضية (19 اختباراً تعمل 100% offline ببيانات synthetic بصيغ إنتاجية):
uv run pytest -v

# 2. جلب بيانات أبحاث Loghub والتحقق من الهاشات المشفرة (اختياري للأبحاث والتقييم):
uv run tests/data/fetch_real_fixtures.py

# 3. تشغيل كامل الاختبارات مع بيانات Loghub (24 اختباراً شاملاً):
# Linux / macOS:
RUN_REAL_DATA=1 uv run pytest -v
# Windows (PowerShell):
$env:RUN_REAL_DATA="1"; uv run pytest -v
```

## الإعداد والربط مع بيئات الذكاء الاصطناعي (8 بيئات معتمدة)

تتوفر ملفات الإعداد الجاهزة في المجلد `configs/`:
- **Claude Desktop**: انسخ محتوى الملف `configs/claude_desktop_config.json` إلى مسار إعدادات كلود.
- **Cursor IDE**: تم إعداد الملف مسبقاً في مسار المشروع `.cursor/mcp.json`.
- **VS Code**: تم إعداد الملف مسبقاً في مسار المشروع `.vscode/mcp.json`.
- **Windsurf**: انسخ محتوى `configs/windsurf_config.json`.
- **Antigravity IDE & 2.0**: تم إعداد الملف مسبقاً في مسار المشروع [`.agents/mcp_config.json`](.agents/mcp_config.json) للاكتشاف التلقائي الفوري، أو عبر الإعداد العام `~/.gemini/config/mcp_config.json` وفق التوثيق الرسمي ([antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)).
- **Claude Code CLI**: ربط فوري عبر الأمر المباشر `claude mcp add`.
- **ChatGPT (OpenAI Developer Mode)**: تفعيل عبر وضع المطورين وربط الرابط السحابي `configs/chatgpt_config.json`.
- **Grok (xAI Connectors & CLI)**: ربط مباشر عبر `grok.com/connectors` أو ملف الإعداد `configs/grok_config.toml`.

## دليل التطوير وربط البيانات الحقيقية
لربط الخادم بقواعد بيانات حقيقية (PostgreSQL عبر `asyncpg`، أو Redis، أو واجهات REST السحابية)، يرجى مراجعة [دليل التطوير والامتداد (`EXTENDING.md`)](EXTENDING.md).

## النشر بواسطة حاويات Docker
```bash
docker build -t enterprise-asset-os .
docker run -p 8000:8000 -e MCP_TRANSPORT=http enterprise-asset-os
```

## الترخيص التجاري
المنتج محمي بترخيص تجاري رسمي، راجع ملف [`LICENSE`](LICENSE) لمعرفة كافة الحقوق وشروط الاستخدام.
