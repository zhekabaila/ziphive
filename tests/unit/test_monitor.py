"""UT-MON-01..03: monitor heartbeat, requeue, batas attempts, idempotensi (PLAN.md Fase 6)."""

from __future__ import annotations

import hashlib
import socket
from pathlib import Path

from pcomp.compressor import compress
from pcomp.master.collector import Collector
from pcomp.master.monitor import Monitor
from pcomp.master.scheduler import DynamicScheduler
from pcomp.master.server import MasterState, WorkerSession
from pcomp.metrics.events import EventLog, read_events
from pcomp.protocol import make_header
from pcomp.tasks import Task


class FakeClock:
    """Jam palsu yang dapat digeser tanpa menunggu waktu nyata."""

    def __init__(self, now: float = 0.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def make_task(task_id: int = 0, length: int = 100) -> Task:
    return Task(task_id=task_id, file=f"f{task_id}.bin", index=0, offset=0, length=length)


def make_session(worker_id: str) -> WorkerSession:
    return WorkerSession(worker_id=worker_id, hostname="uji", procs=1, sock=socket.socket())


def make_state(
    tmp_path: Path,
    tasks: list[Task],
    clock: FakeClock,
    *,
    max_attempts: int = 3,
) -> MasterState:
    collector = Collector(
        tmp_path, algo="gzip", level=1, chunk_mb=1, repeat=1, total_tasks=len(tasks)
    )
    events = EventLog(tmp_path / "events.jsonl", clock=clock)
    return MasterState(
        tasks, collector, events, DynamicScheduler(), max_attempts=max_attempts, clock=clock
    )


def event_names(state: MasterState) -> list[str]:
    return [item["event"] for item in read_events(state.events.path)]


def test_heartbeat_timeout_marks_dead_and_requeues(tmp_path: Path) -> None:
    """UT-MON-01: jam palsu melewati timeout menandai DEAD dan mengembalikan task PENDING."""
    clock = FakeClock(100.0)
    state = make_state(tmp_path, [make_task()], clock)
    session = make_session("w1")
    state.register(session)
    state.begin()
    state.add_credits("w1", 1)
    assert state.take("w1") is not None

    monitor = Monitor(state, timeout=6.0, interval=1.0, clock=clock)
    clock.now = 105.9
    assert monitor.sweep() == []
    clock.now = 106.1
    assert monitor.sweep() == ["w1"]

    assert state.table.counts()["PENDING"] == 1
    names = event_names(state)
    assert "worker_dead" in names
    assert "task_requeued" in names
    session.sock.close()


def test_attempt_limit_marks_task_failed(tmp_path: Path) -> None:
    """UT-MON-02: task yang gagal sampai batas attempts menjadi FAILED, bukan requeue lagi."""
    clock = FakeClock(0.0)
    state = make_state(tmp_path, [make_task()], clock, max_attempts=2)

    first = make_session("w1")
    state.register(first)
    state.begin()
    state.add_credits("w1", 1)
    state.take("w1")
    state.drop_worker("w1", "heartbeat timeout", 1.0)
    assert state.table.counts()["PENDING"] == 1

    second = make_session("w2")
    state.register(second)
    state.add_credits("w2", 1)
    state.take("w2")
    state.drop_worker("w2", "heartbeat timeout", 2.0)

    assert state.table.counts()["FAILED"] == 1
    assert state.table.counts()["PENDING"] == 0
    names = event_names(state)
    assert names.count("task_requeued") == 1
    assert names.count("task_failed") == 1
    assert state.drop_worker("w2", "lagi", 3.0) == []
    first.sock.close()
    second.sock.close()


def test_late_and_duplicate_results_are_ignored(tmp_path: Path) -> None:
    """UT-MON-03: hasil ganda dan hasil terlambat dari Worker DEAD diabaikan serta dicatat."""
    clock = FakeClock(0.0)
    data = b"konten" * 200
    first_task = make_task(task_id=0, length=len(data))
    first_task.sha256 = hashlib.sha256(data).hexdigest()
    state = make_state(tmp_path, [first_task, make_task(task_id=1, length=len(data))], clock)
    session = make_session("w1")
    state.register(session)
    state.begin()
    state.add_credits("w1", 1)
    state.take("w1")

    packed = compress("gzip", 1, data)
    header = make_header(
        "RESULT",
        task_id=0,
        ok=True,
        orig_size=len(data),
        comp_size=len(packed),
        sha256_in=first_task.sha256,
        compute_sec=0.01,
        error=None,
    )

    assert state.handle_result(session, header, packed) == "done"
    assert state.handle_result(session, header, packed) == "ignored"

    state.add_credits("w1", 1)
    assert state.take("w1") is not None
    state.drop_worker("w1", "koneksi putus", 1.0)
    late_header = make_header(
        "RESULT",
        task_id=1,
        ok=True,
        orig_size=len(data),
        comp_size=len(packed),
        sha256_in=first_task.sha256,
        compute_sec=0.01,
        error=None,
    )
    assert state.handle_result(session, late_header, packed) == "ignored"

    names = event_names(state)
    assert names.count("late_or_duplicate") == 2
    session.sock.close()
