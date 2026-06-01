from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from app.agent import BenchmarkAgent
from app.logging_utils import configure_logging
from app.models import BenchmarkSuiteResult, FinalRunResult, RunRequest
from reports.generator import ReportGenerator


app = typer.Typer(help="Agentic-AI-Benchmark-Agent CLI")
console = Console()


def _agent(settings_path: str | None, profiles_path: str | None) -> BenchmarkAgent:
    configure_logging()
    return BenchmarkAgent(settings_path=settings_path, profiles_path=profiles_path)


def _print_run_summary(final: FinalRunResult) -> None:
    table = Table(title="Benchmark Agent Summary")
    table.add_column("Section")
    table.add_column("Status")
    table.add_row("Inspection", final.inspection.status)
    table.add_row("NCCL AllReduce", final.benchmarks.nccl.status if final.benchmarks.nccl else "not_run")
    table.add_row(
        "NCCL AllToAll",
        final.benchmarks.nccl_alltoall.status if final.benchmarks.nccl_alltoall else "not_run",
    )
    table.add_row("NVBandwidth", final.benchmarks.nvbandwidth.status if final.benchmarks.nvbandwidth else "not_run")
    table.add_row("Overall", final.status)
    console.print(table)
    console.print_json(json.dumps(final.model_dump(mode="json"), indent=2))


@app.command()
def run(
    settings: str | None = typer.Option(None, help="Path to settings.yaml"),
    profiles: str | None = typer.Option(None, help="Path to benchmark_profiles.yaml"),
    output_dir: str | None = typer.Option(None, help="Directory for generated reports"),
    nccl_profile: str = typer.Option("default", help="NCCL profile name"),
    nvbandwidth_profile: str = typer.Option("default", help="NVBandwidth profile name"),
) -> None:
    agent = _agent(settings, profiles)
    result = agent.run(
        RunRequest(
            inspect_only=False,
            run_nccl=True,
            run_nvbandwidth=True,
            generate_reports=True,
            nccl_profile=nccl_profile,
            nvbandwidth_profile=nvbandwidth_profile,
            output_dir=output_dir,
        )
    )
    _print_run_summary(result)


@app.command()
def inspect(
    settings: str | None = typer.Option(None, help="Path to settings.yaml"),
    profiles: str | None = typer.Option(None, help="Path to benchmark_profiles.yaml"),
) -> None:
    agent = _agent(settings, profiles)
    inspection = agent.inspect()
    console.print_json(json.dumps(inspection.model_dump(mode="json"), indent=2))


@app.command()
def nccl(
    profile: str = typer.Option("default", help="NCCL profile name"),
    settings: str | None = typer.Option(None, help="Path to settings.yaml"),
    profiles: str | None = typer.Option(None, help="Path to benchmark_profiles.yaml"),
) -> None:
    agent = _agent(settings, profiles)
    result = {
        "all_reduce": agent.run_nccl(profile).model_dump(mode="json"),
        "alltoall": agent.run_nccl_alltoall(profile).model_dump(mode="json"),
    }
    console.print_json(json.dumps(result, indent=2))


@app.command()
def nvbandwidth(
    profile: str = typer.Option("default", help="NVBandwidth profile name"),
    settings: str | None = typer.Option(None, help="Path to settings.yaml"),
    profiles: str | None = typer.Option(None, help="Path to benchmark_profiles.yaml"),
) -> None:
    agent = _agent(settings, profiles)
    result = agent.run_nvbandwidth(profile)
    console.print_json(json.dumps(result.model_dump(mode="json"), indent=2))


@app.command("generate-report")
def generate_report(
    inspection_file: str = typer.Option(..., help="Path to saved inspection JSON"),
    benchmarks_file: str = typer.Option(..., help="Path to saved benchmark JSON"),
    output_dir: str = typer.Option("data/reports", help="Output directory"),
) -> None:
    inspection = json.loads(Path(inspection_file).read_text(encoding="utf-8"))
    benchmarks = json.loads(Path(benchmarks_file).read_text(encoding="utf-8"))
    final = FinalRunResult.model_validate(
        {
            "inspection": inspection,
            "benchmarks": BenchmarkSuiteResult.model_validate(benchmarks).model_dump(mode="json"),
            "report_paths": {},
            "status": inspection.get("status", "partial_success"),
            "warnings": inspection.get("warnings", []),
        }
    )
    paths = ReportGenerator(Path(output_dir)).generate(final)
    console.print_json(json.dumps(paths, indent=2))
