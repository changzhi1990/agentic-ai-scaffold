from inspection.parsers import parse_nvidia_smi_topology_output


def test_parse_nvidia_smi_topology_output_matrix() -> None:
    raw = """\tGPU0\tGPU1\tNIC0\tCPU Affinity\tNUMA Affinity
GPU0\t X \tNV4\tPIX\t0-47\t0
GPU1\tNV4\t X \tPHB\t0-47\t0
NIC0\tPIX\tPHB\t X \t0-47\t0

Legend:
  X    = Self
  SYS  = Path traversing PCIe as well as the SMP interconnect between NUMA nodes
"""
    parsed = parse_nvidia_smi_topology_output(raw)

    assert parsed["headers"][:3] == ["GPU0", "GPU1", "NIC0"]
    assert parsed["matrix"]["GPU0"]["GPU1"] == "NV4"
    assert parsed["matrix"]["GPU1"]["NIC0"] == "PHB"
    assert parsed["gpu_nic_links"][0]["gpu"] == "GPU0"


def test_parse_nvidia_smi_topology_output_strips_ansi_and_keeps_gpu0_row() -> None:
    raw = """\x1b[4mGPU0\tGPU1\tNIC0\tCPU Affinity\tNUMA Affinity\tGPU NUMA ID\x1b[0m
GPU0\t X \tNODE\tPIX\t0-47\t0\tN/A
GPU1\tNODE\t X \tPHB\t0-47\t0\tN/A
NIC0\tPIX\tPHB\t X \t\t\t
"""
    parsed = parse_nvidia_smi_topology_output(raw)

    assert parsed["headers"][0] == "GPU0"
    assert parsed["matrix"]["GPU0"]["GPU0"] == "X"
    assert parsed["matrix"]["GPU0"]["GPU1"] == "NODE"
    assert parsed["matrix"]["GPU1"]["NIC0"] == "PHB"
