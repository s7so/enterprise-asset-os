import json
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from mcp.shared.exceptions import MCPError
from server import mcp, ASSET_DB


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
            await client.call_tool("query_telemetry", {"asset_id": "unknown-99"})
        assert "not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_primitives_registered():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        prompts = await client.list_prompts()
        resources = await client.list_resource_templates()

        assert any(t.name == "query_telemetry" for t in tools)
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
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": "High CPU alert"})
        assert len(prompt.messages) > 0
        assert "High CPU alert" in prompt.messages[0].content.text


@pytest.mark.asyncio
async def test_security_input_sanitization():
    async with Client(mcp) as client:
        # Whitespace and case normalization
        result = await client.call_tool("query_telemetry", {"asset_id": "  SERVER-01  "})
        assert result.data["asset_id"] == "server-01"

        # Injection attempt safely rejected
        with pytest.raises(ToolError):
            await client.call_tool("query_telemetry", {"asset_id": "server-01' OR '1'='1"})


@pytest.mark.asyncio
async def test_security_resource_boundary():
    async with Client(mcp) as client:
        # FastMCP 4 built-in resource security rejects path traversal
        with pytest.raises(MCPError):
            await client.read_resource("config://schemas/../../etc/passwd")

        # Unknown schema returns controlled error payload
        resource = await client.read_resource("config://schemas/unknown_type")
        payload = json.loads(resource[0].text)
        assert "error" in payload


@pytest.mark.asyncio
async def test_security_tool_annotations():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        telemetry_tool = next(t for t in tools if t.name == "query_telemetry")
        assert telemetry_tool.annotations.read_only_hint is True
        assert telemetry_tool.annotations.idempotent_hint is True
        assert telemetry_tool.annotations.open_world_hint is False
