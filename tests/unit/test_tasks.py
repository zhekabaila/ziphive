"""UT-TSK-01..02: model Task dan TaskState (ARCHITECTURE.md bagian 4)."""

from __future__ import annotations

from pcomp.tasks import Task, TaskState


def test_task_defaults() -> None:
    """UT-TSK-01: task baru berstatus PENDING tanpa penugasan."""
    task = Task(task_id=0, file="a.txt", index=0, offset=0, length=1024)
    assert task.state is TaskState.PENDING
    assert task.attempts == 0
    assert task.assigned_to is None
    assert task.assigned_at is None
    assert task.sha256 is None
    assert task.comp_size is None
    assert task.done_at is None


def test_task_state_values() -> None:
    """UT-TSK-02: state machine memakai empat status pada ARCHITECTURE.md."""
    assert {state.value for state in TaskState} == {"PENDING", "ASSIGNED", "DONE", "FAILED"}


def test_task_is_mutable() -> None:
    """Task dapat diubah state-nya oleh TaskTable pada fase berikutnya."""
    task = Task(task_id=1, file="b.txt", index=0, offset=0, length=10)
    task.state = TaskState.ASSIGNED
    task.attempts += 1
    task.assigned_to = "w1"
    assert task.state is TaskState.ASSIGNED
    assert task.attempts == 1
