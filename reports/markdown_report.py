from __future__ import annotations

from pathlib import Path

from app.models import BenchmarkResult, FinalRunResult


def _stringify(value: object) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _render_table(headers: list[str], rows: list[list[object]]) -> str:
    rendered_rows = [[_stringify(cell) for cell in row] for row in rows]
    widths = [len(header) for header in headers]
    for row in rendered_rows:
        for index, cell in enumerate(row):
            widths[index] = max(widths[index], len(cell))

    def _format_row(cells: list[str]) -> str:
        return " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(cells))

    separator = "-+-".join("-" * width for width in widths)
    lines = ["```text", _format_row(headers), separator]
    for row in rendered_rows:
        lines.append(_format_row(row))
    lines.append("```")
    return "\n".join(lines)


def _benchmark_rows(result: BenchmarkResult | None) -> list[object]:
    if result is None:
        return ["not_run", "not_run", "n/a", "n/a", "0", "n/a", "n/a", "n/a", "n/a"]
    return [
        result.name,
        result.status,
        result.testcase or "n/a",
        result.binary_path or "n/a",
        result.completed_runs,
        result.metrics.peak_bandwidth_gbps,
        result.metrics.average_bandwidth_gbps,
        result.metrics.average_latency_ms,
        result.metrics.average_latency_us,
    ]


def _command_output_rows(command_outputs: dict[str, str]) -> list[list[object]]:
    if not command_outputs:
        return [["n/a", 1, "n/a"]]

    rows: list[list[object]] = []
    for command, output in command_outputs.items():
        lines = output.splitlines() or ["n/a"]
        for index, line in enumerate(lines):
            rows.append([command if index == 0 else "", index + 1, line])
    return rows


def write_markdown_report(result: FinalRunResult, output_path: Path) -> Path:
    inspection = result.inspection
    memory_total_gb = round((inspection.memory.total_kb or 0) / 1024 / 1024, 2) if inspection.memory.total_kb else None
    memory_available_gb = (
        round((inspection.memory.available_kb or 0) / 1024 / 1024, 2) if inspection.memory.available_kb else None
    )

    execution_rows = [
        ["Overall Status", result.status],
        ["Timestamp", inspection.timestamp.isoformat()],
        ["OS", inspection.software.os.pretty_name],
        ["Kernel", inspection.software.kernel_version],
        ["Driver", inspection.software.driver_version],
        ["CUDA", inspection.software.cuda_version],
        ["NCCL", inspection.software.nccl_version],
    ]
    inventory_rows = [
        ["BIOS Vendor", inspection.bios.vendor],
        ["Product", inspection.bios.product_name],
        ["CPU Model", inspection.cpu.model_name],
        ["Architecture", inspection.cpu.architecture],
        ["CPU Count", inspection.cpu.cpus],
        ["Sockets", inspection.cpu.sockets],
        ["NUMA Nodes", inspection.cpu.numa_nodes],
        ["Memory Total (GiB)", memory_total_gb],
        ["Memory Available (GiB)", memory_available_gb],
        ["GPUs Detected", len(inspection.gpus)],
        ["NICs Detected", len(inspection.nics)],
        ["PCIe Devices", len(inspection.pci_devices)],
    ]
    config_rows = [
        ["IOMMU Enabled", inspection.software.iommu_enabled],
        ["IOMMU Details", ", ".join(inspection.software.iommu_details) or "n/a"],
        ["Environment Keys", len(inspection.environment)],
        ["System Parameters", len(inspection.system_parameters)],
        ["NCCL AllReduce Command", result.benchmarks.nccl.command if result.benchmarks.nccl else None],
        ["NCCL AllToAll Command", result.benchmarks.nccl_alltoall.command if result.benchmarks.nccl_alltoall else None],
        ["NVBandwidth Command", result.benchmarks.nvbandwidth.command if result.benchmarks.nvbandwidth else None],
    ]
    topology_rows = [
        ["GPU Topology Available", inspection.topology.gpu_topology_available],
        ["NIC Topology Available", inspection.topology.nic_topology_available],
        ["Topology Headers", ", ".join(inspection.topology.headers) or "n/a"],
        ["GPU/NIC Links", len(inspection.topology.gpu_nic_links)],
    ]
    benchmark_rows = [
        _benchmark_rows(result.benchmarks.nccl),
        _benchmark_rows(result.benchmarks.nccl_alltoall),
        _benchmark_rows(result.benchmarks.nvbandwidth),
    ]
    warning_rows = [[warning] for warning in dict.fromkeys([*inspection.warnings, *result.warnings])] or [["None"]]
    lines = [
        "# Agentic-AI-Benchmark-Agent Report",
        "",
        "## Execution Summary",
        "",
        _render_table(["Section", "Value"], execution_rows),
        "",
        "## System Inventory",
        "",
        _render_table(["Item", "Value"], inventory_rows),
        "",
        "## Configuration Summary",
        "",
        _render_table(["Config", "Value"], config_rows),
        "",
        "## Topology Summary",
        "",
        _render_table(["Topology", "Value"], topology_rows),
        "",
        "## Benchmark Performance",
        "",
        _render_table(
            ["Benchmark", "Status", "Test Case", "Binary", "Runs", "Peak BW", "Avg BW", "Avg Lat ms", "Avg Lat us"],
            benchmark_rows,
        ),
        "",
        "## Warnings",
        "",
        _render_table(["Warning"], warning_rows),
        "",
        "## Command Outputs",
        "",
        _render_table(["Command", "Output Line", "Content"], _command_output_rows(inspection.raw_command_outputs)),
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path
