"""Executor Worker: Pool proses dan `compress_task` (PLAN.md P4-T3, P5-T4)."""

from __future__ import annotations

import multiprocessing as mp
import time
from collections.abc import Callable
from dataclasses import replace
from multiprocessing.pool import Pool

from pcomp.compressor import TaskResult, compress_task
from pcomp.local_parallel import pool_context
from pcomp.tasks import Task


def run_task(task: Task, data: bytes, algo: str, level: int, throttle: float) -> TaskResult:
    """Kompres satu task di proses pool; `throttle` meniru Worker lambat dan ikut dihitung sibuk."""
    started = time.perf_counter()
    if throttle > 0:
        time.sleep(throttle)
    result = compress_task(task, data, algo, level)
    return replace(result, compute_sec=time.perf_counter() - started)


class Executor:
    """Jalankan kompresi task di `multiprocessing.Pool` milik Worker."""

    def __init__(
        self,
        procs: int,
        on_result: Callable[[TaskResult], None],
        *,
        throttle: float = 0.0,
        context: mp.context.BaseContext | None = None,
    ) -> None:
        if procs < 1:
            raise ValueError("procs minimal 1")
        if throttle < 0:
            raise ValueError("throttle tidak boleh negatif")
        self.procs = procs
        self.throttle = throttle
        self._on_result = on_result
        self._pool: Pool = (context or pool_context()).Pool(processes=procs)

    def submit(self, task: Task, data: bytes, algo: str, level: int) -> None:
        """Kirim satu task ke proses pool; hasil dikirim ke `on_result`."""
        self._pool.apply_async(
            run_task,
            (task, data, algo, level, self.throttle),
            callback=self._on_result,
        )

    def close(self) -> None:
        """Tutup pool dan tunggu seluruh task yang sudah dikirim selesai."""
        self._pool.close()
        self._pool.join()
