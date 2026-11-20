"""Task decomposition: pindai folder dan pecah file menjadi chunk (PLAN.md P2-T2)."""

from __future__ import annotations

from pathlib import Path

from pcomp import constants
from pcomp.tasks import Task


def chunk_size_bytes(chunk_mb: int) -> int:
    """Ukuran chunk dalam byte."""
    if chunk_mb < 1:
        raise ValueError("chunk_mb minimal 1")
    return chunk_mb * constants.MIB


def scan_files(root: Path) -> list[Path]:
    """Pindai file dataset dengan urutan deterministik; file kosong dilewati."""
    if not root.is_dir():
        raise FileNotFoundError(f"folder input tidak ditemukan: {root}")
    files = [path for path in root.rglob("*") if path.is_file() and path.stat().st_size > 0]
    files.sort(key=lambda path: path.relative_to(root).as_posix())
    return files


def plan_tasks(
    root: Path,
    chunk_mb: int = constants.DEFAULT_CHUNK_MB,
    repeat: int = constants.DEFAULT_REPEAT,
) -> list[Task]:
    """Buat daftar task dari folder dataset, diulang sebanyak `repeat` kali."""
    if repeat < 1:
        raise ValueError("repeat minimal 1")
    size = chunk_size_bytes(chunk_mb)
    tasks: list[Task] = []
    task_id = 0
    for _ in range(repeat):
        for path in scan_files(root):
            relative = path.relative_to(root).as_posix()
            total = path.stat().st_size
            index = 0
            offset = 0
            while offset < total:
                length = min(size, total - offset)
                tasks.append(
                    Task(
                        task_id=task_id,
                        file=relative,
                        index=index,
                        offset=offset,
                        length=length,
                    )
                )
                task_id += 1
                index += 1
                offset += length
    return tasks


def read_chunk(root: Path, task: Task) -> bytes:
    """Baca isi chunk sesuai offset dan panjang pada task."""
    with (root / task.file).open("rb") as handle:
        handle.seek(task.offset)
        return handle.read(task.length)


def copy_index(task_id: int, per_copy: int) -> int:
    """Nomor salinan `--repeat` dari sebuah task_id."""
    if per_copy < 1:
        raise ValueError("per_copy minimal 1")
    return task_id // per_copy
