"""UT-SEQ-01: baseline sequential menghasilkan manifest dan metrics."""

from __future__ import annotations

import json
from pathlib import Path

from pcomp.manifest import read_manifest, verify_entries
from pcomp.sequential import run_sequential


def test_run_sequential_outputs(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "a.txt").write_bytes(b"halo dunia " * 500)
    (source / "b.bin").write_bytes(bytes(range(256)) * 100)
    out_dir = tmp_path / "out"

    result = run_sequential(source, out_dir, algo="gzip", level=1, chunk_mb=1, repeat=1)

    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "metrics.json").is_file()
    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["mode"] == "sequential"
    assert metrics["algo"] == "gzip"
    assert metrics["level"] == 1
    assert metrics["tasks"] == 2
    assert metrics["total_orig_bytes"] == result.manifest.total_orig_bytes
    assert metrics["total_comp_bytes"] == result.manifest.total_comp_bytes
    assert metrics["time_s"] >= 0
    assert metrics["throughput_mbs"] >= 0
    assert metrics["ratio"] > 0
    assert metrics["simulated"] is False
    assert "started_at" in metrics

    manifest = read_manifest(out_dir / "manifest.json")
    assert all(item.ok for item in verify_entries(manifest, out_dir))


def test_run_sequential_marks_simulated(tmp_path: Path) -> None:
    """Algoritma sim wajib ditandai di metadata keluaran."""
    source = tmp_path / "input"
    source.mkdir()
    (source / "a.txt").write_bytes(b"x" * 100)
    out_dir = tmp_path / "out"

    run_sequential(source, out_dir, algo="sim", level=1, chunk_mb=1)
    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["algo"] == "sim"
    assert metrics["simulated"] is True


def test_run_sequential_repeat(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    (source / "a.txt").write_bytes(b"y" * 100)
    out_dir = tmp_path / "out"

    result = run_sequential(source, out_dir, algo="gzip", level=1, chunk_mb=1, repeat=3)
    assert len(result.manifest.entries) == 3
    assert result.manifest.total_orig_bytes == 300
    assert all(item.ok for item in verify_entries(result.manifest, out_dir))


def test_run_sequential_empty_input(tmp_path: Path) -> None:
    source = tmp_path / "input"
    source.mkdir()
    out_dir = tmp_path / "out"
    result = run_sequential(source, out_dir, algo="gzip", level=1)
    assert result.manifest.entries == ()
    assert (out_dir / "metrics.json").is_file()
