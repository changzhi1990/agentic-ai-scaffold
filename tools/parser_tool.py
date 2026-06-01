from __future__ import annotations

from inspection import parsers as inspection_parsers
from benchmarks import parsers as benchmark_parsers


PARSER_REGISTRY = {
    "lscpu": inspection_parsers.parse_lscpu_output,
    "nvidia_smi_query": inspection_parsers.parse_nvidia_smi_query_output,
    "nvidia_smi_topology": inspection_parsers.parse_nvidia_smi_topology_output,
    "numactl_hardware": inspection_parsers.parse_numactl_hardware_output,
    "uname": inspection_parsers.parse_uname_output,
    "os_release": inspection_parsers.parse_os_release,
    "lspci": inspection_parsers.parse_lspci_output,
    "sysctl": inspection_parsers.parse_sysctl_output,
    "lsmod": inspection_parsers.parse_lsmod_output,
    "proc_cmdline": inspection_parsers.parse_proc_cmdline,
    "proc_meminfo": inspection_parsers.parse_proc_meminfo,
    "nccl_output": benchmark_parsers.parse_nccl_output,
    "nvbandwidth_output": benchmark_parsers.parse_nvbandwidth_output,
}


class ParserTool:
    def parse(self, parser_name: str, raw_text: str) -> dict:
        parser = PARSER_REGISTRY[parser_name]
        return parser(raw_text)
