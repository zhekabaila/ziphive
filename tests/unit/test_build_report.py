"""UT-DOC-01..05: pembangun laporan DOCX dan smoke paket (PLAN.md P10-T2, P10-T6)."""

from __future__ import annotations

import zipfile
from pathlib import Path
from types import ModuleType

import pytest

GROUP_TOML = """\
project_name = "ZipHive"
tema = "16 - Distributed Data Compression"

[[anggota]]
nama = "Anggota Uji"
npm = "000000"
"""


@pytest.fixture
def build_module(load_script) -> ModuleType:
    return load_script("build_report.py")


@pytest.fixture
def smoke_module(load_script) -> ModuleType:
    return load_script("smoke_package.py")


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    """Repo tiruan berisi identitas kelompok dan tanpa berkas gambar."""
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "group.toml").write_text(GROUP_TOML, encoding="utf-8")
    return tmp_path


def test_runs_replace_markup(build_module: ModuleType) -> None:
    """Penanda **tebal** dan `mono` berubah menjadi run, tanpa sisa penanda."""
    xml = build_module._runs("nilai `lzma` preset **6**")
    assert 'w:ascii="Courier New"' in xml
    assert "<w:b/>" in xml
    assert "`" not in xml
    assert "**" not in xml
    assert "lzma" in xml and "preset" in xml


def test_chapter_uses_single_heading_paragraph(build_module: ModuleType) -> None:
    """Judul bab menjadi satu paragraf Heading 1 dengan pemisah baris."""
    xml = build_module.chapter("BAB I", "PENDAHULUAN")
    assert xml.count("<w:p>") == 1
    assert 'w:pStyle w:val="Heading1"' in xml
    assert "<w:br/>" in xml


def test_png_size_reads_header(build_module: ModuleType, repo_root: Path) -> None:
    """Ukuran gambar dibaca dari header PNG milik repo."""
    path = repo_root / "results" / "figures" / "speedup.png"
    width, height = build_module.png_size(path)
    assert width > 0 and height > 0


def test_build_uses_placeholder_when_image_missing(
    build_module: ModuleType, fake_repo: Path, tmp_path: Path
) -> None:
    """Gambar yang tidak tersedia diganti kotak placeholder, bukan dikarang."""
    out = tmp_path / "laporan.docx"
    images, missing = build_module.build(fake_repo, out)
    assert images == 0
    assert missing, "harus ada gambar yang dilaporkan hilang"
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
        assert "word/document.xml" in names
        document = archive.read("word/document.xml").decode("utf-8")
        assert "PLACEHOLDER GAMBAR" in document
        assert "Cara memperoleh" in document
        rels = archive.read("word/_rels/document.xml.rels").decode("utf-8")
        assert "rIdFooter" in rels


def test_check_entries_flags_forbidden_and_missing(smoke_module: ModuleType) -> None:
    """Pemeriksa isi ZIP menolak entri terlarang dan menandai entri wajib hilang."""
    problems = smoke_module.check_entries(["data/bench/text_00.txt", "README.md"])
    assert any("entri terlarang" in problem for problem in problems)
    assert any("entri wajib tidak ditemukan" in problem for problem in problems)

    clean = [*smoke_module.REQUIRED_ENTRIES, "src/pcomp/tasks.py"]
    assert smoke_module.check_entries(clean) == []
