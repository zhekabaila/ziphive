"""Registri algoritma kompresi (PLAN.md P2-T3)."""

from __future__ import annotations

import bz2
import gzip
import lzma
import time

from pcomp import constants

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
