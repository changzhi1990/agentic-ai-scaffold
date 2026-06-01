from __future__ import annotations

from app.models import TopologyLink, TopologySummary


def build_topology_summary(parsed: dict) -> TopologySummary:
    links = [
        TopologyLink(source=item["gpu"], target=item["nic"], link_type=item["link_type"])
        for item in parsed.get("gpu_nic_links", [])
    ]
    return TopologySummary(
        gpu_topology_available=bool(parsed.get("matrix")),
        nic_topology_available=any(header.startswith("NIC") for header in parsed.get("headers", [])),
        headers=parsed.get("headers", []),
        matrix=parsed.get("matrix", {}),
        gpu_nic_links=links,
    )
