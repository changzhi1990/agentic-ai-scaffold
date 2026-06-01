from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseShellTool(ABC):
    @abstractmethod
    def exists(self, command: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(self, command: str, timeout: int | None = None) -> dict[str, Any]:
        raise NotImplementedError


class BaseFileTool(ABC):
    @abstractmethod
    def read(self, path: str) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    def exists(self, path: str) -> dict[str, Any]:
        raise NotImplementedError
