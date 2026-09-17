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

- **أداة (Tool)**: `query_telemetry` — استعلام عن قياسات وحالة خوادم البنية التحتية مع دعم وسوم الأمان (`readOnlyHint`, `idempotentHint`).
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
```bash
$env:MCP_TRANSPORT="http"
$env:PORT="8000"
uv run server.py
```

### تشغيل الاختبارات المؤتمتة
```bash
uv run pytest -q
```

## الإعداد والربط مع بيئات الذكاء الاصطناعي (AI Hosts)

تتوفر ملفات الإعداد الجاهزة في المجلد `configs/`:
- **Claude Desktop**: انسخ محتوى الملف `configs/claude_desktop_config.json` إلى مسار إعدادات كلود.
- **Cursor IDE**: تم إعداد الملف مسبقاً في مسار المشروع `.cursor/mcp.json`.
- **VS Code**: تم إعداد الملف مسبقاً في مسار المشروع `.vscode/mcp.json`.
- **Windsurf**: انسخ محتوى `configs/windsurf_config.json`.
- **Antigravity IDE & 2.0**: تم إعداد الملف مسبقاً في مسار المشروع [`.agents/mcp_config.json`](.agents/mcp_config.json) للاكتشاف التلقائي الفوري، أو عبر الإعداد العام `~/.gemini/config/mcp_config.json` وفق التوثيق الرسمي ([antigravity.google/docs/mcp](https://antigravity.google/docs/mcp)).

## النشر بواسطة حاويات Docker
```bash
docker build -t enterprise-asset-os .
docker run -p 8000:8000 -e MCP_TRANSPORT=http enterprise-asset-os
```
