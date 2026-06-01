from __future__ import annotations

from statistics import mean

from app.models import BenchmarkMetrics, BenchmarkSample


def build_metrics(parsed_runs: list[dict], latency_key: str | None = None) -> BenchmarkMetrics:
    all_samples: list[BenchmarkSample] = []
    peak_values = []
    avg_values = []
    latency_values = []

    for parsed in parsed_runs:
        for sample in parsed.get("samples", []):
            all_samples.append(
                BenchmarkSample(
                    label=sample["label"],
                    bandwidth_gbps=sample.get("busbw_gbps", sample.get("bandwidth_gbps")),
                    latency_ms=sample.get("time_ms"),
                    latency_us=sample.get("latency_us"),
                    raw=sample,
                )
            )
        if parsed.get("peak_bandwidth_gbps") is not None:
            peak_values.append(parsed["peak_bandwidth_gbps"])
        if parsed.get("average_bandwidth_gbps") is not None:
            avg_values.append(parsed["average_bandwidth_gbps"])
        if latency_key and parsed.get(latency_key) is not None:
            latency_values.append(parsed[latency_key])

    metrics = BenchmarkMetrics(samples=all_samples)
    if peak_values:
        metrics.peak_bandwidth_gbps = max(peak_values)
    if avg_values:
        metrics.average_bandwidth_gbps = round(mean(avg_values), 2)
    if latency_key == "average_latency_ms" and latency_values:
        metrics.average_latency_ms = round(mean(latency_values), 2)
    if latency_key == "average_latency_us" and latency_values:
        metrics.average_latency_us = round(mean(latency_values), 2)
    return metrics
