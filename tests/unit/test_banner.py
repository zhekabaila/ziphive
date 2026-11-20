"""UT-BOOT-02 dan UT-BOOT-03: banner dari group.toml valid dan placeholder."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp.banner import GroupInfo, is_placeholder, load_group_info, render_banner


def test_load_valid_group(valid_group_file: Path) -> None:
    info = load_group_info(valid_group_file)
    assert isinstance(info, GroupInfo)
    assert info.project_name == "ZipHive"
    assert info.nama_kelompok == "Kelompok Uji"
    assert info.anggota[0].nama == "Ani Uji"
    assert info.has_placeholder is False


def test_render_valid_banner(valid_group_file: Path) -> None:
    text = render_banner(load_group_info(valid_group_file))
    assert "ZipHive" in text
    assert "Kelompok Uji" in text
    assert "Ani Uji" in text
    assert "123456" in text
    assert "Distributed Data Compression" in text
    assert "BELUM DIISI" not in text


def test_render_placeholder_banner(placeholder_group_file: Path) -> None:
    info = load_group_info(placeholder_group_file)
    assert info.has_placeholder is True
    text = render_banner(info)
    assert "BELUM DIISI" in text
    assert "config/group.toml" in text


def test_is_placeholder() -> None:
    assert is_placeholder("<ISI NAMA>") is True
    assert is_placeholder("   ") is True
    assert is_placeholder("Kelompok Uji") is False


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_group_info(tmp_path / "tidak-ada.toml")


def test_malformed_file_raises(tmp_path: Path) -> None:
    bad = tmp_path / "rusak.toml"
    bad.write_text("ini bukan toml = = =", encoding="utf-8")
    with pytest.raises(ValueError):
        load_group_info(bad)


def test_missing_section_raises(tmp_path: Path) -> None:
    bad = tmp_path / "kurang.toml"
    bad.write_text('project_name = "ZipHive"\n', encoding="utf-8")
    with pytest.raises(ValueError):
        load_group_info(bad)
