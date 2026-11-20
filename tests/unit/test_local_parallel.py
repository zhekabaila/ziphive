"""UT-LOC-01..05: baseline paralel satu mesin (PLAN.md P3-T1..T3)."""

from __future__ import annotations

import hashlib
import json
import pickle
from pathlib import Path

import pytest

from pcomp.chunker import plan_tasks
from pcomp.compressor import compress, compress_task
from pcomp.local_parallel import LOCAL_START_METHOD, pool_context, run_local
from pcomp.manifest import to_dict, verify_entries
from pcomp.sequential import run_sequential
from pcomp.tasks import Task

MIB = 1024 * 1024


def make_input(tmp_path: Path, files: int = 3, size: int = 700_000) -> Path:
    """Buat folder input berisi beberapa file biner."""
    source = tmp_path / "input"
    source.mkdir()
    for position in range(files):
        payload = bytes([position]) * size + b"|" + bytes(range(256)) * 10
        (source / f"f{position}.bin").write_bytes(payload)
    return source


def test_manifest_matches_sequential(tmp_path: Path) -> None:
    """UT-LOC-01: manifest dan isi chunk identik dengan baseline sequential."""
    source = make_input(tmp_path)
    sequential = run_sequential(source, tmp_path / "seq", algo="gzip", level=1, chunk_mb=1)
    local = run_local(source, tmp_path / "local", algo="gzip", level=1, chunk_mb=1, procs=2)

    assert to_dict(local.manifest) == to_dict(sequential.manifest)
    assert len(local.manifest.entries) == 3
    for entry in sequential.manifest.entries:
        expected = (tmp_path / "seq" / entry.output).read_bytes()
        assert (tmp_path / "local" / entry.output).read_bytes() == expected
    assert all(item.ok for item in verify_entries(local.manifest, tmp_path / "local"))


@pytest.mark.parametrize("procs", [1, 2, 4])
def test_procs_variants(tmp_path: Path, procs: int) -> None:
    """UT-LOC-02: p = 1, 2, 4 menghasilkan manifest lengkap dan metrik terisi."""
    source = make_input(tmp_path, files=4, size=600_000)
    out_dir = tmp_path / f"out{procs}"
    result = run_local(source, out_dir, algo="lzma", level=1, chunk_mb=1, procs=procs)
    metrics = result.metrics

    assert metrics["mode"] == "local"
    assert metrics["procs"] == procs
    assert metrics["tasks"] == 4
    assert metrics["tasks_ok"] == 4
    assert metrics["tasks_failed"] == 0
    assert metrics["errors"] == []
    assert metrics["time_s"] >= 0
    assert metrics["throughput_mbs"] >= 0
    assert metrics["ratio"] > 1
    assert metrics["busy_per_process"]
    assert len(metrics["busy_per_process"]) <= procs
    assert sum(metrics["busy_per_process"].values()) > 0
    assert (out_dir / "metrics.json").is_file()
    assert (out_dir / "manifest.json").is_file()
    assert json.loads((out_dir / "metrics.json").read_text(encoding="utf-8")) == metrics
    assert len(result.manifest.entries) == 4
    assert all(item.ok for item in verify_entries(result.manifest, out_dir))


def test_pool_uses_spawn_context() -> None:
    """UT-LOC-03: pool selalu memakai start method spawn (AGENTS.md aturan 8)."""
    assert LOCAL_START_METHOD == "spawn"
    assert pool_context().get_start_method() == "spawn"

    task = Task(task_id=0, file="a.bin", index=0, offset=0, length=4)
    result = compress_task(task, b"data" * 100, "gzip", 1)
    assert pickle.loads(pickle.dumps(result)) == result


def test_compress_task_matches_compress() -> None:
    """compress_task dipakai ulang oleh Worker: hasil harus sama dengan compress."""
    task = Task(task_id=7, file="a.bin", index=1, offset=1024, length=4)
    data = b"data" * 1000

    result = compress_task(task, data, "gzip", 1)

    assert result.ok is True
    assert result.task_id == 7
    assert result.data == compress("gzip", 1, data)
    assert result.sha256 == hashlib.sha256(data).hexdigest()
    assert result.comp_size == len(result.data or b"")
    assert result.compute_sec >= 0.0
    assert result.error is None


def test_compress_task_records_error() -> None:
    """Task bermasalah menghasilkan hasil gagal, bukan exception yang naik ke pool."""
    task = Task(task_id=1, file="a.bin", index=0, offset=0, length=1)

    result = compress_task(task, b"x", "zip", 1)

    assert result.ok is False
    assert result.data is None
    assert result.comp_size == 0
    assert result.error
    assert result.compute_sec >= 0.0


def test_task_error_does_not_kill_pool(tmp_path: Path) -> None:
    """UT-LOC-04: satu task gagal dicatat, task lain tetap selesai."""
    source = make_input(tmp_path, files=2, size=200_000)
    tasks = plan_tasks(source, chunk_mb=1)
    broken = Task(task_id=len(tasks), file="tidak-ada.bin", index=0, offset=0, length=10)

    result = run_local(
        source,
        tmp_path / "out",
        algo="gzip",
        level=1,
        procs=2,
        tasks=[*tasks, broken],
    )
    metrics = result.metrics

    assert metrics["tasks"] == 3
    assert metrics["tasks_ok"] == 2
    assert metrics["tasks_failed"] == 1
    assert metrics["errors"][0]["task_id"] == broken.task_id
    assert metrics["errors"][0]["error"]
    assert len(result.manifest.entries) == 2
    assert all(item.ok for item in verify_entries(result.manifest, tmp_path / "out"))


def test_metrics_busy_per_process(tmp_path: Path) -> None:
    """UT-LOC-05: waktu sibuk dicatat per proses dan tidak melebihi total compute."""
    source = make_input(tmp_path, files=6, size=300_000)
    result = run_local(source, tmp_path / "out", algo="gzip", level=1, procs=2)
    busy = result.metrics["busy_per_process"]

    assert set(busy)  # ada minimal satu proses yang melapor
    assert all(value >= 0 for value in busy.values())
    assert sum(busy.values()) <= result.metrics["time_s"] * 2 + 1.0


def test_empty_input_dir(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    result = run_local(source, tmp_path / "out", algo="gzip", level=1, procs=2)

    assert result.manifest.entries == ()
    assert result.metrics["tasks"] == 0
    assert (tmp_path / "out" / "metrics.json").is_file()
