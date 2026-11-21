"""Sampler psutil 1 Hz dan penulis `system.csv` (PLAN.md P7-T1)."""

from __future__ import annotations

import csv
import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, TextIO

import psutil

from pcomp import constants

SYSTEM_CSV_COLUMNS = (
    "ts",
    "role",
    "node",
    "worker_id",
    "cpu_percent",
    "mem_percent",
    "rss_mb",
)

UsesSnapshot = tuple[float, float, float]


@dataclass(frozen=True)
class Sample:
    """Satu baris `system.csv`."""

    ts: float
    role: str
    node: str = ""
    worker_id: str = ""
    cpu_percent: float = 0.0
    mem_percent: float = 0.0
    rss_mb: float = 0.0

    def as_row(self) -> dict[str, Any]:
        """Baris CSV dengan urutan kolom tetap."""
        return {column: asdict(self)[column] for column in SYSTEM_CSV_COLUMNS}


class ProcessSampler:
    """Snapshot CPU dan memori proses sendiri (Worker atau Master)."""

    def __init__(self, pid: int | None = None) -> None:
        self._process = psutil.Process(pid) if pid is not None else psutil.Process()
        # Panggilan pertama psutil selalu 0.0; ambil baseline agar sampel berikutnya wajar.
        self._process.cpu_percent(interval=None)

    def usage(self) -> tuple[float, float]:
        """(cpu_percent, mem_percent) proses sendiri untuk heartbeat."""
        return (
            self._process.cpu_percent(interval=None),
            self._process.memory_percent(),
        )

    def snapshot(self) -> UsesSnapshot:
        """(cpu_percent, mem_percent, rss_mb) proses sendiri."""
        cpu, mem = self.usage()
        return (cpu, mem, self._process.memory_info().rss / constants.MIB)


class SystemSampler:
    """Ambil sampel berkala dari `sampler` dan kirim ke `sink`."""

    def __init__(
        self,
        sink: Callable[[Sample], None],
        *,
        role: str,
        node: str = "",
        worker_id: str = "",
        interval: float = constants.SYSTEM_SAMPLE_INTERVAL,
        sampler: Callable[[], UsesSnapshot] | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if interval <= 0:
            raise ValueError("interval harus lebih besar dari 0")
        self._sink = sink
        self._role = role
        self._node = node
        self._worker_id = worker_id
        self._interval = interval
        self._sampler = sampler if sampler is not None else ProcessSampler().snapshot
        self._clock = clock
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def sample_once(self) -> Sample:
        """Ambil satu sampel dan kirim ke sink."""
        cpu, mem, rss = self._sampler()
        sample = Sample(
            ts=self._clock(),
            role=self._role,
            node=self._node,
            worker_id=self._worker_id,
            cpu_percent=float(cpu),
            mem_percent=float(mem),
            rss_mb=float(rss),
        )
        self._sink(sample)
        return sample

    def start(self) -> None:
        """Mulai thread sampler sampai `stop` dipanggil."""
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="system-sampler", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Hentikan thread sampler dan tunggu selesai."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            self.sample_once()


class SystemLog:
    """Penulis `system.csv` yang aman dipakai beberapa thread."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._handle: TextIO | None = None
        self._writer: Any = None

    @property
    def path(self) -> Path:
        """Lokasi file system.csv."""
        return self._path

    def _ensure_open(self) -> TextIO:
        """Buka file dan tulis header sekali saat baris pertama datang."""
        if self._handle is None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self._path.open("w", encoding="utf-8", newline="")
            self._writer = csv.DictWriter(self._handle, fieldnames=list(SYSTEM_CSV_COLUMNS))
            self._writer.writeheader()
        return self._handle

    def write(self, sample: Sample) -> None:
        """Tulis satu sampel."""
        with self._lock:
            handle = self._ensure_open()
            self._writer.writerow(sample.as_row())
            handle.flush()

    def close(self) -> None:
        """Tutup file bila pernah dibuka."""
        with self._lock:
            if self._handle is not None and not self._handle.closed:
                self._handle.close()
            self._handle = None


def read_system_csv(path: Path) -> list[Sample]:
    """Baca kembali `system.csv` menjadi daftar `Sample`."""
    if not path.is_file():
        return []
    samples: list[Sample] = []
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            samples.append(
                Sample(
                    ts=float(row["ts"]),
                    role=row["role"],
                    node=row["node"],
                    worker_id=row["worker_id"],
                    cpu_percent=float(row["cpu_percent"]),
                    mem_percent=float(row["mem_percent"]),
                    rss_mb=float(row["rss_mb"]),
                )
            )
    return samples


@dataclass(frozen=True)
class UsageSummary:
    """Rata-rata pemakaian CPU dan memori per peran."""

    cpu_avg_master: float | None
    mem_avg_master: float | None
    cpu_avg_workers: float | None
    mem_avg_workers: float | None


def _mean(values: Sequence[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def summarise_usage(samples: Sequence[Sample]) -> UsageSummary:
    """Rata-rata CPU/memori Master (`master`/`local`) dan Worker."""
    master = [item for item in samples if item.role in ("master", "local")]
    workers = [item for item in samples if item.role == "worker"]
    return UsageSummary(
        cpu_avg_master=_mean([item.cpu_percent for item in master]),
        mem_avg_master=_mean([item.mem_percent for item in master]),
        cpu_avg_workers=_mean([item.cpu_percent for item in workers]),
        mem_avg_workers=_mean([item.mem_percent for item in workers]),
    )
