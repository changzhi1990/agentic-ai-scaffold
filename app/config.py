from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from app.exceptions import ConfigurationError
from app.models import BenchmarkProfile, Settings


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def resolve_path(path_like: str) -> Path:
    path = Path(path_like)
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigurationError(f"Expected mapping in YAML file: {path}")
    return data


def load_settings(path: str | None = None) -> Settings:
    config_path = resolve_path(path or os.getenv("AGENTIC_BENCHMARK_SETTINGS", "config/settings.yaml"))
    raw = _load_yaml(config_path)
    app_config = raw.get("app", raw)
    return Settings.model_validate(app_config)


def load_benchmark_profiles(path: str | None = None) -> dict[str, dict[str, BenchmarkProfile]]:
    profile_path = resolve_path(path or os.getenv("AGENTIC_BENCHMARK_PROFILES", "config/benchmark_profiles.yaml"))
    raw = _load_yaml(profile_path)
    parsed: dict[str, dict[str, BenchmarkProfile]] = {}
    for benchmark_name, profiles in raw.items():
        parsed[benchmark_name] = {}
        if not isinstance(profiles, dict):
            continue
        for profile_name, config in profiles.items():
            merged = {"name": profile_name, **(config or {})}
            parsed[benchmark_name][profile_name] = BenchmarkProfile.model_validate(merged)
    return parsed
