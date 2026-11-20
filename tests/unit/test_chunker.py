"""UT-CHK-01..05: pemecahan dataset menjadi chunk (ARCHITECTURE.md bagian 5)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp.chunker import (
    chunk_size_bytes,
    copy_index,
    plan_tasks,
    read_chunk,
    scan_files,
)
from pcomp.tasks import TaskState

MIB = 1024 * 1024


def test_chunk_size_bytes() -> None:
    assert chunk_size_bytes(4) == 4 * MIB
    with pytest.raises(ValueError):
        chunk_size_bytes(0)


def test_small_file_single_chunk(tmp_path: Path) -> None:
    """UT-CHK-01: file lebih kecil dari chunk menjadi satu task."""
    (tmp_path / "kecil.txt").write_bytes(b"abc" * 100)
    tasks = plan_tasks(tmp_path, chunk_mb=4)
    assert len(tasks) == 1
    assert tasks[0].length == 300
    assert tasks[0].offset == 0
    assert tasks[0].index == 0
    assert tasks[0].state is TaskState.PENDING


def test_exact_multiple_no_extra_chunk(tmp_path: Path) -> None:
    """UT-CHK-02: file kelipatan pas tidak menghasilkan chunk kosong."""
    (tmp_path / "pas.bin").write_bytes(b"x" * (2 * MIB))
    tasks = plan_tasks(tmp_path, chunk_mb=1)
    assert len(tasks) == 2
    assert [task.length for task in tasks] == [MIB, MIB]


def test_remainder_last_chunk_shorter(tmp_path: Path) -> None:
    """UT-CHK-03: sisa pembagian menjadi chunk terakhir yang lebih pendek."""
    (tmp_path / "sisa.bin").write_bytes(b"y" * (2 * MIB + 123))
    tasks = plan_tasks(tmp_path, chunk_mb=1)
    assert [task.length for task in tasks] == [MIB, MIB, 123]
    assert tasks[-1].offset == 2 * MIB


def test_deterministic_order_and_empty_files_skipped(tmp_path: Path) -> None:
    """UT-CHK-04: urutan deterministik berdasarkan path, file kosong dilewati."""
    (tmp_path / "b.txt").write_bytes(b"bb")
    (tmp_path / "a.txt").write_bytes(b"aa")
    (tmp_path / "kosong.txt").write_bytes(b"")
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "c.txt").write_bytes(b"cc")

    files = scan_files(tmp_path)
    assert [path.relative_to(tmp_path).as_posix() for path in files] == [
        "a.txt",
        "b.txt",
        "sub/c.txt",
    ]

    tasks = plan_tasks(tmp_path, chunk_mb=1)
    assert [task.file for task in tasks] == ["a.txt", "b.txt", "sub/c.txt"]
    assert [task.task_id for task in tasks] == [0, 1, 2]


def test_repeat_duplicates_tasks(tmp_path: Path) -> None:
    """UT-CHK-05: --repeat menggandakan daftar task dengan task_id berbeda."""
    (tmp_path / "a.txt").write_bytes(b"a" * 10)
    (tmp_path / "b.txt").write_bytes(b"b" * 10)
    tasks = plan_tasks(tmp_path, chunk_mb=1, repeat=3)
    assert len(tasks) == 6
    assert [task.task_id for task in tasks] == list(range(6))
    assert [task.file for task in tasks] == ["a.txt", "b.txt"] * 3
    assert copy_index(0, per_copy=2) == 0
    assert copy_index(3, per_copy=2) == 1


def test_read_chunk_matches_source(tmp_path: Path) -> None:
    data = bytes(range(256)) * (MIB // 256) + b"tail"
    (tmp_path / "data.bin").write_bytes(data)
    tasks = plan_tasks(tmp_path, chunk_mb=1)
    joined = b"".join(read_chunk(tmp_path, task) for task in tasks)
    assert joined == data


def test_missing_input_dir(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        plan_tasks(tmp_path / "tidak-ada", chunk_mb=1)


def test_invalid_repeat(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"a")
    with pytest.raises(ValueError):
        plan_tasks(tmp_path, chunk_mb=1, repeat=0)
