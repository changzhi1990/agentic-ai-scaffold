"""Simple in-process memory store for recent agent runs."""

from __future__ import annotations

from collections import deque

from app.models import TaskResponse


class RunMemory:
    """Stores recent task responses for auditability and debugging."""

    def __init__(self, max_items: int = 100) -> None:
        self._items: deque[TaskResponse] = deque(maxlen=max_items)

    def add(self, response: TaskResponse) -> None:
        self._items.append(response)

    def recent(self) -> list[TaskResponse]:
        return list(self._items)
