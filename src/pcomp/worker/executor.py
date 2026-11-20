"""Executor Worker: Pool proses dan `compress_task` (PLAN.md P4-T3)."""

from __future__ import annotations

import multiprocessing as mp
from collections.abc import Callable
from multiprocessing.pool import Pool

from pcomp.compressor import TaskResult, compress_task
from pcomp.local_parallel import pool_context
from pcomp.tasks import Task


class Executor:
    """Jalankan kompresi task di `multiprocessing.Pool` milik Worker."""

    def __init__(
        self,
        procs: int,
        on_result: Callable[[TaskResult], None],
        *,
        context: mp.context.BaseContext | None = None,
    ) -> None:
        if procs < 1:
            raise ValueError("procs minimal 1")
        self.procs = procs
        self._on_result = on_result
        self._pool: Pool = (context or pool_context()).Pool(processes=procs)

    def submit(self, task: Task, data: bytes, algo: str, level: int) -> None:
        """Kirim satu task ke proses pool; hasil dikirim ke `on_result`."""
        self._pool.apply_async(compress_task, (task, data, algo, level), callback=self._on_result)

    def close(self) -> None:
        """Tutup pool dan tunggu seluruh task yang sudah dikirim selesai."""
        self._pool.close()
        self._pool.join()
