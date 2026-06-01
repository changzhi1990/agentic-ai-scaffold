from __future__ import annotations

from pathlib import Path

from app.models import FinalRunResult
from benchmarks.nccl_runner import NcclBenchmarkRunner
from benchmarks.nvbandwidth_runner import NvBandwidthBenchmarkRunner
from reports.generator import ReportGenerator
from tools.file_tool import FileTool
from tools.parser_tool import ParserTool
from tools.shell_tool import ShellTool


class ToolRegistry:
    def __init__(self) -> None:
        self.shell_tool = ShellTool()
        self.file_tool = FileTool()
        self.parser_tool = ParserTool()

    def run_shell_command(self, command: str, timeout: int | None = None) -> dict:
        return self.shell_tool.run(command, timeout=timeout)

    def read_file(self, path: str) -> dict:
        return self.file_tool.read(path)

    def file_exists(self, path: str) -> dict:
        return self.file_tool.exists(path)

    def parse_command_output(self, parser_name: str, raw_text: str) -> dict:
        return {"parsed": self.parser_tool.parse(parser_name, raw_text)}

    def run_nccl_benchmark(self, profile: dict) -> dict:
        runner = NcclBenchmarkRunner(shell_tool=self.shell_tool)
        return {"result": runner.run(profile).model_dump(mode="json")}

    def run_nvbandwidth_benchmark(self, profile: dict) -> dict:
        runner = NvBandwidthBenchmarkRunner(shell_tool=self.shell_tool)
        return {"result": runner.run(profile).model_dump(mode="json")}

    def generate_report(self, inspection_result: dict, benchmark_results: dict, output_dir: str) -> dict:
        final = FinalRunResult.model_validate(
            {
                "inspection": inspection_result,
                "benchmarks": benchmark_results,
                "report_paths": {},
                "status": inspection_result.get("status", "partial_success"),
                "warnings": inspection_result.get("warnings", []),
            }
        )
        generator = ReportGenerator(output_dir=Path(output_dir))
        return {"report_paths": generator.generate(final)}
