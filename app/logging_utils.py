import logging
import os


def configure_logging(level: str | None = None) -> None:
    log_level = (level or os.getenv("AGENTIC_BENCHMARK_LOG_LEVEL", "INFO")).upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
