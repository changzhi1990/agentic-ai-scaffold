from benchmarks.nvbandwidth_runner import NvBandwidthBenchmarkRunner


def test_nvbandwidth_runner_parses_metrics_from_output() -> None:
    class FakeShellTool:
        def exists(self, command: str) -> bool:
            return True

        def run(self, command: str, timeout=None):
            stdout = """
Device to Device Bandwidth, 2 GPUs
GPU0 -> GPU1 : bandwidth 312.50 GB/s latency 2.30 us
GPU1 -> GPU0 : bandwidth 311.00 GB/s latency 2.50 us
"""
            return {"stdout": stdout, "stderr": "", "exit_code": 0}

    runner = NvBandwidthBenchmarkRunner(shell_tool=FakeShellTool())
    result = runner.run(
        {
            "name": "pairwise",
            "binary_path": "/opt/nvbandwidth/nvbandwidth",
            "args": ["--gpu-list", "0,1"],
            "timeout_seconds": 30,
        }
    )

    assert result.status == "passed"
    assert result.metrics.peak_bandwidth_gbps == 312.5
    assert result.metrics.average_latency_us == 2.4


def test_nvbandwidth_runner_parses_matrix_bandwidth_output() -> None:
    class FakeShellTool:
        def exists(self, command: str) -> bool:
            return True

        def run(self, command: str, timeout=None):
            stdout = """
Running device_to_device_memcpy_read_ce.
memcpy CE GPU(row) -> GPU(column) bandwidth (GB/s)
           0         1         2
 0       N/A     56.51     41.56
 1     56.51       N/A     44.82
 2     45.84     41.59       N/A

SUM device_to_device_memcpy_read_ce 286.83
COEFFICIENT_OF_VARIATION device_to_device_memcpy_read_ce 0.13
"""
            return {"stdout": stdout, "stderr": "", "exit_code": 0}

    runner = NvBandwidthBenchmarkRunner(shell_tool=FakeShellTool())
    result = runner.run(
        {
            "name": "matrix",
            "binary_path": "/opt/nvbandwidth/nvbandwidth",
            "args": ["--testcase", "device_to_device_memcpy_read_ce"],
            "timeout_seconds": 30,
        }
    )

    assert result.status == "passed"
    assert result.testcase == "device_to_device_memcpy_read_ce"
    assert result.command == "/opt/nvbandwidth/nvbandwidth --testcase device_to_device_memcpy_read_ce"
    assert result.metrics.peak_bandwidth_gbps == 56.51
    assert result.metrics.average_bandwidth_gbps == 47.8
    assert len(result.metrics.samples) == 6
