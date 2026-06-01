from __future__ import annotations

import json
from pathlib import Path

from app.models import BenchmarkResult, BenchmarkSuiteResult, FinalRunResult, RunRequest, Settings
from benchmarks.nccl_runner import NcclBenchmarkRunner
from benchmarks.nvbandwidth_runner import NvBandwidthBenchmarkRunner
from inspection.system_inspector import SystemInspector
from reports.generator import ReportGenerator


class BenchmarkOrchestrator:
    def __init__(
        self,
        settings: Settings,
        benchmark_profiles: dict,
        system_inspector: SystemInspector | None = None,
        nccl_runner: NcclBenchmarkRunner | None = None,
        nvbandwidth_runner: NvBandwidthBenchmarkRunner | None = None,
    ) -> None:
        self.settings = settings
        self.benchmark_profiles = benchmark_profiles
        self.system_inspector = system_inspector or SystemInspector()
        self.nccl_runner = nccl_runner or NcclBenchmarkRunner()
        self.nvbandwidth_runner = nvbandwidth_runner or NvBandwidthBenchmarkRunner()

    def inspect_system(self):
        return self.system_inspector.inspect(
            selected_env_vars=self.settings.selected_env_vars,
            system_parameters=self.settings.system_parameters,
        )

    def run_nccl(self, profile_name: str = "default") -> BenchmarkResult:
        profile = self.benchmark_profiles.get("nccl", {}).get(profile_name)
        if profile is None:
            return BenchmarkResult(
                name="nccl",
                status="failed",
                profile_name=profile_name,
                error=f"NCCL profile not found: {profile_name}",
            )
        return self.nccl_runner.run(profile)

    def run_nvbandwidth(self, profile_name: str = "default") -> BenchmarkResult:
        profile = self.benchmark_profiles.get("nvbandwidth", {}).get(profile_name)
        if profile is None:
            return BenchmarkResult(
                name="nvbandwidth",
                status="failed",
                profile_name=profile_name,
                error=f"NVBandwidth profile not found: {profile_name}",
            )
        return self.nvbandwidth_runner.run(profile)

    def run(self, request: RunRequest) -> FinalRunResult:
        inspection = self.inspect_system()
        benchmarks = BenchmarkSuiteResult()
        warnings = list(inspection.warnings)

        if not request.inspect_only and request.run_nccl and self.settings.enable_benchmarks.get("nccl", True):
            benchmarks.nccl = self.run_nccl(request.nccl_profile)
            warnings.extend(benchmarks.nccl.warnings)
            if benchmarks.nccl.error:
                warnings.append(benchmarks.nccl.error)
        if not request.inspect_only and request.run_nvbandwidth and self.settings.enable_benchmarks.get("nvbandwidth", True):
            benchmarks.nvbandwidth = self.run_nvbandwidth(request.nvbandwidth_profile)
            warnings.extend(benchmarks.nvbandwidth.warnings)
            if benchmarks.nvbandwidth.error:
                warnings.append(benchmarks.nvbandwidth.error)

        statuses = [inspection.status]
        if benchmarks.nccl:
            statuses.append("success" if benchmarks.nccl.status == "passed" else "partial_success")
        if benchmarks.nvbandwidth:
            statuses.append("success" if benchmarks.nvbandwidth.status == "passed" else "partial_success")
        overall_status = "failed" if all(status == "failed" for status in statuses) else "partial_success"
        if statuses and all(status == "success" for status in statuses):
            overall_status = "success"

        final = FinalRunResult(
            inspection=inspection,
            benchmarks=benchmarks,
            report_paths={},
            status=overall_status,
            warnings=list(dict.fromkeys(warnings)),
        )

        self._persist_structured_result(final, request.output_dir)
        if request.generate_reports:
            output_dir = Path(request.output_dir or self.settings.report_output_dir)
            final.report_paths = ReportGenerator(output_dir=output_dir).generate(final)
        return final

    def _persist_structured_result(self, final: FinalRunResult, output_dir: str | None) -> None:
        results_dir = Path(output_dir or self.settings.result_output_dir)
        results_dir.mkdir(parents=True, exist_ok=True)
        result_path = results_dir / "latest_result.json"
        result_path.write_text(json.dumps(final.model_dump(mode="json"), indent=2), encoding="utf-8")
