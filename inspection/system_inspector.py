from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

from app.models import (
    BiosInfo,
    CpuInfo,
    GpuInfo,
    InspectionResult,
    NicInfo,
    NumaNode,
    OperatingSystemInfo,
    PciDeviceInfo,
    SoftwareStack,
    SystemMemoryInfo,
)
from inspection.command_collectors import BIOS_FILES, INSPECTION_COMMANDS, NCCL_HEADER_PATHS
from inspection.parsers import (
    parse_cuda_version_text,
    parse_lsmod_output,
    parse_lscpu_output,
    parse_lspci_output,
    parse_nccl_header_version,
    parse_nvidia_smi_query_output,
    parse_nvidia_smi_topology_output,
    parse_numactl_hardware_output,
    parse_os_release,
    parse_proc_cmdline,
    parse_proc_meminfo,
    parse_sysctl_output,
    parse_uname_output,
)
from inspection.topology import build_topology_summary
from tools.file_tool import FileTool
from tools.shell_tool import ShellTool, parse_command_output

LOGGER = logging.getLogger(__name__)
ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


class SystemInspector:
    def __init__(self, shell_tool: ShellTool | Any | None = None, file_tool: FileTool | None = None) -> None:
        self.shell_tool = shell_tool or ShellTool()
        self.file_tool = file_tool or FileTool()

    def inspect(self, selected_env_vars: list[str] | None = None, system_parameters: list[str] | None = None) -> InspectionResult:
        result = InspectionResult()
        selected_env_vars = selected_env_vars or []
        system_parameters = system_parameters or []

        collected: dict[str, dict] = {}
        for spec in INSPECTION_COMMANDS:
            if not self.shell_tool.exists(spec.executable):
                result.raw_command_notes[spec.command] = f"executable unavailable: {spec.executable}"
                result.raw_command_outputs[spec.command] = f"executable unavailable: {spec.executable}"
                result.warnings.append(f"Command unavailable: {spec.executable}")
                continue
            command_result = self.shell_tool.run(spec.command)
            if command_result.get("exit_code", 1) != 0:
                result.raw_command_notes[spec.command] = f"command failed: exit_code={command_result.get('exit_code')}"
                result.raw_command_outputs[spec.command] = self._normalize_command_output(
                    command_result.get("stdout") or command_result.get("stderr") or result.raw_command_notes[spec.command]
                )
                if command_result.get("stderr"):
                    result.warnings.append(f"{spec.command}: {command_result['stderr'].strip()}")
                continue
            collected[spec.name] = command_result
            result.raw_command_notes[spec.command] = "collected"
            result.raw_command_outputs[spec.command] = self._normalize_command_output(command_result.get("stdout", ""))

        self._populate_bios(result)
        self._populate_cpu(result, collected.get("lscpu", {}).get("stdout", ""))
        self._populate_memory(result, collected.get("proc_meminfo", {}).get("stdout", ""))
        self._populate_numa(result, collected.get("numactl", {}).get("stdout", ""))
        self._populate_gpus(result, collected.get("nvidia_smi_query", {}).get("stdout", ""))
        self._populate_pci_and_nics(result, collected.get("lspci", {}).get("stdout", ""))
        self._populate_software(
            result,
            uname_raw=collected.get("uname", {}).get("stdout", ""),
            os_release_raw=collected.get("os_release", {}).get("stdout", ""),
            proc_cmdline_raw=collected.get("proc_cmdline", {}).get("stdout", ""),
            nvidia_driver_raw=collected.get("nvidia_driver_proc", {}).get("stdout", ""),
            cuda_version_raw=collected.get("cuda_version_json", {}).get("stdout", ""),
        )
        self._populate_system_parameters(
            result,
            sysctl_raw=collected.get("sysctl", {}).get("stdout", ""),
            lsmod_raw=collected.get("lsmod", {}).get("stdout", ""),
            env_raw=collected.get("env", {}).get("stdout", ""),
            selected_env_vars=selected_env_vars,
            selected_parameters=system_parameters,
        )
        self._populate_topology(result, collected.get("nvidia_smi_topology", {}).get("stdout", ""))
        self._populate_nccl_version(result)
        self._finalize_status(result)
        return result

    def _populate_bios(self, result: InspectionResult) -> None:
        bios = BiosInfo()
        for field, path in BIOS_FILES.items():
            if not Path(path).exists():
                continue
            try:
                setattr(bios, field, self.file_tool.read(path)["content"].strip())
            except OSError as exc:
                LOGGER.debug("Failed to read BIOS field %s from %s: %s", field, path, exc)
        result.bios = bios

    def _populate_cpu(self, result: InspectionResult, raw_text: str) -> None:
        if not raw_text:
            result.warnings.append("CPU inventory unavailable")
            return
        parsed = parse_command_output(raw_text, parse_lscpu_output, fallback={})
        result.cpu = CpuInfo.model_validate(parsed)

    def _populate_memory(self, result: InspectionResult, raw_text: str) -> None:
        if raw_text:
            parsed = parse_command_output(raw_text, parse_proc_meminfo, fallback={})
            result.memory = SystemMemoryInfo.model_validate(parsed)

    def _populate_numa(self, result: InspectionResult, raw_text: str) -> None:
        if not raw_text:
            result.warnings.append("NUMA layout unavailable")
            return
        parsed = parse_command_output(raw_text, parse_numactl_hardware_output, fallback={"nodes": []})
        result.numa_nodes = [NumaNode.model_validate(node) for node in parsed.get("nodes", [])]
        if result.cpu.numa_nodes is None:
            result.cpu.numa_nodes = parsed.get("node_count")

    def _populate_gpus(self, result: InspectionResult, raw_text: str) -> None:
        if not raw_text:
            result.warnings.append("GPU inventory unavailable")
            return
        parsed = parse_command_output(raw_text, parse_nvidia_smi_query_output, fallback={"gpus": []})
        result.gpus = [GpuInfo.model_validate(gpu) for gpu in parsed.get("gpus", [])]
        if result.gpus and not result.software.driver_version:
            result.software.driver_version = result.gpus[0].driver_version

    def _populate_pci_and_nics(self, result: InspectionResult, raw_text: str) -> None:
        if not raw_text:
            return
        parsed = parse_command_output(raw_text, parse_lspci_output, fallback={"devices": []})
        devices = [PciDeviceInfo.model_validate(item) for item in parsed.get("devices", [])]
        result.pci_devices = devices
        nics = []
        for item in devices:
            desc_lower = item.description.lower()
            if "ethernet" in desc_lower or "network" in desc_lower or "infiniband" in desc_lower:
                nics.append(NicInfo(name=item.description.split(":")[0], pci_bus_id=item.slot, description=item.description))
        result.nics = nics

    def _populate_software(
        self,
        result: InspectionResult,
        uname_raw: str,
        os_release_raw: str,
        proc_cmdline_raw: str,
        nvidia_driver_raw: str,
        cuda_version_raw: str,
    ) -> None:
        software = result.software if result.software else SoftwareStack()
        if uname_raw:
            uname = parse_command_output(uname_raw, parse_uname_output, fallback={})
            software.kernel_full = uname.get("kernel_full")
            software.kernel_version = uname.get("kernel_version")
        if os_release_raw:
            software.os = OperatingSystemInfo.model_validate(
                parse_command_output(os_release_raw, parse_os_release, fallback={})
            )
        if proc_cmdline_raw:
            cmdline = parse_command_output(proc_cmdline_raw, parse_proc_cmdline, fallback={})
            software.iommu_enabled = cmdline.get("iommu_enabled")
            software.iommu_details = cmdline.get("iommu_details", [])
        if nvidia_driver_raw and not software.driver_version:
            software.driver_version = nvidia_driver_raw.strip().split()[-1]
        if cuda_version_raw:
            software.cuda_version = parse_command_output(cuda_version_raw, parse_cuda_version_text, fallback={}).get(
                "cuda_version"
            )
        result.software = software

    def _populate_system_parameters(
        self,
        result: InspectionResult,
        sysctl_raw: str,
        lsmod_raw: str,
        env_raw: str,
        selected_env_vars: list[str],
        selected_parameters: list[str],
    ) -> None:
        if sysctl_raw:
            sysctl_map = parse_command_output(sysctl_raw, parse_sysctl_output, fallback={})
            if selected_parameters:
                result.system_parameters.update({key: sysctl_map.get(key) for key in selected_parameters})
            else:
                result.system_parameters.update(sysctl_map)
        if lsmod_raw:
            parsed_lsmod = parse_command_output(lsmod_raw, parse_lsmod_output, fallback={"modules": []})
            result.system_parameters["kernel_modules"] = parsed_lsmod.get("modules", [])
        if env_raw:
            env_map = {}
            for line in env_raw.splitlines():
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                env_map[key] = value
            if selected_env_vars:
                result.environment = {key: env_map[key] for key in selected_env_vars if key in env_map}
            else:
                result.environment = env_map

    def _populate_topology(self, result: InspectionResult, raw_text: str) -> None:
        if not raw_text:
            result.warnings.append("GPU topology matrix unavailable")
            return
        parsed = parse_command_output(raw_text, parse_nvidia_smi_topology_output, fallback={})
        result.topology = build_topology_summary(parsed)

    def _populate_nccl_version(self, result: InspectionResult) -> None:
        for path in NCCL_HEADER_PATHS:
            if not Path(path).exists():
                continue
            try:
                parsed = parse_nccl_header_version(self.file_tool.read(path)["content"])
                if parsed.get("nccl_version"):
                    result.software.nccl_version = parsed["nccl_version"]
                    return
            except OSError as exc:
                LOGGER.debug("Failed to read NCCL header %s: %s", path, exc)
        result.warnings.append("NCCL version not detected")

    def _finalize_status(self, result: InspectionResult) -> None:
        if result.cpu.architecture and (result.gpus or result.nics or result.pci_devices):
            result.status = "partial_success" if result.warnings else "success"
        elif result.cpu.architecture or result.gpus:
            result.status = "partial_success"
        else:
            result.status = "failed"

    def _normalize_command_output(self, raw_text: str) -> str:
        cleaned = ANSI_ESCAPE_PATTERN.sub("", raw_text or "")
        return cleaned.strip()
