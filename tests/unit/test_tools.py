"""UT-TOOL-01..02: dataset sintetis dan perencanaan unduhan korpus."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcomp.tools.download_corpus import DownloadError, build_plan, sha256_file
from pcomp.tools.make_dataset import build_dataset

MIB = 1024 * 1024


def test_make_dataset_deterministic(tmp_path: Path) -> None:
    """UT-TOOL-01: seed sama menghasilkan isi dan sha256 sama."""
    first = build_dataset(tmp_path / "satu", size_mb=1, seed=123)
    second = build_dataset(tmp_path / "dua", size_mb=1, seed=123)
    assert [item["sha256"] for item in first["files"]] == [
        item["sha256"] for item in second["files"]
    ]


def test_make_dataset_size_and_metadata(tmp_path: Path) -> None:
    metadata = build_dataset(tmp_path / "data", size_mb=2, seed=7, files=4)
    total = sum(item["size"] for item in metadata["files"])
    assert total == 2 * MIB
    assert len(metadata["files"]) == 4
    assert metadata["seed"] == 7

    on_disk = tmp_path / "data" / "dataset.json"
    assert on_disk.is_file()
    saved = json.loads(on_disk.read_text(encoding="utf-8"))
    assert saved["seed"] == 7
    assert saved["files"] == metadata["files"]


def test_make_dataset_rejects_bad_size(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        build_dataset(tmp_path / "data", size_mb=0)


def test_build_plan_derives_filename(tmp_path: Path) -> None:
    """UT-TOOL-02: rencana unduhan diturunkan dari URL tanpa akses jaringan."""
    plan = build_plan("https://contoh.invalid/corpus/silesia.zip", tmp_path)
    assert plan.filename == "silesia.zip"
    assert plan.target == tmp_path / "silesia.zip"


def test_build_plan_rejects_non_http(tmp_path: Path) -> None:
    with pytest.raises(DownloadError):
        build_plan("ftp://contoh.invalid/silesia.zip", tmp_path)


def test_sha256_file(tmp_path: Path) -> None:
    path = tmp_path / "satu.bin"
    path.write_bytes(b"abc")
    assert sha256_file(path) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
