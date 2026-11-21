"""Executor Worker: Pool proses dan `compress_task` (PLAN.md P4-T3, P5-T4)."""

from __future__ import annotations

import hashlib
import multiprocessing as mp
import random
import time
from collections.abc import Callable
from dataclasses import replace
from multiprocessing.pool import Pool

from pcomp.compressor import TaskResult, compress_task
from pcomp.local_parallel import pool_context
from pcomp.tasks import Task


def run_task(
    task: Task,
    data: bytes,
    algo: str,
    level: int,
    throttle: float,
    task_fail_rate: float = 0.0,
    seed: int = 0,
) -> TaskResult:
    """Kompres satu task di proses pool; `throttle` meniru Worker lambat.

    `task_fail_rate` dengan `seed` tetap mensimulasikan kegagalan task secara deterministik
    untuk menguji retry dan dead-letter (PLAN.md P6-T5).
    """
    started = time.perf_counter()
    if throttle > 0:
        time.sleep(throttle)
    if task_fail_rate > 0:
        rng = random.Random(seed * 1_000_003 + task.task_id)
        if rng.random() < task_fail_rate:
            return TaskResult(
                task_id=task.task_id,
                ok=False,
                sha256=hashlib.sha256(data).hexdigest(),
                comp_size=0,
                data=None,
                error="task_fail_rate",
                compute_sec=time.perf_counter() - started,
            )
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
        task_fail_rate: float = 0.0,
        seed: int = 0,
        context: mp.context.BaseContext | None = None,
    ) -> None:
        if procs < 1:
            raise ValueError("procs minimal 1")
        if throttle < 0:
            raise ValueError("throttle tidak boleh negatif")
        if not 0.0 <= task_fail_rate <= 1.0:
            raise ValueError("task_fail_rate harus di antara 0 dan 1")
        self.procs = procs
        self.throttle = throttle
        self.task_fail_rate = task_fail_rate
        self.seed = seed
        self._on_result = on_result
        self._pool: Pool = (context or pool_context()).Pool(processes=procs)

    def submit(self, task: Task, data: bytes, algo: str, level: int) -> None:
        """Kirim satu task ke proses pool; hasil dikirim ke `on_result`."""
        self._pool.apply_async(
            run_task,
            (task, data, algo, level, self.throttle, self.task_fail_rate, self.seed),
            callback=self._on_result,
        )

    def close(self) -> None:
        """Tutup pool dan tunggu seluruh task yang sudah dikirim selesai."""
        self._pool.close()
        self._pool.join()
