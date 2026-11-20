"""UT-COL-01..03: collector menulis chunk, manifest, dan metrics (PLAN.md P4-T2)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pcomp.compressor import compress
from pcomp.manifest import read_manifest, verify_entries
from pcomp.master.collector import Collector
from pcomp.tasks import Task


def make_task(task_id: int, file: str = "a.bin") -> Task:
    return Task(task_id=task_id, file=file, index=task_id, offset=task_id * 10, length=10)


def test_write_chunk_creates_file_and_entry(tmp_path: Path) -> None:
    """UT-COL-01: chunk ditulis ke chunks/<file>.<index>.<ext> dan dicatat."""
    collector = Collector(tmp_path, algo="gzip", level=1, chunk_mb=1, repeat=1, total_tasks=2)
    task = make_task(0)
    data = b"0123456789"
    packed = compress("gzip", 1, data)

    entry = collector.write_chunk(
        task, packed, sha256=hashlib.sha256(data).hexdigest(), comp_size=len(packed)
    )

    assert entry.output == "chunks/a.bin.0000.gz"
    assert (tmp_path / entry.output).read_bytes() == packed
    assert entry.length == 10
    assert entry.task_id == 0
    assert entry.copy == 0


def test_manifest_total_and_verify(tmp_path: Path) -> None:
    """UT-COL-02: manifest hasil collector dapat diverifikasi."""
    collector = Collector(tmp_path, algo="gzip", level=1, chunk_mb=1, repeat=1, total_tasks=2)
    for task_id in range(2):
        data = bytes([task_id]) * 10
        packed = compress("gzip", 1, data)
        collector.write_chunk(
            make_task(task_id),
            packed,
            sha256=hashlib.sha256(data).hexdigest(),
            comp_size=len(packed),
        )

    manifest = collector.write_manifest()

    assert manifest.total_orig_bytes == 20
    assert manifest.total_comp_bytes == sum(entry.comp_size for entry in manifest.entries)
    assert read_manifest(tmp_path / "manifest.json") == manifest
    assert all(result.ok for result in verify_entries(manifest, tmp_path))


def test_write_metrics(tmp_path: Path) -> None:
    """UT-COL-03: metrics.json ditulis apa adanya."""
    collector = Collector(tmp_path, algo="gzip", level=1, chunk_mb=1, repeat=1, total_tasks=0)
    collector.write_metrics({"mode": "distributed", "tasks": 0})

    saved = json.loads((tmp_path / "metrics.json").read_text(encoding="utf-8"))
    assert saved == {"mode": "distributed", "tasks": 0}


def test_repeat_uses_copy_folder(tmp_path: Path) -> None:
    collector = Collector(tmp_path, algo="lzma", level=1, chunk_mb=1, repeat=2, total_tasks=4)
    data = b"x" * 10
    packed = compress("lzma", 1, data)

    first = collector.write_chunk(make_task(0), packed, sha256="h", comp_size=len(packed))
    second = collector.write_chunk(make_task(2), packed, sha256="h", comp_size=len(packed))

    assert first.output == "chunks/r0/a.bin.0000.xz"
    assert second.output == "chunks/r1/a.bin.0002.xz"
    assert first.copy == 0 and second.copy == 1
