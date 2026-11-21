"""UT-SCH-01..06: scheduler static/dynamic dan metrik beban (PLAN.md P5-T1..T3, P5-T5)."""

from __future__ import annotations

import socket
from pathlib import Path

import pytest

from pcomp.master.collector import Collector
from pcomp.master.scheduler import (
    DynamicScheduler,
    StaticScheduler,
    build_scheduler,
    imbalance_factor,
)
from pcomp.master.server import MasterState, WorkerSession
from pcomp.metrics.events import EventLog
from pcomp.tasks import Task, TaskTable


def make_tasks(lengths: list[int]) -> list[Task]:
    return [
        Task(task_id=index, file=f"f{index}.bin", index=index, offset=0, length=length)
        for index, length in enumerate(lengths)
    ]


def make_session(worker_id: str) -> WorkerSession:
    return WorkerSession(worker_id=worker_id, hostname="uji", procs=1, sock=socket.socket())


def make_state(
    tmp_path: Path, tasks: list[Task], scheduler: DynamicScheduler | StaticScheduler
) -> MasterState:
    collector = Collector(
        tmp_path, algo="sim", level=1, chunk_mb=1, repeat=1, total_tasks=len(tasks)
    )
    events = EventLog(tmp_path / "events.jsonl")
    return MasterState(tasks, collector, events, scheduler)


def test_dynamic_takes_largest_first() -> None:
    """UT-SCH-01: LPT memilih task terbesar, seri dipecah task_id terkecil."""
    table = TaskTable(make_tasks([10, 50, 20, 50]))
    scheduler = DynamicScheduler()

    order = [scheduler.take(table, "w1", 0.0).task_id for _ in range(4)]  # type: ignore[union-attr]

    assert order == [1, 3, 2, 0]
    assert table.counts() == {"PENDING": 0, "ASSIGNED": 4, "DONE": 0, "FAILED": 0}


def test_static_partition_is_round_robin_and_even() -> None:
    """UT-SCH-02: partisi static membagi task round-robin, selisih maksimal satu."""
    table = TaskTable(make_tasks([1] * 7))
    scheduler = StaticScheduler()
    scheduler.start(table, ["w1", "w2", "w3"])

    assigned: dict[str, list[int]] = {}
    for worker_id in ("w1", "w2", "w3"):
        assigned[worker_id] = []
        while True:
            task = scheduler.take(table, worker_id, 0.0)
            if task is None:
                break
            assigned[worker_id].append(task.task_id)

    assert assigned == {"w1": [0, 3, 6], "w2": [1, 4], "w3": [2, 5]}
    counts = [len(items) for items in assigned.values()]
    assert max(counts) - min(counts) <= 1


def test_credit_exhausted_then_refilled(tmp_path: Path) -> None:
    """UT-SCH-03: dispatch berhenti saat credit habis dan lanjut setelah credit baru."""
    state = make_state(tmp_path, make_tasks([10, 20]), DynamicScheduler())
    state.register(make_session("w1"))
    state.begin()

    state.add_credits("w1", 1)
    first = state.take("w1")
    second = state.take("w1")

    assert first is not None and first.length == 20
    assert second is None

    state.add_credits("w1", 1)
    third = state.take("w1")
    assert third is not None and third.length == 10
    assert state.table.counts()["ASSIGNED"] == 2


def test_static_serves_only_its_own_queue() -> None:
    """UT-SCH-04: static tidak mengambil jatah Worker lain dan menolak Worker asing."""
    table = TaskTable(make_tasks([5] * 4))
    scheduler = StaticScheduler()
    scheduler.start(table, ["w1", "w2"])

    assert scheduler.take(table, "w9", 0.0) is None
    owned = [scheduler.take(table, "w1", 0.0) for _ in range(3)]
    assert [task.task_id for task in owned if task is not None] == [0, 2]
    assert scheduler.take(table, "w1", 0.0) is None
    assert table.counts()["PENDING"] == 2


def test_imbalance_factor() -> None:
    """UT-SCH-05: imbalance = max(busy) / mean(busy); 1.0 bila seimbang atau kosong."""
    assert imbalance_factor([1.0, 1.0, 1.0]) == pytest.approx(1.0)
    assert imbalance_factor([2.0, 1.0, 0.0]) == pytest.approx(2.0)
    assert imbalance_factor([]) == pytest.approx(1.0)
    assert imbalance_factor([0.0, 0.0]) == pytest.approx(1.0)


def test_build_scheduler_by_name() -> None:
    """UT-SCH-06: nama scheduler dari konfigurasi dipetakan ke kelas yang tepat."""
    assert build_scheduler("static").name == "static"
    assert build_scheduler("dynamic").name == "dynamic"
    with pytest.raises(ValueError):
        build_scheduler("lain")


def test_static_moves_dead_queue_to_orphans() -> None:
    """UT-SCH-07: jatah Worker mati dipindahkan ke antrean bersama Worker yang hidup."""
    table = TaskTable(make_tasks([1] * 4))
    scheduler = StaticScheduler()
    scheduler.start(table, ["w1", "w2"])

    scheduler.on_worker_dead("w1")
    taken: list[int] = []
    while True:
        task = scheduler.take(table, "w2", 0.0)
        if task is None:
            break
        taken.append(task.task_id)

    assert sorted(taken) == [0, 1, 2, 3]


def test_static_requeue_is_served_again() -> None:
    """UT-SCH-08: task yang di-requeue dapat diambil lagi oleh Worker hidup."""
    table = TaskTable(make_tasks([1] * 2))
    scheduler = StaticScheduler()
    scheduler.start(table, ["w1", "w2"])
    assigned = scheduler.take(table, "w1", 0.0)
    assert assigned is not None
    table.requeue_task(assigned.task_id, now=1.0, max_attempts=3, reason="uji")
    scheduler.on_requeue(assigned)

    taken = [scheduler.take(table, "w2", 0.0) for _ in range(2)]
    assert sorted(task.task_id for task in taken if task is not None) == [0, 1]
