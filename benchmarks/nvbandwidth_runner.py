from __future__ import annotations

from benchmarks.base import BaseBenchmarkRunner
from benchmarks.parsers import parse_nvbandwidth_output


class NvBandwidthBenchmarkRunner(BaseBenchmarkRunner):
    benchmark_name = "nvbandwidth"
    latency_metric_key = "average_latency_us"

    def parse_output(self, raw_text: str) -> dict:
        return parse_nvbandwidth_output(raw_text)
