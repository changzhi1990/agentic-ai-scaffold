import json
from pathlib import Path

from app.models import (
    BenchmarkMetrics,
    BenchmarkResult,
    BenchmarkSuiteResult,
    CpuInfo,
    FinalRunResult,
    GpuInfo,
    InspectionResult,
    NicInfo,
    NumaNode,
    OperatingSystemInfo,
    PciDeviceInfo,
    SoftwareStack,
    SystemMemoryInfo,
    TopologySummary,
)
from reports.generator import ReportGenerator


def test_report_generator_writes_json_and_markdown(tmp_path: Path) -> None:
    inspection = InspectionResult(
        status="partial_success",
        cpu=CpuInfo(architecture="x86_64", cpus=64, sockets=2, numa_nodes=2),
        numa_nodes=[NumaNode(node_id=0, cpus=[0, 1], size_mb=1024)],
        memory=SystemMemoryInfo(total_kb=1000, available_kb=500),
        gpus=[GpuInfo(index=0, name="NVIDIA H100", pci_bus_id="0000:01:00.0", driver_version="550.54.15", memory_total_mb=81559)],
        nics=[NicInfo(name="eth0", pci_bus_id="0000:81:00.0")],
        pci_devices=[PciDeviceInfo(slot="0000:81:00.0", description="Ethernet controller: Mellanox")],
        software=SoftwareStack(
            os=OperatingSystemInfo(name="Ubuntu", version_id="24.04", pretty_name="Ubuntu 24.04 LTS"),
            kernel_version="6.8.0",
            driver_version="550.54.15",
        ),
        topology=TopologySummary(gpu_topology_available=False, nic_topology_available=True),
        warnings=["GPU topology matrix unavailable"],
        raw_command_notes={"nvidia-smi topo -m": "command failed: exit_code=1"},
        raw_command_outputs={
            "lscpu": "Architecture: x86_64\nCPU(s): 64\nNUMA node(s): 2",
            "uname -a": "Linux test-host 6.8.0 #1 SMP x86_64 GNU/Linux",
        },
    )
    benchmarks = BenchmarkSuiteResult(
        nccl=BenchmarkResult(
            name="nccl",
            status="missing_binary",
            command="all_reduce_perf -g 8",
            metrics=BenchmarkMetrics(),
            warnings=["binary missing"],
        ),
        nccl_alltoall=BenchmarkResult(
            name="nccl_alltoall",
            status="passed",
            testcase="alltoall_perf",
            command="alltoall_perf -g 8",
            metrics=BenchmarkMetrics(peak_bandwidth_gbps=30.48),
        ),
        nvbandwidth=BenchmarkResult(
            name="nvbandwidth",
            status="passed",
            testcase="device_to_device_memcpy_read_ce",
            command="nvbandwidth --testcase device_to_device_memcpy_read_ce",
            metrics=BenchmarkMetrics(peak_bandwidth_gbps=312.5),
        ),
    )
    result = FinalRunResult(
        inspection=inspection,
        benchmarks=benchmarks,
        report_paths={},
        status="partial_success",
        warnings=["binary missing"],
    )

    generator = ReportGenerator(output_dir=tmp_path)
    paths = generator.generate(result)

    json_data = json.loads(Path(paths["json"]).read_text())
    md_data = Path(paths["markdown"]).read_text()

    assert json_data["status"] == "partial_success"
    assert "Ubuntu 24.04 LTS" in md_data
    assert "binary missing" in md_data
    assert "## Execution Summary" in md_data
    assert "## System Inventory" in md_data
    assert "## NUMA Layout" in md_data
    assert "## GPU Inventory" in md_data
    assert "## NIC Inventory" in md_data
    assert "## Configuration Summary" in md_data
    assert "## Benchmark Commands" in md_data
    assert "## Benchmark Performance" in md_data
    assert "```text" in md_data
    assert "Section        | Value" in md_data
    assert "Benchmark     | Status" in md_data
    assert "nccl_alltoall" in md_data
    assert "device_to_device_memcpy_read_ce" in md_data
    assert "NVIDIA H100" in md_data
    assert "eth0" in md_data
    assert "alltoall_perf -g 8" in md_data
    assert "Command  | Output Line | Content" in md_data
    assert "Architecture: x86_64" in md_data
    assert "collected" not in md_data
