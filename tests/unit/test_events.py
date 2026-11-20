"""UT-EVT-01: event log JSONL ditulis dari banyak thread tanpa rusak."""

from __future__ import annotations

import json
import threading
from pathlib import Path

from pcomp.metrics.events import EventLog, read_events


def test_event_log_single_entry(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    with EventLog(path) as log:
        entry = log.emit("worker_dead", worker_id="w1")
    assert entry["event"] == "worker_dead"
    assert entry["worker_id"] == "w1"
    assert isinstance(entry["ts"], float)

    rows = read_events(path)
    assert len(rows) == 1
    assert rows[0]["event"] == "worker_dead"


def test_event_log_many_threads(tmp_path: Path) -> None:
    """UT-EVT-01: 8 thread x 50 event menghasilkan 400 baris JSON valid."""
    path = tmp_path / "events.jsonl"
    threads: list[threading.Thread] = []
    total = 8 * 50

    def worker(thread_id: int) -> None:
        for index in range(50):
            log.emit("task_done", thread=thread_id, seq=index)

    with EventLog(path) as log:
        for thread_id in range(8):
            thread = threading.Thread(target=worker, args=(thread_id,))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join(timeout=10.0)
            assert not thread.is_alive()

    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == total
    parsed = [json.loads(line) for line in lines]
    assert all(isinstance(row["ts"], float) for row in parsed)
    assert all(row["event"] == "task_done" for row in parsed)
    assert len(read_events(path)) == total


def test_event_log_extra_fields(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    with EventLog(path) as log:
        log.emit("task_requeued", task_id=17, attempts=2, nested={"a": 1})
    row = read_events(path)[0]
    assert row["task_id"] == 17
    assert row["attempts"] == 2
    assert row["nested"] == {"a": 1}


def test_event_log_append(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    with EventLog(path) as log:
        log.emit("satu")
    with EventLog(path) as log:
        log.emit("dua")
    assert [row["event"] for row in read_events(path)] == ["satu", "dua"]
