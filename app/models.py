from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class CommandExecutionResult(BaseModel):
    command: str
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    timed_out: bool = False
    duration_seconds: float | None = None


class CpuInfo(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    architecture: str | None = None
    cpus: int | None = None
    threads_per_core: int | None = None
    cores_per_socket: int | None = None
    sockets: int | None = None
    numa_nodes: int | None = None
    model_name: str | None = None


class NumaNode(BaseModel):
    node_id: int
    cpus: list[int] = Field(default_factory=list)
    size_mb: int | None = None


class SystemMemoryInfo(BaseModel):
    total_kb: int | None = None
    available_kb: int | None = None


class GpuInfo(BaseModel):
    index: int | None = None
    name: str | None = None
    uuid: str | None = None
    pci_bus_id: str | None = None
    driver_version: str | None = None
    memory_total_mb: int | None = None


class NicInfo(BaseModel):
    name: str | None = None
    pci_bus_id: str | None = None
    description: str | None = None


class PciDeviceInfo(BaseModel):
    slot: str
    description: str


class OperatingSystemInfo(BaseModel):
    name: str | None = None
    version_id: str | None = None
    pretty_name: str | None = None


class BiosInfo(BaseModel):
    vendor: str | None = None
    version: str | None = None
    product_name: str | None = None


class SoftwareStack(BaseModel):
    os: OperatingSystemInfo = Field(default_factory=OperatingSystemInfo)
    kernel_version: str | None = None
    kernel_full: str | None = None
    driver_version: str | None = None
    cuda_version: str | None = None
    nccl_version: str | None = None
    iommu_enabled: bool | None = None
    iommu_details: list[str] = Field(default_factory=list)


class TopologyLink(BaseModel):
    source: str
    target: str
    link_type: str


class TopologySummary(BaseModel):
    gpu_topology_available: bool = False
    nic_topology_available: bool = False
    headers: list[str] = Field(default_factory=list)
    matrix: dict[str, dict[str, str]] = Field(default_factory=dict)
    gpu_nic_links: list[TopologyLink] = Field(default_factory=list)


class InspectionResult(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Literal["success", "partial_success", "failed"] = "success"
    bios: BiosInfo = Field(default_factory=BiosInfo)
    cpu: CpuInfo = Field(default_factory=CpuInfo)
    numa_nodes: list[NumaNode] = Field(default_factory=list)
    memory: SystemMemoryInfo = Field(default_factory=SystemMemoryInfo)
    gpus: list[GpuInfo] = Field(default_factory=list)
    nics: list[NicInfo] = Field(default_factory=list)
    pci_devices: list[PciDeviceInfo] = Field(default_factory=list)
    software: SoftwareStack = Field(default_factory=SoftwareStack)
    topology: TopologySummary = Field(default_factory=TopologySummary)
    system_parameters: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    raw_command_notes: dict[str, str] = Field(default_factory=dict)
    raw_command_outputs: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)


class BenchmarkSample(BaseModel):
    label: str
    bandwidth_gbps: float | None = None
    latency_ms: float | None = None
    latency_us: float | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class BenchmarkMetrics(BaseModel):
    peak_bandwidth_gbps: float | None = None
    average_bandwidth_gbps: float | None = None
    average_latency_ms: float | None = None
    average_latency_us: float | None = None
    samples: list[BenchmarkSample] = Field(default_factory=list)


class BenchmarkResult(BaseModel):
    name: str
    status: Literal["passed", "failed", "missing_binary", "timeout", "skipped"] = "skipped"
    profile_name: str | None = None
    binary_path: str | None = None
    testcase: str | None = None
    command: str | None = None
    metrics: BenchmarkMetrics = Field(default_factory=BenchmarkMetrics)
    parsed_output: dict[str, Any] = Field(default_factory=dict)
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    completed_runs: int = 0
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None


class BenchmarkSuiteResult(BaseModel):
    nccl: BenchmarkResult | None = None
    nccl_alltoall: BenchmarkResult | None = None
    nvbandwidth: BenchmarkResult | None = None


class FinalRunResult(BaseModel):
    inspection: InspectionResult
    benchmarks: BenchmarkSuiteResult
    report_paths: dict[str, str]
    status: Literal["success", "partial_success", "failed"]
    warnings: list[str] = Field(default_factory=list)


class BenchmarkProfile(BaseModel):
    name: str = "default"
    enabled: bool = True
    binary_path: str
    env: dict[str, str] = Field(default_factory=dict)
    args: list[str] = Field(default_factory=list)
    timeout_seconds: int = 60
    repetitions: int = 1


class Settings(BaseModel):
    agent_name: str = "Agentic-AI-Benchmark-Agent"
    report_output_dir: str = "data/reports"
    result_output_dir: str = "data/results"
    default_command_timeout_seconds: int = 30
    inspect_dmesg: bool = False
    selected_env_vars: list[str] = Field(default_factory=list)
    system_parameters: list[str] = Field(default_factory=list)
    enable_benchmarks: dict[str, bool] = Field(default_factory=dict)
    benchmark_profiles_file: str = "config/benchmark_profiles.yaml"


class RunRequest(BaseModel):
    inspect_only: bool = False
    run_nccl: bool = True
    run_nvbandwidth: bool = True
    generate_reports: bool = True
    nccl_profile: str = "default"
    nvbandwidth_profile: str = "default"
    output_dir: str | None = None


class BenchmarkRequest(BaseModel):
    profile_name: str = "default"
