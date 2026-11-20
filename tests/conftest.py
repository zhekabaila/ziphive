"""Fixture bersama untuk seluruh test ZipHive."""

from __future__ import annotations

from pathlib import Path

import pytest

VALID_GROUP_TOML = """\
project_name = "ZipHive"
tema = "16 - Distributed Data Compression"
mata_kuliah = "Komputasi Paralel dan Sistem Terdistribusi"
institusi = "Informatika, Universitas Siliwangi"

[kelompok]
nama = "Kelompok Uji"

[[anggota]]
nama = "Ani Uji"
npm = "123456"
"""

PLACEHOLDER_GROUP_TOML = """\
project_name = "ZipHive"
tema = "16 - Distributed Data Compression"
mata_kuliah = "Komputasi Paralel dan Sistem Terdistribusi"
institusi = "Informatika, Universitas Siliwangi"

[kelompok]
nama = "<ISI NAMA KELOMPOK>"

[[anggota]]
nama = "<ISI NAMA ANGGOTA 1>"
npm = "<ISI NPM 1>"
"""


@pytest.fixture
def repo_root() -> Path:
    """Folder akar repo (berisi pyproject.toml)."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def valid_group_file(tmp_path: Path) -> Path:
    """File group.toml yang sudah terisi lengkap."""
    path = tmp_path / "group-valid.toml"
    path.write_text(VALID_GROUP_TOML, encoding="utf-8")
    return path


@pytest.fixture
def placeholder_group_file(tmp_path: Path) -> Path:
    """File group.toml yang masih berisi placeholder."""
    path = tmp_path / "group-placeholder.toml"
    path.write_text(PLACEHOLDER_GROUP_TOML, encoding="utf-8")
    return path
