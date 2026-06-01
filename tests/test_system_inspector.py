from inspection.parsers import parse_lscpu_output, parse_numactl_hardware_output
from inspection.system_inspector import SystemInspector


def test_parse_lscpu_output_extracts_basic_fields() -> None:
    raw = """Architecture:                    x86_64
CPU(s):                          128
Thread(s) per core:              2
Core(s) per socket:              32
Socket(s):                       2
NUMA node(s):                    2
"""
    parsed = parse_lscpu_output(raw)

    assert parsed["architecture"] == "x86_64"
    assert parsed["cpus"] == 128
    assert parsed["sockets"] == 2
    assert parsed["numa_nodes"] == 2


def test_parse_numactl_output_extracts_nodes() -> None:
    raw = """available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3
node 0 size: 257340 MB
node 1 cpus: 4 5 6 7
node 1 size: 257451 MB
node distances:
node   0   1
  0:  10  20
  1:  20  10
"""
    parsed = parse_numactl_hardware_output(raw)

    assert parsed["node_count"] == 2
    assert parsed["nodes"][0]["cpus"] == [0, 1, 2, 3]
    assert parsed["distance_matrix"]["0"]["1"] == 20


def test_system_inspector_collects_partial_results_without_crashing() -> None:
    command_map = {
        "lscpu": ("Architecture: x86_64\nCPU(s): 64\nNUMA node(s): 1\n", "", 0),
        "nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,driver_version,memory.total --format=csv,noheader,nounits": (
            "0, NVIDIA H100, GPU-1, 0000:01:00.0, 550.54.15, 81559\n",
            "",
            0,
        ),
        "nvidia-smi topo -m": ("GPU0\tCPU Affinity\tNUMA Affinity\nGPU0\tX\t0-63\t0\n", "", 0),
        "uname -a": ("Linux test-host 6.8.0 #1 SMP x86_64 GNU/Linux", "", 0),
        "numactl --hardware": ("available: 1 nodes (0)\nnode 0 cpus: 0 1\nnode 0 size: 1000 MB\n", "", 0),
        "cat /etc/os-release": ('NAME="Ubuntu"\nVERSION_ID="24.04"\nPRETTY_NAME="Ubuntu 24.04 LTS"\n', "", 0),
        "cat /proc/cmdline": ("BOOT_IMAGE=/vmlinuz iommu=pt intel_iommu=on", "", 0),
        "sysctl -a": ("vm.swappiness = 1\nkernel.numa_balancing = 0\n", "", 0),
        "lspci -D": ("0000:01:00.0 VGA compatible controller: NVIDIA Corporation Device\n", "", 0),
        "lsmod": ("nvidia 123 0\nmlx5_core 456 0\n", "", 0),
        "printenv": ("CUDA_HOME=/usr/local/cuda\nNCCL_DEBUG=INFO\n", "", 0),
        "cat /proc/driver/nvidia/version": ("NVRM version: NVIDIA UNIX x86_64 Kernel Module  550.54.15", "", 0),
        "cat /usr/local/cuda/version.json": ('{"cuda":{"version":"12.4.1"}}', "", 0),
    }

    class FakeShellTool:
        def exists(self, command: str) -> bool:
            return command in {"lscpu", "nvidia-smi", "uname", "numactl", "lspci", "lsmod", "sysctl", "cat", "printenv"}

        def run(self, command: str, timeout=None):
            stdout, stderr, exit_code = command_map.get(command, ("", "missing", 1))
            return {"stdout": stdout, "stderr": stderr, "exit_code": exit_code}

    inspector = SystemInspector(shell_tool=FakeShellTool())
    result = inspector.inspect()

    assert result.status in {"success", "partial_success"}
    assert result.cpu.architecture == "x86_64"
    assert result.gpus[0].name == "NVIDIA H100"
    assert result.software.os.pretty_name == "Ubuntu 24.04 LTS"
    assert "nvidia-smi topo -m" in result.raw_command_notes
    assert result.raw_command_outputs["lscpu"].startswith("Architecture: x86_64")
    assert "CUDA_HOME=/usr/local/cuda" in result.raw_command_outputs["printenv"]
    assert result.raw_command_outputs["cat /proc/meminfo"] == "missing"
