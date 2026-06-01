from __future__ import annotations

import json
from pathlib import Path

from app.models import FinalRunResult


def write_json_report(result: FinalRunResult, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
    return output_path
