"""UT-TBL-01..06: TaskTable ber-lock (ARCHITECTURE.md bagian 4)."""

from __future__ import annotations

import pytest

from pcomp.tasks import Task, TaskState, TaskTable


def make_tasks() -> list[Task]:
    return [
        Task(task_id=index, file=f"f{index}.bin", index=0, offset=0, length=10)
        for index in range(3)
    ]


def test_initial_state_all_pending() -> None:
    """UT-TBL-01: seluruh task baru berstatus PENDING."""
    table = TaskTable(make_tasks())
    assert len(table) == 3
    assert table.counts() == {"PENDING": 3, "ASSIGNED": 0, "DONE": 0, "FAILED": 0}
    assert table.all_finished() is False
    assert all(task.state is TaskState.PENDING for task in table.snapshot())


def test_take_next_is_fifo_and_sets_assigned() -> None:
    """UT-TBL-02: dispatch FIFO berdasarkan task_id, state menjadi ASSIGNED."""
    table = TaskTable(make_tasks())

    first = table.take_next("w1", now=100.0)
    second = table.take_next("w1", now=101.0)

    assert first is not None and first.task_id == 0
    assert second is not None and second.task_id == 1
    assert first.state is TaskState.ASSIGNED
    assert first.assigned_to == "w1"
    assert first.assigned_at == 100.0
    assert first.attempts == 1
    assert table.counts() == {"PENDING": 1, "ASSIGNED": 2, "DONE": 0, "FAILED": 0}


def test_take_next_empty_returns_none() -> None:
    table = TaskTable([])
    assert table.take_next("w1", now=0.0) is None
    assert table.counts() == {"PENDING": 0, "ASSIGNED": 0, "DONE": 0, "FAILED": 0}


def test_claim_result_only_for_assignee() -> None:
    """UT-TBL-03: hasil hanya diklaim oleh Worker pemilik task."""
    table = TaskTable(make_tasks())
    table.take_next("w1", now=0.0)

    assert table.claim_result(0, "w2") is None
    claimed = table.claim_result(0, "w1")
    assert claimed is not None and claimed.task_id == 0


def test_mark_done_updates_task_and_finishes() -> None:
    """UT-TBL-04: mark_done mengisi sha256/comp_size/done_at dan menutup run."""
    table = TaskTable(make_tasks())
    for worker_id in ("w1", "w2", "w1"):
        table.take_next(worker_id, now=0.0)
    table.claim_result(0, "w1")

    done = table.mark_done(0, sha256="abc", comp_size=5, now=9.5)

    assert done is not None
    assert done.state is TaskState.DONE
    assert done.sha256 == "abc"
    assert done.comp_size == 5
    assert done.done_at == 9.5
    assert table.all_finished() is False

    for task_id in (1, 2):
        owner = "w2" if task_id == 1 else "w1"
        table.claim_result(task_id, owner)
        table.mark_done(task_id, sha256="abc", comp_size=5, now=10.0)
    assert table.all_finished() is True


def test_mark_failed_and_finished() -> None:
    """UT-TBL-05: task gagal menjadi FAILED dan tetap dihitung selesai."""
    table = TaskTable(make_tasks()[:1])
    table.take_next("w1", now=0.0)
    failed = table.mark_failed(0, now=1.0)

    assert failed is not None
    assert failed.state is TaskState.FAILED
    assert table.all_finished() is True
    assert table.counts()["FAILED"] == 1


def test_duplicate_result_rejected() -> None:
    """UT-TBL-06: hasil kedua untuk task yang sama diabaikan."""
    table = TaskTable(make_tasks()[:1])
    table.take_next("w1", now=0.0)
    table.claim_result(0, "w1")
    table.mark_done(0, sha256="abc", comp_size=5, now=1.0)

    assert table.claim_result(0, "w1") is None
    assert table.mark_done(0, sha256="abc", comp_size=5, now=2.0) is None
    assert table.counts()["DONE"] == 1


def test_mark_failed_requires_assignment() -> None:
    table = TaskTable(make_tasks()[:1])
    assert table.mark_failed(0, now=0.0) is None
    assert table.counts()["PENDING"] == 1


@pytest.mark.parametrize("worker_id", ["w1", "w9"])
def test_mark_done_requires_assignment(worker_id: str) -> None:
    table = TaskTable(make_tasks()[:1])
    assert table.mark_done(0, sha256="x", comp_size=1, now=0.0) is None
    table.take_next("w1", now=0.0)
    if worker_id == "w9":
        assert table.claim_result(0, worker_id) is None
