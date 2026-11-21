"""Pemilihan task untuk Worker (PLAN.md P5-T1..T3, ARCHITECTURE.md bagian 6)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from collections.abc import Sequence

from pcomp.tasks import Task, TaskTable


class Scheduler(ABC):
    """Antarmuka penentu task berikutnya untuk satu Worker."""

    name: str

    @abstractmethod
    def start(self, table: TaskTable, worker_ids: Sequence[str]) -> None:
        """Siapkan rencana awal setelah barrier terpenuhi."""

    @abstractmethod
    def take(self, table: TaskTable, worker_id: str, now: float) -> Task | None:
        """Ambil satu task untuk Worker, atau None bila tidak ada jatah."""

    def on_worker_dead(self, worker_id: str) -> None:
        """Beri kesempatan scheduler memindahkan jatah Worker yang mati."""
        return None

    def on_requeue(self, task: Task) -> None:
        """Beri kesempatan scheduler mengantrekan ulang task yang dikembalikan."""
        return None


class DynamicScheduler(Scheduler):
    """Dispatch saat Worker meminta credit, task terbesar lebih dulu (LPT)."""

    name = "dynamic"

    def start(self, table: TaskTable, worker_ids: Sequence[str]) -> None:
        """Tidak perlu rencana awal; kapasitas tercermin dari credit."""

    def take(self, table: TaskTable, worker_id: str, now: float) -> Task | None:
        return table.take_largest(worker_id, now)


class StaticScheduler(Scheduler):
    """Partisi round-robin sekali di awal, tanpa penyeimbangan sesudahnya."""

    name = "static"

    def __init__(self) -> None:
        self._queues: dict[str, deque[int]] = {}
        self._orphans: deque[int] = deque()

    def start(self, table: TaskTable, worker_ids: Sequence[str]) -> None:
        """Bagi task round-robin menurut urutan task_id ke Worker yang hadir saat barrier."""
        workers = list(worker_ids)
        self._queues = {worker_id: deque() for worker_id in workers}
        self._orphans = deque()
        if not workers:
            return
        for position, task in enumerate(table.snapshot()):
            self._queues[workers[position % len(workers)]].append(task.task_id)

    def _next_id(self, worker_id: str) -> int | None:
        """Ambil id berikutnya dari jatah sendiri, lalu dari antrean bersama."""
        queue = self._queues.get(worker_id)
        if queue:
            return queue.popleft()
        if self._orphans:
            return self._orphans.popleft()
        return None

    def take(self, table: TaskTable, worker_id: str, now: float) -> Task | None:
        while True:
            task_id = self._next_id(worker_id)
            if task_id is None:
                return None
            task = table.take_task(task_id, worker_id, now)
            if task is not None:
                return task

    def on_worker_dead(self, worker_id: str) -> None:
        """Pindahkan jatah Worker mati ke antrean bersama."""
        queue = self._queues.pop(worker_id, None)
        if queue:
            self._orphans.extend(queue)

    def on_requeue(self, task: Task) -> None:
        """Task yang kembali PENDING dapat diambil Worker hidup mana pun."""
        self._orphans.append(task.task_id)


def build_scheduler(name: str) -> Scheduler:
    """Petakan nama scheduler dari konfigurasi ke kelasnya."""
    if name == "static":
        return StaticScheduler()
    if name == "dynamic":
        return DynamicScheduler()
    raise ValueError(f"scheduler '{name}' tidak dikenal")


def imbalance_factor(busy: Sequence[float]) -> float:
    """max(busy) / mean(busy); 1.0 berarti seimbang atau data kosong (EXPERIMENTS.md bagian 3)."""
    values = [max(0.0, value) for value in busy]
    if not values:
        return 1.0
    mean = sum(values) / len(values)
    if mean <= 0.0:
        return 1.0
    return max(values) / mean
