from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    name: str
    command: str
    executable: str


INSPECTION_COMMANDS = [
    CommandSpec("lscpu", "lscpu", "lscpu"),
    CommandSpec("uname", "uname -a", "uname"),
    CommandSpec("numactl", "numactl --hardware", "numactl"),
    CommandSpec("os_release", "cat /etc/os-release", "cat"),
    CommandSpec("proc_cmdline", "cat /proc/cmdline", "cat"),
    CommandSpec("proc_meminfo", "cat /proc/meminfo", "cat"),
    CommandSpec("sysctl", "sysctl -a", "sysctl"),
    CommandSpec("lspci", "lspci -D", "lspci"),
    CommandSpec("lsmod", "lsmod", "lsmod"),
    CommandSpec("env", "printenv", "printenv"),
    CommandSpec(
        "nvidia_smi_query",
        "nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,driver_version,memory.total --format=csv,noheader,nounits",
        "nvidia-smi",
    ),
    CommandSpec("nvidia_smi_topology", "nvidia-smi topo -m", "nvidia-smi"),
    CommandSpec("nvidia_driver_proc", "cat /proc/driver/nvidia/version", "cat"),
    CommandSpec("cuda_version_json", "cat /usr/local/cuda/version.json", "cat"),
]


BIOS_FILES = {
    "vendor": "/sys/class/dmi/id/bios_vendor",
    "version": "/sys/class/dmi/id/bios_version",
    "product_name": "/sys/class/dmi/id/product_name",
}


NCCL_HEADER_PATHS = [
    "/usr/include/nccl.h",
    "/usr/local/cuda/include/nccl.h",
]
