import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.shared.exceptions import MCPError
from server import mcp


@pytest.mark.asyncio
async def test_query_telemetry_success():
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "server-01"})
        assert result.data["asset_id"] == "server-01"
        assert result.data["telemetry"]["status"] == "active"


@pytest.mark.asyncio
async def test_query_telemetry_not_found():
    async with Client(mcp) as client:
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("query_telemetry", {"asset_id": "server-99"})
        assert "not found" in str(exc_info.value)
        # Verify topology disclosure prevention: valid IDs must not be leaked
        assert "server-01" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_primitives_registered():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        resources = await client.list_resource_templates()

        assert any(t.name == "query_telemetry" for t in tools)
        assert any(t.name == "query_store_inventory" for t in tools)
        assert any(p.name == "incident_triage_prompt" for p in prompts)
        assert any(r.uri_template == "config://schemas/{schema_type}" for r in resources)


@pytest.mark.asyncio
async def test_read_resource():
    async with Client(mcp) as client:
        resource = await client.read_resource("config://schemas/compute")
        assert "vcpus" in resource[0].text


@pytest.mark.asyncio
async def test_get_prompt():
    async with Client(mcp) as client:
        prompt = await client.get_prompt(
            "incident_triage_prompt", {"incident_log": "High CPU alert on node 1"}
        )
        assert len(prompt.messages) > 0
        assert "High CPU alert on node 1" in prompt.messages[0].content.text


@pytest.mark.asyncio
async def test_prompt_validation_bounds():
    async with Client(mcp) as client:
        with pytest.raises(MCPError):
            await client.get_prompt("incident_triage_prompt", {"incident_log": "   "})

        oversized_log = "x" * 40000
        with pytest.raises(MCPError):
            await client.get_prompt("incident_triage_prompt", {"incident_log": oversized_log})


@pytest.mark.asyncio
async def test_security_input_validation():
    async with Client(mcp) as client:
        # Whitespace and case normalization on valid asset IDs
        result = await client.call_tool("query_telemetry", {"asset_id": "  SERVER-01  "})
        assert result.data["asset_id"] == "server-01"

        # Injection attempt rejected by format regex validator
        with pytest.raises(ToolError) as exc_info:
            await client.call_tool("query_telemetry", {"asset_id": "server-01' OR '1'='1"})
        assert "Invalid asset ID format" in str(exc_info.value)

        # Empty and path traversal format rejected
        with pytest.raises(ToolError):
            await client.call_tool("query_telemetry", {"asset_id": "../etc/passwd"})


@pytest.mark.asyncio
async def test_security_resource_boundary():
    async with Client(mcp) as client:
        # FastMCP built-in resource security rejects path traversal
        with pytest.raises(MCPError):
            await client.read_resource("config://schemas/../../etc/passwd")

        # Unknown schema raises proper protocol-level error instead of swallowing into 200 OK
        with pytest.raises(MCPError):
            await client.read_resource("config://schemas/unknown_type")


@pytest.mark.asyncio
async def test_security_tool_annotations():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        telemetry_tool = next(t for t in tools if t.name == "query_telemetry")
        assert telemetry_tool.annotations.read_only_hint is True
        assert telemetry_tool.annotations.idempotent_hint is True
        assert telemetry_tool.annotations.open_world_hint is False

        store_tool = next(t for t in tools if t.name == "query_store_inventory")
        assert store_tool.annotations.read_only_hint is True
        assert store_tool.annotations.idempotent_hint is True

        unpaid_tool = next(t for t in tools if t.name == "get_unpaid_invoices")
        assert unpaid_tool.annotations.read_only_hint is True
        assert unpaid_tool.annotations.idempotent_hint is True

        cash_tool = next(t for t in tools if t.name == "get_cash_flow_summary")
        assert cash_tool.annotations.read_only_hint is True
        assert cash_tool.annotations.idempotent_hint is True


@pytest.mark.asyncio
async def test_query_store_inventory_low_stock():
    """Verify query_store_inventory correctly flags low-stock items under threshold."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_store_inventory", {"max_stock_threshold": 10})
        data = result.data
        assert data["status"] == "success"
        assert data["threshold_applied"] == 10
        assert isinstance(data["replenishment_needed"], list)
        for item in data["replenishment_needed"]:
            assert item["current_stock"] <= 10
            assert "title" in item
            assert item["urgency"] in ("CRITICAL", "WARNING")


@pytest.mark.asyncio
async def test_query_store_inventory_with_category():
    """Verify query_store_inventory filters by category properly."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_store_inventory", {"category": "groceries", "max_stock_threshold": 20})
        data = result.data
        assert data["status"] == "success"
        for item in data["replenishment_needed"]:
            assert "groceries" in item["category"].lower()


@pytest.mark.asyncio
async def test_get_unpaid_invoices_all():
    """Verify get_unpaid_invoices returns pending invoices with complete aging attributes."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_unpaid_invoices", {})
        data = result.data
        assert data["status"] == "success"
        assert data["total_unpaid_found"] > 0
        assert len(data["invoices"]) <= 10
        for inv in data["invoices"]:
            assert "invoice_number" in inv
            assert "client_name" in inv
            assert inv["amount_due"] > 0
            assert "days_overdue" in inv
            assert inv["urgency"] in ("CRITICAL", "WARNING", "ATTENTION", "CURRENT")


@pytest.mark.asyncio
async def test_get_unpaid_invoices_overdue_filter():
    """Verify get_unpaid_invoices correctly isolates accounts overdue >= 30 days."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_unpaid_invoices", {"min_days_overdue": 30, "limit": 20})
        data = result.data
        assert data["status"] == "success"
        assert len(data["invoices"]) > 0
        for inv in data["invoices"]:
            assert inv["days_overdue"] >= 30


@pytest.mark.asyncio
async def test_get_unpaid_invoices_client_filter():
    """Verify get_unpaid_invoices filters accurately by client substring."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_unpaid_invoices", {"client_name": "الأهرام"})
        data = result.data
        assert data["status"] == "success"
        assert len(data["invoices"]) > 0
        for inv in data["invoices"]:
            assert "الأهرام" in inv["client_name"]


@pytest.mark.asyncio
async def test_get_cash_flow_summary_egp():
    """Verify get_cash_flow_summary aggregates receivables, aging buckets, and top debtors for EGP."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_cash_flow_summary", {"currency": "EGP"})
        data = result.data
        assert data["status"] == "success"
        assert data["currency"] == "EGP"
        assert data["total_invoiced"] > 0
        assert data["total_receivables_outstanding"] > 0
        assert "aging_buckets" in data
        assert "current_0_to_30_days" in data["aging_buckets"]
        assert "overdue_over_90_days" in data["aging_buckets"]
        assert len(data["top_5_debtor_clients"]) <= 5
        assert data["portfolio_health"]["status"] in ("HEALTHY", "MODERATE_WARNING", "HIGH_RISK")


@pytest.mark.asyncio
async def test_get_cash_flow_summary_usd():
    """Verify get_cash_flow_summary computes currency-segregated figures for USD transactions."""
    async with Client(mcp) as client:
        result = await client.call_tool("get_cash_flow_summary", {"currency": "USD"})
        data = result.data
        assert data["status"] == "success"
        assert data["currency"] == "USD"
        assert data["total_receivables_outstanding"] > 0


