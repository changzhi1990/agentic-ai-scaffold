from benchmarks.nccl_runner import NcclBenchmarkRunner


def test_nccl_runner_parses_metrics_from_output() -> None:
    class FakeShellTool:
        def exists(self, command: str) -> bool:
            return True

        def run(self, command: str, timeout=None):
            stdout = """
# nThread 1 nGpus 2 minBytes 8 maxBytes 67108864 step: 2
      size         count    type   redop    root     time   algbw   busbw #wrong
   1048576        262144   float     sum      -1    12.34   80.11   91.22      0
   2097152        524288   float     sum      -1    20.00   85.50   93.40      0
"""
            return {"stdout": stdout, "stderr": "", "exit_code": 0}

    runner = NcclBenchmarkRunner(shell_tool=FakeShellTool())
    result = runner.run(
        {
            "name": "smoke",
            "binary_path": "/opt/nccl-tests/build/all_reduce_perf",
            "args": ["-b", "1M", "-e", "2M", "-g", "2"],
            "timeout_seconds": 30,
        }
    )

    assert result.status == "passed"
    assert result.metrics.peak_bandwidth_gbps == 93.4
    assert result.metrics.average_latency_ms == 16.17


def test_nccl_runner_handles_missing_binary() -> None:
    class FakeShellTool:
        def exists(self, command: str) -> bool:
            return False

        def run(self, command: str, timeout=None):
            raise AssertionError("run should not be called")

    runner = NcclBenchmarkRunner(shell_tool=FakeShellTool())
    result = runner.run({"binary_path": "/missing/all_reduce_perf", "args": []})

    assert result.status == "missing_binary"
    assert "not found" in result.error.lower()

