from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.models import BenchmarkMetrics, BenchmarkProfile, BenchmarkResult
from benchmarks.metrics import build_metrics
from tools.shell_tool import ShellTool


class BaseBenchmarkRunner(ABC):
    benchmark_name: str = "benchmark"
    latency_metric_key: str | None = None

    def __init__(self, shell_tool: ShellTool | Any | None = None) -> None:
        self.shell_tool = shell_tool or ShellTool()

    @abstractmethod
    def parse_output(self, raw_text: str) -> dict:
        raise NotImplementedError

    def run(self, profile: dict | BenchmarkProfile) -> BenchmarkResult:
        config = profile if isinstance(profile, BenchmarkProfile) else BenchmarkProfile.model_validate(profile)
        if not config.enabled:
            return BenchmarkResult(name=self.benchmark_name, status="skipped", profile_name=config.name)
        if not self.shell_tool.exists(config.binary_path):
            return BenchmarkResult(
                name=self.benchmark_name,
                status="missing_binary",
                profile_name=config.name,
                binary_path=config.binary_path,
                error=f"Benchmark binary not found: {config.binary_path}",
                warnings=[f"{self.benchmark_name} binary not found"],
            )

        command = ShellTool.format_command(config.binary_path, config.args, env=config.env)
        parsed_runs = []
        stdout_parts = []
        stderr_parts = []
        exit_code = 0
        warnings: list[str] = []

        for _ in range(config.repetitions):
            executed = self.shell_tool.run(command, timeout=config.timeout_seconds)
            stdout_parts.append(executed.get("stdout", ""))
            stderr_parts.append(executed.get("stderr", ""))
            exit_code = executed.get("exit_code", 1)
            if executed.get("timed_out"):
                return BenchmarkResult(
                    name=self.benchmark_name,
                    status="timeout",
                    profile_name=config.name,
                    binary_path=config.binary_path,
                    command=command,
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                    exit_code=exit_code,
                    completed_runs=len(parsed_runs),
                    error=f"Timed out after {config.timeout_seconds} seconds",
                )
            if exit_code != 0:
                return BenchmarkResult(
                    name=self.benchmark_name,
                    status="failed",
                    profile_name=config.name,
                    binary_path=config.binary_path,
                    command=command,
                    stdout="\n".join(stdout_parts),
                    stderr="\n".join(stderr_parts),
                    exit_code=exit_code,
                    completed_runs=len(parsed_runs),
                    error="Benchmark process exited with a non-zero status",
                )
            parsed = self.parse_output(executed.get("stdout", ""))
            if not parsed.get("samples"):
                warnings.append("No benchmark samples were parsed from command output")
            parsed_runs.append(parsed)

        metrics: BenchmarkMetrics = build_metrics(parsed_runs, latency_key=self.latency_metric_key)
        status = "passed" if metrics.samples else "failed"
        return BenchmarkResult(
            name=self.benchmark_name,
            status=status,
            profile_name=config.name,
            binary_path=config.binary_path,
            command=command,
            metrics=metrics,
            parsed_output={"runs": parsed_runs},
            stdout="\n".join(stdout_parts),
            stderr="\n".join(stderr_parts),
            exit_code=exit_code,
            completed_runs=config.repetitions,
            warnings=warnings,
            error=None if metrics.samples else "Unable to parse benchmark metrics from output",
        )
