"""Event log JSONL thread-safe: ts, event, dan field bebas (PLAN.md P1-T4)."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TextIO


class EventLog:
    """Penulis event JSONL yang aman dipakai banyak thread."""

    def __init__(self, path: Path, clock: Callable[[], float] = time.time) -> None:
        self._path = path
        self._clock = clock
        self._lock = threading.Lock()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._handle: TextIO = path.open("a", encoding="utf-8")

    @property
    def path(self) -> Path:
        """Lokasi file event."""
        return self._path

    def emit(self, event: str, **fields: Any) -> dict[str, Any]:
        """Tulis satu event dan kembalikan entri yang ditulis."""
        entry: dict[str, Any] = {"ts": self._clock(), "event": event}
        entry.update(fields)
        line = json.dumps(entry, ensure_ascii=False)
        with self._lock:
            self._handle.write(line + "\n")
            self._handle.flush()
        return entry

    def close(self) -> None:
        """Tutup file event."""
        with self._lock:
            if not self._handle.closed:
                self._handle.close()

    def __enter__(self) -> EventLog:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


def read_events(path: Path) -> list[dict[str, Any]]:
    """Baca seluruh event dari file JSONL."""
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                rows.append(json.loads(stripped))
    return rows
