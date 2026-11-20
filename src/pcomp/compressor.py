"""Registri algoritma kompresi (PLAN.md P2-T3)."""

from __future__ import annotations

import bz2
import gzip
import hashlib
import lzma
import time
from dataclasses import dataclass

from pcomp import constants
from pcomp.tasks import Task

ALGORITHMS = ("gzip", "bz2", "lzma", "sim")

_EXTENSIONS = {
    "gzip": "gz",
    "bz2": "bz2",
    "lzma": "xz",
    "sim": "sim",
}


def _validate(algo: str, level: int) -> None:
    if algo not in ALGORITHMS:
        raise ValueError(f"algoritma tidak dikenal: {algo} (pilihan: {', '.join(ALGORITHMS)})")
    if not 0 <= level <= 9:
        raise ValueError(f"level {level} di luar rentang 0-9")
    if algo == "bz2" and level < 1:
        raise ValueError("level bz2 minimal 1")


def compress(algo: str, level: int, data: bytes) -> bytes:
    """Kompres data dengan algoritma terdaftar."""
    _validate(algo, level)
    if algo == "gzip":
        return gzip.compress(data, compresslevel=level)
    if algo == "bz2":
        return bz2.compress(data, compresslevel=level)
    if algo == "lzma":
        return lzma.compress(data, preset=level)
    time.sleep(sim_delay_seconds(len(data)))
    return data


def decompress(algo: str, level: int, data: bytes) -> bytes:
    """Dekompresi data hasil `compress` dengan algoritma yang sama."""
    _validate(algo, level)
    if algo == "gzip":
        return gzip.decompress(data)
    if algo == "bz2":
        return bz2.decompress(data)
    if algo == "lzma":
        return lzma.decompress(data)
    return data


@dataclass(frozen=True)
class TaskResult:
    """Hasil kompresi satu task; dipakai ulang oleh Worker pada Fase 4."""

    task_id: int
    ok: bool
    sha256: str
    comp_size: int
    data: bytes | None
    error: str | None
    compute_sec: float


def compress_task(task: Task, data: bytes, algo: str, level: int) -> TaskResult:
    """Kompres satu task dan tangkap semua error agar pool Worker tetap hidup.

    Fungsi ini sengaja diletakkan di modul netral (bukan di `worker/`) supaya
    Worker Fase 4 dan baseline local parallel memakai logika yang sama.
    """
    started = time.perf_counter()
    digest = hashlib.sha256(data).hexdigest()
    try:
        packed = compress(algo, level, data)
    except Exception as exc:  # noqa: BLE001 - error task dicatat, bukan mematikan pool
        return TaskResult(
            task_id=task.task_id,
            ok=False,
            sha256=digest,
            comp_size=0,
            data=None,
            error=f"{type(exc).__name__}: {exc}",
            compute_sec=time.perf_counter() - started,
        )
    return TaskResult(
        task_id=task.task_id,
        ok=True,
        sha256=digest,
        comp_size=len(packed),
        data=packed,
        error=None,
        compute_sec=time.perf_counter() - started,
    )


def sim_delay_seconds(size_bytes: int) -> float:
    """Perkiraan waktu algoritma `sim`: sebanding ukuran data (khusus test)."""
    return (size_bytes / constants.MIB) * constants.SIM_SECONDS_PER_MB


def file_extension(algo: str) -> str:
    """Ekstensi file chunk hasil kompresi."""
    if algo not in _EXTENSIONS:
        raise ValueError(f"algoritma tidak dikenal: {algo}")
    return _EXTENSIONS[algo]


def is_simulated(algo: str) -> bool:
    """True bila algoritma `sim` dipakai (hasil tidak boleh masuk laporan)."""
    return algo == "sim"
