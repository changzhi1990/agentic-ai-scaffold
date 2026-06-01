from __future__ import annotations

import csv
import json
import re
from io import StringIO

ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def _parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", value)
    return int(digits) if digits else None


def parse_lscpu_output(raw_text: str) -> dict:
    mapping: dict[str, str] = {}
    for line in raw_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        mapping[key.strip()] = value.strip()
    return {
        "architecture": mapping.get("Architecture"),
        "cpus": _parse_int(mapping.get("CPU(s)")),
        "threads_per_core": _parse_int(mapping.get("Thread(s) per core")),
        "cores_per_socket": _parse_int(mapping.get("Core(s) per socket")),
        "sockets": _parse_int(mapping.get("Socket(s)")),
        "numa_nodes": _parse_int(mapping.get("NUMA node(s)")),
        "model_name": mapping.get("Model name"),
    }


def parse_nvidia_smi_query_output(raw_text: str) -> dict:
    reader = csv.reader(StringIO(raw_text.strip()))
    gpus = []
    for row in reader:
        if len(row) < 6:
            continue
        if row[0].strip().lower() == "index":
            continue
        gpus.append(
            {
                "index": _parse_int(row[0].strip()),
                "name": row[1].strip(),
                "uuid": row[2].strip(),
                "pci_bus_id": row[3].strip(),
                "driver_version": row[4].strip(),
                "memory_total_mb": _parse_int(row[5].strip()),
            }
        )
    return {"gpus": gpus}


def parse_nvidia_smi_topology_output(raw_text: str) -> dict:
    normalized = ANSI_ESCAPE_PATTERN.sub("", raw_text)
    lines = [line.rstrip() for line in normalized.splitlines() if line.strip()]
    matrix_lines: list[list[str]] = []
    legend: list[str] = []
    for line in lines:
        if line.startswith("Legend:") or legend:
            legend.append(line)
            continue
        stripped_line = line.strip("\t")
        parts = re.split(r"\s{2,}|\t", stripped_line)
        if line.startswith("\t") and parts and parts[0]:
            parts.insert(0, "")
        if parts:
            matrix_lines.append([part.strip() for part in parts if part.strip()])
    if not matrix_lines:
        return {"headers": [], "matrix": {}, "gpu_nic_links": [], "legend": legend}

    headers = matrix_lines[0]
    matrix: dict[str, dict[str, str]] = {}
    gpu_nic_links: list[dict[str, str]] = []
    peer_headers = [header for header in headers if header.startswith(("GPU", "NIC"))]

    for row in matrix_lines[1:]:
        row_name = row[0]
        if row_name not in peer_headers:
            continue
        values = row[1:]
        peer_values = values[: len(peer_headers)]
        matrix[row_name] = {}
        for header, relation in zip(peer_headers, peer_values, strict=False):
            matrix[row_name][header] = relation
            if row_name.startswith("GPU") and header.startswith("NIC") and relation not in {"X", "N/A"}:
                gpu_nic_links.append({"gpu": row_name, "nic": header, "link_type": relation})

    return {"headers": headers, "matrix": matrix, "gpu_nic_links": gpu_nic_links, "legend": legend}


def parse_numactl_hardware_output(raw_text: str) -> dict:
    node_count = 0
    nodes: list[dict] = []
    distance_matrix: dict[str, dict[str, int]] = {}
    header_nodes: list[str] = []

    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("available:"):
            match = re.search(r"available:\s+(\d+)\s+nodes", stripped)
            if match:
                node_count = int(match.group(1))
        elif stripped.startswith("node ") and " cpus:" in stripped:
            match = re.match(r"node\s+(\d+)\s+cpus:\s*(.*)", stripped)
            if match:
                node_id = int(match.group(1))
                cpus = [int(token) for token in match.group(2).split()] if match.group(2).strip() else []
                nodes.append({"node_id": node_id, "cpus": cpus, "size_mb": None})
        elif stripped.startswith("node ") and " size:" in stripped:
            match = re.match(r"node\s+(\d+)\s+size:\s*(\d+)", stripped)
            if match:
                node_id = int(match.group(1))
                size_mb = int(match.group(2))
                for node in nodes:
                    if node["node_id"] == node_id:
                        node["size_mb"] = size_mb
                        break
        elif stripped.startswith("node") and ":" not in stripped:
            header_nodes = [token for token in stripped.split()[1:]]
        elif re.match(r"^\d+:", stripped):
            source, values = stripped.split(":", 1)
            distances = [int(token) for token in values.split()]
            distance_matrix[source.strip()] = {
                target: distance for target, distance in zip(header_nodes, distances, strict=False)
            }

    return {"node_count": node_count, "nodes": nodes, "distance_matrix": distance_matrix}


def parse_uname_output(raw_text: str) -> dict:
    tokens = raw_text.strip().split()
    return {
        "kernel_full": raw_text.strip(),
        "kernel_version": tokens[2] if len(tokens) > 2 else None,
        "hostname": tokens[1] if len(tokens) > 1 else None,
    }


def parse_os_release(raw_text: str) -> dict:
    data: dict[str, str] = {}
    for line in raw_text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return {
        "name": data.get("NAME"),
        "version_id": data.get("VERSION_ID"),
        "pretty_name": data.get("PRETTY_NAME"),
    }


def parse_lspci_output(raw_text: str) -> dict:
    devices = []
    for line in raw_text.splitlines():
        if not line.strip():
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        devices.append({"slot": parts[0].strip(), "description": parts[1].strip()})
    return {"devices": devices}


def parse_sysctl_output(raw_text: str) -> dict:
    values: dict[str, str] = {}
    for line in raw_text.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def parse_lsmod_output(raw_text: str) -> dict:
    modules = []
    for index, line in enumerate(raw_text.splitlines()):
        if not line.strip():
            continue
        if index == 0 and line.lower().startswith("module"):
            continue
        parts = line.split()
        modules.append({"name": parts[0], "size": _parse_int(parts[1]) if len(parts) > 1 else None})
    return {"modules": modules}


def parse_proc_cmdline(raw_text: str) -> dict:
    tokens = raw_text.strip().split()
    iommu_tokens = [token for token in tokens if "iommu" in token.lower()]
    enabled = any(token.lower().endswith(("=on", "=pt")) for token in iommu_tokens)
    return {"iommu_enabled": enabled if iommu_tokens else None, "iommu_details": iommu_tokens}


def parse_proc_meminfo(raw_text: str) -> dict:
    values: dict[str, int] = {}
    for line in raw_text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = _parse_int(value)
    return {"total_kb": values.get("MemTotal"), "available_kb": values.get("MemAvailable")}


def parse_cuda_version_text(raw_text: str) -> dict:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        match = re.search(r"CUDA Version\s*([\d.]+)", raw_text)
        return {"cuda_version": match.group(1) if match else raw_text.strip()}
    version = data.get("cuda", {}).get("version")
    return {"cuda_version": version}


def parse_nccl_header_version(raw_text: str) -> dict:
    parts = {}
    for field in ("NCCL_MAJOR", "NCCL_MINOR", "NCCL_PATCH"):
        match = re.search(rf"#define\s+{field}\s+(\d+)", raw_text)
        if match:
            parts[field] = match.group(1)
    if len(parts) == 3:
        version = ".".join([parts["NCCL_MAJOR"], parts["NCCL_MINOR"], parts["NCCL_PATCH"]])
        return {"nccl_version": version}
    match = re.search(r"NCCL version\s*([\d.]+)", raw_text, flags=re.IGNORECASE)
    return {"nccl_version": match.group(1) if match else None}
