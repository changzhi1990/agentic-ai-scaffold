from __future__ import annotations

from app.config import load_benchmark_profiles, load_settings
from app.models import BenchmarkResult, FinalRunResult, InspectionResult, RunRequest
from app.orchestrator import BenchmarkOrchestrator


class BenchmarkAgent:
    def __init__(self, settings_path: str | None = None, profiles_path: str | None = None) -> None:
        self.settings = load_settings(settings_path)
        self.benchmark_profiles = load_benchmark_profiles(
            profiles_path or self.settings.benchmark_profiles_file
        )
        self.orchestrator = BenchmarkOrchestrator(self.settings, self.benchmark_profiles)

    def inspect(self) -> InspectionResult:
        return self.orchestrator.inspect_system()

    def run_nccl(self, profile_name: str = "default") -> BenchmarkResult:
        return self.orchestrator.run_nccl(profile_name)

    def run_nvbandwidth(self, profile_name: str = "default") -> BenchmarkResult:
        return self.orchestrator.run_nvbandwidth(profile_name)

    def run(self, request: RunRequest) -> FinalRunResult:
        return self.orchestrator.run(request)
