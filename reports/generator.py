from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.models import FinalRunResult
from reports.json_report import write_json_report
from reports.markdown_report import write_markdown_report


class ReportGenerator:
    def __init__(self, output_dir: Path | str) -> None:
        self.output_dir = Path(output_dir)

    def generate(self, result: FinalRunResult) -> dict[str, str]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        json_path = self.output_dir / f"benchmark_report_{timestamp}.json"
        markdown_path = self.output_dir / f"benchmark_report_{timestamp}.md"
        write_json_report(result, json_path)
        write_markdown_report(result, markdown_path)
        return {"json": str(json_path), "markdown": str(markdown_path)}
