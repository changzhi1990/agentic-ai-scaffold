from __future__ import annotations

from benchmarks.base import BaseBenchmarkRunner
from benchmarks.parsers import parse_nccl_output


class NcclBenchmarkRunner(BaseBenchmarkRunner):
    benchmark_name = "nccl"
    latency_metric_key = "average_latency_ms"

    def parse_output(self, raw_text: str) -> dict:
        return parse_nccl_output(raw_text)
