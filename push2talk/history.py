"""Thread-safe recognition history with fixed max size."""

from __future__ import annotations

import threading
from collections import deque


class RecognitionHistory:
    def __init__(self, maxlen: int = 10) -> None:
        self._items: deque[str] = deque(maxlen=maxlen)
        self._lock = threading.Lock()

    def add(self, text: str) -> None:
        with self._lock:
            self._items.appendleft(text)

    def get_items(self) -> list[str]:
        with self._lock:
            return list(self._items)

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
