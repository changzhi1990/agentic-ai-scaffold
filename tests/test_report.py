import json
from pathlib import Path

from app.models import (
    BenchmarkMetrics,
    BenchmarkResult,
    BenchmarkSuiteResult,
    CpuInfo,
    FinalRunResult,
    InspectionResult,
    NicInfo,
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
        memory=SystemMemoryInfo(total_kb=1000, available_kb=500),
        gpus=[],
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
            metrics=BenchmarkMetrics(),
            warnings=["binary missing"],
        ),
        nccl_alltoall=BenchmarkResult(
            name="nccl_alltoall",
            status="passed",
            metrics=BenchmarkMetrics(peak_bandwidth_gbps=30.48),
        ),
        nvbandwidth=BenchmarkResult(
            name="nvbandwidth",
            status="passed",
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
    assert "## Configuration Summary" in md_data
    assert "## Benchmark Performance" in md_data
    assert "```text" in md_data
    assert "Section        | Value" in md_data
    assert "Benchmark     | Status" in md_data
    assert "nccl_alltoall" in md_data
    assert "Command  | Output Line | Content" in md_data
    assert "Architecture: x86_64" in md_data
    assert "collected" not in md_data
