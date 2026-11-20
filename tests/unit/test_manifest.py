"""UT-MAN-01..03: manifest, rekonstruksi, dan verifikasi."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from pcomp.chunker import plan_tasks, read_chunk
from pcomp.compressor import compress
from pcomp.manifest import (
    ManifestEntry,
    ManifestError,
    build_manifest,
    chunk_output_name,
    read_manifest,
    reconstruct_file,
    verify_entries,
    write_manifest,
)

MIB = 1024 * 1024


def prepare_run(
    tmp_path: Path, data: bytes, algo: str = "gzip", level: int = 1, chunk_mb: int = 1
) -> tuple[object, Path, Path]:
    source = tmp_path / "input"
    source.mkdir()
    (source / "data.bin").write_bytes(data)
    out_dir = tmp_path / "out"
    out_dir.mkdir()

    entries: list[ManifestEntry] = []
    for task in plan_tasks(source, chunk_mb=chunk_mb):
        raw = read_chunk(source, task)
        packed = compress(algo, level, raw)
        relative = chunk_output_name(task.file, task.index, algo, copy=0, repeat=1)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(packed)
        entries.append(
            ManifestEntry(
                task_id=task.task_id,
                file=task.file,
                index=task.index,
                offset=task.offset,
                length=len(raw),
                sha256=hashlib.sha256(raw).hexdigest(),
                output=relative,
                comp_size=len(packed),
                copy=0,
            )
        )
    manifest = build_manifest(algo=algo, level=level, chunk_mb=chunk_mb, repeat=1, entries=entries)
    return manifest, out_dir, source


def test_write_and_read_manifest(tmp_path: Path) -> None:
    """UT-MAN-01: skema manifest bolak-balik tanpa kehilangan data."""
    manifest, _, _ = prepare_run(tmp_path, b"z" * (2 * MIB + 7))
    path = tmp_path / "manifest.json"
    write_manifest(path, manifest)
    loaded = read_manifest(path)

    assert loaded == manifest
    assert loaded.version == 1
    assert loaded.algo == "gzip"
    assert loaded.chunk_mb == 1
    assert len(loaded.entries) == 3
    assert loaded.total_orig_bytes == 2 * MIB + 7
    assert loaded.total_comp_bytes == sum(entry.comp_size for entry in loaded.entries)
    assert loaded.ratio > 1.0


def test_manifest_json_schema(tmp_path: Path) -> None:
    manifest, _, _ = prepare_run(tmp_path, b"abc" * 100)
    path = tmp_path / "manifest.json"
    write_manifest(path, manifest)
    import json

    payload = json.loads(path.read_text(encoding="utf-8"))
    assert set(payload) >= {
        "version",
        "algo",
        "level",
        "chunk_mb",
        "repeat",
        "total_orig_bytes",
        "total_comp_bytes",
        "entries",
    }
    assert set(payload["entries"][0]) == {
        "task_id",
        "file",
        "index",
        "offset",
        "length",
        "sha256",
        "output",
        "comp_size",
        "copy",
    }


def test_reconstruct_identical(tmp_path: Path) -> None:
    """UT-MAN-02: rekonstruksi menghasilkan file identik (sha256 sama)."""
    data = bytes(range(256)) * (MIB // 128) + b"ekor"
    manifest, out_dir, _ = prepare_run(tmp_path, data)
    rebuilt = reconstruct_file(manifest, out_dir, "data.bin")
    assert rebuilt == data
    assert hashlib.sha256(rebuilt).hexdigest() == hashlib.sha256(data).hexdigest()


def test_verify_detects_corruption(tmp_path: Path) -> None:
    """UT-MAN-03: chunk yang dirusak terdeteksi saat verifikasi."""
    manifest, out_dir, _ = prepare_run(tmp_path, b"aman" * 1000)
    assert all(result.ok for result in verify_entries(manifest, out_dir))

    target = out_dir / manifest.entries[0].output
    target.write_bytes(target.read_bytes() + b"rusak")

    results = verify_entries(manifest, out_dir)
    assert results[0].ok is False
    assert results[0].reason


def test_verify_detects_missing_chunk(tmp_path: Path) -> None:
    manifest, out_dir, _ = prepare_run(tmp_path, b"hilang" * 100)
    (out_dir / manifest.entries[0].output).unlink()
    results = verify_entries(manifest, out_dir)
    assert results[0].ok is False


def test_read_manifest_invalid(tmp_path: Path) -> None:
    path = tmp_path / "rusak.json"
    path.write_text("{bukan json", encoding="utf-8")
    with pytest.raises(ManifestError):
        read_manifest(path)


def test_read_manifest_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_manifest(tmp_path / "tidak-ada.json")


def test_chunk_output_name() -> None:
    assert chunk_output_name("a.txt", 0, "lzma", copy=0, repeat=1) == "chunks/a.txt.0000.xz"
    assert chunk_output_name("a.txt", 1, "gzip", copy=2, repeat=3) == "chunks/r2/a.txt.0001.gz"
