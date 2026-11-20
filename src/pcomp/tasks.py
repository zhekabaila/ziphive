"""Model task dan state machine (ARCHITECTURE.md bagian 4)."""

from __future__ import annotations

import threading
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum


class TaskState(StrEnum):
    """Status satu task pada Master."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Task:
    """Satu chunk file yang harus dikompresi."""

    task_id: int
    file: str
    index: int
    offset: int
    length: int
    state: TaskState = TaskState.PENDING
    attempts: int = 0
    assigned_to: str | None = None
    assigned_at: float | None = None
    sha256: str | None = None
    comp_size: int | None = None
    done_at: float | None = None


class TaskTable:
    """Seluruh state task, dilindungi satu lock (ARCHITECTURE.md bagian 2 dan 4)."""

    def __init__(self, tasks: Iterable[Task]) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[int, Task] = {task.task_id: task for task in tasks}
        self._pending: deque[int] = deque(sorted(self._tasks))

    def __len__(self) -> int:
        return len(self._tasks)

    def take_next(self, worker_id: str, now: float) -> Task | None:
        """Ambil task PENDING berikutnya (FIFO) dan tandai ASSIGNED untuk `worker_id`."""
        with self._lock:
            if not self._pending:
                return None
            task = self._tasks[self._pending.popleft()]
            task.state = TaskState.ASSIGNED
            task.assigned_to = worker_id
            task.assigned_at = now
            task.attempts += 1
            return task

    def claim_result(self, task_id: int, worker_id: str) -> Task | None:
        """Kembalikan task hanya bila ASSIGNED ke Worker pengirim (idempotensi)."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.ASSIGNED:
                return None
            if task.assigned_to != worker_id:
                return None
            return task

    def mark_done(self, task_id: int, *, sha256: str, comp_size: int, now: float) -> Task | None:
        """Tandai task selesai; None bila task tidak sedang ASSIGNED."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.ASSIGNED:
                return None
            task.state = TaskState.DONE
            task.sha256 = sha256
            task.comp_size = comp_size
            task.done_at = now
            return task

    def mark_failed(self, task_id: int, now: float) -> Task | None:
        """Tandai task gagal (dead-letter pada fase ini); None bila tidak ASSIGNED."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.ASSIGNED:
                return None
            task.state = TaskState.FAILED
            task.done_at = now
            return task

    def counts(self) -> dict[str, int]:
        """Jumlah task per state."""
        with self._lock:
            totals = {state.value: 0 for state in TaskState}
            for task in self._tasks.values():
                totals[task.state.value] += 1
            return totals

    def all_finished(self) -> bool:
        """True bila tidak ada task PENDING atau ASSIGNED."""
        with self._lock:
            return all(
                task.state in (TaskState.DONE, TaskState.FAILED) for task in self._tasks.values()
            )

    def snapshot(self) -> list[Task]:
        """Salinan daftar task (objek asli, urut task_id)."""
        with self._lock:
            return [self._tasks[task_id] for task_id in sorted(self._tasks)]
