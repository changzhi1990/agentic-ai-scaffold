from __future__ import annotations

from fastapi import FastAPI

from app.agent import BenchmarkAgent
from app.logging_utils import configure_logging
from app.models import BenchmarkRequest, RunRequest


configure_logging()
api = FastAPI(title="Agentic-AI-Benchmark-Agent", version="0.1.0")


def _agent() -> BenchmarkAgent:
    return BenchmarkAgent()


@api.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@api.post("/inspect")
def inspect() -> dict:
    return _agent().inspect().model_dump(mode="json")


@api.post("/benchmark/nccl")
def benchmark_nccl(payload: BenchmarkRequest | None = None) -> dict:
    request = payload or BenchmarkRequest()
    return _agent().run_nccl(request.profile_name).model_dump(mode="json")


@api.post("/benchmark/nvbandwidth")
def benchmark_nvbandwidth(payload: BenchmarkRequest | None = None) -> dict:
    request = payload or BenchmarkRequest()
    return _agent().run_nvbandwidth(request.profile_name).model_dump(mode="json")


@api.post("/run")
def run(payload: RunRequest | None = None) -> dict:
    request = payload or RunRequest()
    return _agent().run(request).model_dump(mode="json")
