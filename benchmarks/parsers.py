from __future__ import annotations

import re
from statistics import mean


def parse_nccl_output(raw_text: str) -> dict:
    samples = []
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("size"):
            continue
        parts = stripped.split()
        if len(parts) < 8 or not parts[0].isdigit():
            continue
        sample = {
            "label": parts[0],
            "time_ms": float(parts[5]),
            "algbw_gbps": float(parts[6]),
            "busbw_gbps": float(parts[7]),
        }
        samples.append(sample)
    if not samples:
        return {"samples": [], "peak_bandwidth_gbps": None, "average_latency_ms": None}
    return {
        "samples": samples,
        "peak_bandwidth_gbps": max(sample["busbw_gbps"] for sample in samples),
        "average_bandwidth_gbps": mean(sample["busbw_gbps"] for sample in samples),
        "average_latency_ms": round(mean(sample["time_ms"] for sample in samples), 2),
    }


def parse_nvbandwidth_output(raw_text: str) -> dict:
    line_pattern = re.compile(
        r"(?P<src>GPU\d+)\s*->\s*(?P<dst>GPU\d+)\s*:\s*bandwidth\s*(?P<bw>[\d.]+)\s*GB/s\s*latency\s*(?P<lat>[\d.]+)\s*us",
        flags=re.IGNORECASE,
    )
    samples = []
    for line in raw_text.splitlines():
        match = line_pattern.search(line)
        if not match:
            continue
        samples.append(
            {
                "label": f"{match.group('src')}->{match.group('dst')}",
                "bandwidth_gbps": float(match.group("bw")),
                "latency_us": float(match.group("lat")),
            }
        )

    if samples:
        return {
            "samples": samples,
            "peak_bandwidth_gbps": max(sample["bandwidth_gbps"] for sample in samples),
            "average_bandwidth_gbps": mean(sample["bandwidth_gbps"] for sample in samples),
            "average_latency_us": round(mean(sample["latency_us"] for sample in samples), 2),
        }

    matrix_lines = raw_text.splitlines()
    for index, line in enumerate(matrix_lines):
        if "bandwidth (GB/s)" not in line:
            continue
        if index + 1 >= len(matrix_lines):
            continue
        header_tokens = matrix_lines[index + 1].split()
        if not header_tokens or not all(token.isdigit() for token in header_tokens):
            continue
        columns = header_tokens
        for row_line in matrix_lines[index + 2 :]:
            stripped = row_line.strip()
            if not stripped:
                break
            row_tokens = stripped.split()
            if len(row_tokens) != len(columns) + 1 or not row_tokens[0].isdigit():
                break
            row_id = row_tokens[0]
            for column_id, value in zip(columns, row_tokens[1:], strict=False):
                if value.upper() == "N/A":
                    continue
                try:
                    bandwidth = float(value)
                except ValueError:
                    continue
                samples.append(
                    {
                        "label": f"GPU{row_id}->GPU{column_id}",
                        "bandwidth_gbps": bandwidth,
                    }
                )

    if not samples:
        return {"samples": [], "peak_bandwidth_gbps": None, "average_latency_us": None}
    return {
        "samples": samples,
        "peak_bandwidth_gbps": max(sample["bandwidth_gbps"] for sample in samples),
        "average_bandwidth_gbps": mean(sample["bandwidth_gbps"] for sample in samples),
        "average_latency_us": round(mean(sample["latency_us"] for sample in samples), 2)
        if all(sample.get("latency_us") is not None for sample in samples)
        else None,
    }
