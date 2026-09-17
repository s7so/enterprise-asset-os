"""
Fetch-on-Demand Script for Research-Licensed Loghub Benchmarks
Downloads canonical log samples from upstream, verifies cryptographic SHA-256 pins,
extracts documented line-slices, and regenerates real fixtures locally.

NOTICE: This script must be run explicitly by researchers/developers who have reviewed
and accepted the research/academic terms of the Loghub datasets.
Canonical source repository: https://github.com/logpai/loghub
"""
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

PINNED_SOURCES = {
    "Linux_2k.log": {
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/Linux/Linux_2k.log",
        "sha256": "b3e20bc1afe732ab1bf3ed1de4bf9c809e4194e02f7dea911d918e5342e8e173",
        "expected_bytes": 216485,
    },
    "OpenStack_2k.log": {
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/OpenStack/OpenStack_2k.log",
        "sha256": "025a1bc64ff5b2ef4a4bda6c4ad5c5c5f18478b71cd1ad2b0676e01625629f2f",
        "expected_bytes": 595119,
    },
    "HDFS_2k.log": {
        "url": "https://raw.githubusercontent.com/logpai/loghub/master/HDFS/HDFS_2k.log",
        "sha256": "7c967000980c086ed55fa6544ba4f05fe66d44622795e890c68caf8bbb635035",
        "expected_bytes": 287848,
    },
}

VERBATIM_LOGHUB_LICENSE = (
    "LICENSE OF LOGHUB: data files collected from open source repositories; "
    "use for research/academic purposes; citation of Zhu et al. (arXiv:2308.07703) appreciated."
)

VERBATIM_CITATION = (
    "Jieming Zhu, Shilin He, Pinjia He, Jinyang Liu, Michael R. Lyu. "
    "Loghub: A Large Collection of System Log Datasets for AI-driven Log Analytics. "
    "In ISSRE, 2023. arXiv:2308.07703."
)


def fetch_and_verify() -> None:
    data_dir = Path(__file__).resolve().parent
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    downloaded_raw = {}

    print("=" * 70)
    print("LOGHUB RESEARCH DATASET ACQUISITION (FETCH-ON-DEMAND)")
    print("=" * 70)
    print(f"\n[LICENSE NOTICE]\n{VERBATIM_LOGHUB_LICENSE}\n")
    print(f"[ACADEMIC CITATION]\n{VERBATIM_CITATION}\n")
    print("-" * 70)

    for filename, meta in PINNED_SOURCES.items():
        dest = raw_dir / filename
        print(f"[*] Downloading {filename} from {meta['url']}...")
        req = urllib.request.Request(
            meta["url"],
            headers={"User-Agent": "Enterprise-Asset-OS-Loghub-Fetcher/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()

        computed_hash = hashlib.sha256(content).hexdigest()
        if computed_hash != meta["sha256"]:
            print(f"[!] SHA-256 PIN MISMATCH for {filename}!")
            print(f"    Expected: {meta['sha256']}")
            print(f"    Got:      {computed_hash}")
            sys.exit(1)

        dest.write_bytes(content)
        downloaded_raw[filename] = content.decode("utf-8", errors="replace")
        print(f"    Verified SHA-256: {computed_hash} ({len(content)} bytes) [OK]")

    # Extract documented continuous slices
    print("\n[*] Extracting documented line-slices from canonical byte streams...")
    linux_lines = downloaded_raw["Linux_2k.log"].splitlines()
    openstack_lines = downloaded_raw["OpenStack_2k.log"].splitlines()
    hdfs_lines = downloaded_raw["HDFS_2k.log"].splitlines()

    real_incidents = [
        {
            "id": "INC-LOGHUB-LINUX-001",
            "system": "Linux Security & Authentication Daemon (PAM/SSHD)",
            "source_file": "Linux_2k.log",
            "source_repo": "https://github.com/logpai/loghub",
            "line_range": "L10-L35",
            "severity": "HIGH",
            "title": "High-Frequency SSH Daemon Authentication Failures & PAM Rejection Burst",
            "raw_log": "\n".join(linux_lines[9:35]),
        },
        {
            "id": "INC-LOGHUB-OPENSTACK-002",
            "system": "OpenStack Nova Compute / Libvirt ImageCache & WSGI",
            "source_file": "OpenStack_2k.log",
            "source_repo": "https://github.com/logpai/loghub",
            "line_range": "L55-L62",
            "severity": "WARNING",
            "title": "Nova Libvirt Unknown Base Image Cache Warning & WSGI HTTP 404 Exception",
            "raw_log": "\n".join(openstack_lines[54:62]),
        },
        {
            "id": "INC-LOGHUB-HDFS-003",
            "system": "HDFS Distributed DataNode DataXceiver",
            "source_file": "HDFS_2k.log",
            "source_repo": "https://github.com/logpai/loghub",
            "line_range": "L78-L85",
            "severity": "ERROR",
            "title": "DataNode Block Transmission Exceptions to Client Socket Endpoints",
            "raw_log": "\n".join(hdfs_lines[77:85]),
        },
    ]

    incidents_path = data_dir / "real_incidents.json"
    incidents_bytes = json.dumps(real_incidents, indent=2).encode("utf-8")
    incidents_path.write_bytes(incidents_bytes)
    incidents_hash = hashlib.sha256(incidents_bytes).hexdigest()
    print(f"    Generated {incidents_path.name} (SHA-256: {incidents_hash})")

    # Generate hybrid cluster nodes fixture
    real_cluster_nodes = {
        "10.251.30.85:50010": {
            "status": "degraded",
            "load_pct": 88.4,
            "region": "hdfs-rack-01",
            "provider": "loghub-hdfs-datanode",
            "extracted_from": "HDFS_2k.log:L78",
            "cores": 8,
            "ram_total_gb": 32.0,
        },
        "10.251.126.255:50010": {
            "status": "active",
            "load_pct": 42.6,
            "region": "hdfs-rack-01",
            "provider": "loghub-hdfs-datanode",
            "extracted_from": "HDFS_2k.log:L79",
            "cores": 8,
            "ram_total_gb": 32.0,
        },
        "10.251.71.68:50010": {
            "status": "active",
            "load_pct": 29.1,
            "region": "hdfs-rack-02",
            "provider": "loghub-hdfs-datanode",
            "extracted_from": "HDFS_2k.log:L80",
            "cores": 16,
            "ram_total_gb": 64.0,
        },
        "b9000564-fe1a-409b-b8cc-1e88b294cd1d": {
            "status": "active",
            "load_pct": 51.7,
            "region": "openstack-nova-compute",
            "provider": "loghub-openstack-vm",
            "extracted_from": "OpenStack_2k.log:L55",
            "cores": 4,
            "ram_total_gb": 16.0,
        },
        "10.11.10.1": {
            "status": "active",
            "load_pct": 33.2,
            "region": "openstack-controller",
            "provider": "loghub-openstack-api",
            "extracted_from": "OpenStack_2k.log:L56",
            "cores": 16,
            "ram_total_gb": 64.0,
        },
        "i-0a81b2c3d4e5f6789": {
            "status": "active",
            "load_pct": 42.1,
            "region": "us-east-1",
            "provider": "aws-ec2",
            "instance_type": "c6i.4xlarge",
            "cores": 16,
            "ram_total_gb": 32.0,
        },
        "gke-prod-cluster-pool-1-a1b2": {
            "status": "active",
            "load_pct": 55.3,
            "region": "us-central1-a",
            "provider": "gcp-gke",
            "cores": 16,
            "ram_total_gb": 64.0,
        },
        "aks-nodepool1-28491028-vmss000001": {
            "status": "rebooting",
            "load_pct": 0.0,
            "region": "westeurope",
            "provider": "azure-aks",
            "cores": 8,
            "ram_total_gb": 32.0,
        },
        "node-worker-01.infra.internal": {
            "status": "active",
            "load_pct": 14.2,
            "region": "me-central-1",
            "provider": "bare-metal",
            "cores": 32,
            "ram_total_gb": 128.0,
        },
        "server-01": {
            "status": "active",
            "load_pct": 34.5,
            "region": "us-east-1",
            "provider": "canonical-baseline",
        },
        "server-02": {
            "status": "degraded",
            "load_pct": 89.2,
            "region": "eu-west-1",
            "provider": "canonical-baseline",
        },
    }

    nodes_path = data_dir / "real_cluster_nodes.json"
    nodes_bytes = json.dumps(real_cluster_nodes, indent=2).encode("utf-8")
    nodes_path.write_bytes(nodes_bytes)
    nodes_hash = hashlib.sha256(nodes_bytes).hexdigest()
    print(f"    Generated {nodes_path.name} (SHA-256: {nodes_hash})")

    # Generate MANIFEST.json with verbatim license quote
    manifest = {
        "version": "1.2.0",
        "generation_date": "2026-09-17",
        "hash_method": "sha256-of-raw-bytes",
        "distribution_policy": "fetch-on-demand only; zero research data bundled in release artifacts",
        "license": VERBATIM_LOGHUB_LICENSE,
        "academic_citation": VERBATIM_CITATION,
        "canonical_upstream_sources": {
            k: {
                "source_url": v["url"],
                "local_path": f"tests/data/raw/{k}",
                "size_bytes": v["expected_bytes"],
                "sha256": v["sha256"],
            }
            for k, v in PINNED_SOURCES.items()
        },
        "fixtures": {
            "real_incidents.json": {
                "local_path": "tests/data/real_incidents.json",
                "size_bytes": len(incidents_bytes),
                "sha256": incidents_hash,
                "classification": "100% genuine continuous line-slice from downloaded raw logs",
                "samples": [
                    {"id": "INC-LOGHUB-LINUX-001", "source": "Linux_2k.log", "lines": "L10-L35"},
                    {"id": "INC-LOGHUB-OPENSTACK-002", "source": "OpenStack_2k.log", "lines": "L55-L62"},
                    {"id": "INC-LOGHUB-HDFS-003", "source": "HDFS_2k.log", "lines": "L78-L85"},
                ],
            },
            "real_cluster_nodes.json": {
                "local_path": "tests/data/real_cluster_nodes.json",
                "size_bytes": len(nodes_bytes),
                "sha256": nodes_hash,
                "classification": "hybrid (extracted node identifiers + representative cloud-format samples + synthetic telemetry attributes)",
                "composition": {
                    "extracted_identifiers": [
                        {"id": "10.251.30.85:50010", "source": "HDFS_2k.log:L78"},
                        {"id": "10.251.126.255:50010", "source": "HDFS_2k.log:L79"},
                        {"id": "10.251.71.68:50010", "source": "HDFS_2k.log:L80"},
                        {"id": "b9000564-fe1a-409b-b8cc-1e88b294cd1d", "source": "OpenStack_2k.log:L55"},
                        {"id": "10.11.10.1", "source": "OpenStack_2k.log:L56"},
                    ],
                    "representative_format_samples": [
                        "i-0a81b2c3d4e5f6789 (AWS EC2)",
                        "gke-prod-cluster-pool-1-a1b2 (GCP GKE)",
                        "aks-nodepool1-28491028-vmss000001 (Azure AKS)",
                        "node-worker-01.infra.internal (Internal FQDN)",
                    ],
                    "telemetry_attributes": "synthetic across all entries",
                },
            },
        },
    }

    manifest_path = data_dir / "MANIFEST.json"
    manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)
    print(f"    Generated {manifest_path.name} (SHA-256: {hashlib.sha256(manifest_bytes).hexdigest()})")
    print("\n[SUCCESS] All real-data fixtures fetched, pinned, and generated.")


if __name__ == "__main__":
    fetch_and_verify()
