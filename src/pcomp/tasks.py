"""Model task dan state machine (ARCHITECTURE.md bagian 4)."""

from __future__ import annotations

import threading
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
    fail_reason: str | None = None


class TaskTable:
    """Seluruh state task, dilindungi satu lock (ARCHITECTURE.md bagian 2 dan 4)."""

    def __init__(self, tasks: Iterable[Task]) -> None:
        self._lock = threading.Lock()
        self._tasks: dict[int, Task] = {task.task_id: task for task in tasks}
        self._pending: set[int] = set(self._tasks)

    def __len__(self) -> int:
        return len(self._tasks)

    def _assign(self, task: Task, worker_id: str, now: float) -> Task:
        """Tandai task ASSIGNED; pemanggil wajib memegang lock."""
        task.state = TaskState.ASSIGNED
        task.assigned_to = worker_id
        task.assigned_at = now
        task.attempts += 1
        return task

    def take_next(self, worker_id: str, now: float) -> Task | None:
        """Ambil task PENDING dengan task_id terkecil (FIFO) dan tandai ASSIGNED."""
        with self._lock:
            if not self._pending:
                return None
            task_id = min(self._pending)
            self._pending.discard(task_id)
            return self._assign(self._tasks[task_id], worker_id, now)

    def take_largest(self, worker_id: str, now: float) -> Task | None:
        """Ambil task PENDING terbesar (LPT); seri diputus task_id terkecil."""
        with self._lock:
            if not self._pending:
                return None
            task_id = max(self._pending, key=lambda item: (self._tasks[item].length, -item))
            self._pending.discard(task_id)
            return self._assign(self._tasks[task_id], worker_id, now)

    def take_task(self, task_id: int, worker_id: str, now: float) -> Task | None:
        """Ambil task tertentu bila masih PENDING (dipakai static scheduler)."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.PENDING:
                return None
            self._pending.discard(task_id)
            return self._assign(task, worker_id, now)

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

    def mark_failed(self, task_id: int, now: float, reason: str | None = None) -> Task | None:
        """Tandai task gagal (dead-letter); None bila tidak ASSIGNED."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.ASSIGNED:
                return None
            task.state = TaskState.FAILED
            task.done_at = now
            task.fail_reason = reason
            return task

    def _requeue_locked(self, task: Task, now: float, max_attempts: int, reason: str) -> bool:
        """Kembalikan task ke PENDING atau FAILED; pemanggil wajib memegang lock."""
        if task.attempts >= max_attempts:
            task.state = TaskState.FAILED
            task.done_at = now
            task.fail_reason = reason
            return False
        task.state = TaskState.PENDING
        task.assigned_to = None
        task.assigned_at = None
        self._pending.add(task.task_id)
        return True

    def requeue_task(
        self, task_id: int, *, now: float, max_attempts: int, reason: str = ""
    ) -> Task | None:
        """Kembalikan task ASSIGNED ke PENDING; FAILED bila attempts sudah habis."""
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task.state is not TaskState.ASSIGNED:
                return None
            self._requeue_locked(task, now, max_attempts, reason)
            return task

    def requeue_from(
        self, worker_id: str, *, now: float, max_attempts: int, reason: str = ""
    ) -> list[tuple[Task, bool]]:
        """Requeue seluruh task milik Worker; kembalikan (task, kembali_ke_PENDING)."""
        with self._lock:
            outcomes: list[tuple[Task, bool]] = []
            for task in self._tasks.values():
                if task.state is not TaskState.ASSIGNED or task.assigned_to != worker_id:
                    continue
                requeued = self._requeue_locked(task, now, max_attempts, reason)
                outcomes.append((task, requeued))
            outcomes.sort(key=lambda item: item[0].task_id)
            return outcomes

    def fail_unfinished(self, reason: str, now: float) -> list[Task]:
        """Tandai seluruh task PENDING/ASSIGNED sebagai FAILED (abort run)."""
        with self._lock:
            failed: list[Task] = []
            for task in self._tasks.values():
                if task.state not in (TaskState.PENDING, TaskState.ASSIGNED):
                    continue
                task.state = TaskState.FAILED
                task.done_at = now
                task.fail_reason = reason
                failed.append(task)
            self._pending.clear()
            return sorted(failed, key=lambda item: item.task_id)

    def failed_tasks(self) -> list[Task]:
        """Daftar task FAILED, urut task_id (dead-letter pada manifest)."""
        with self._lock:
            return [
                self._tasks[task_id]
                for task_id in sorted(self._tasks)
                if self._tasks[task_id].state is TaskState.FAILED
            ]

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
