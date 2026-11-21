"""UT-PACK-01..03: paket ZIP sumber tanpa data, output, venv, dan riwayat git (P8-T3)."""

from __future__ import annotations

import zipfile
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

Loader = Callable[[str], ModuleType]


@pytest.fixture
def pack(load_script: Loader) -> ModuleType:
    return load_script("pack_source.py")


def make_repo(root: Path) -> Path:
    """Pohon repo palsu berisi file yang boleh dan tidak boleh dipaketkan."""
    files = [
        "src/pcomp/constants.py",
        "tests/unit/test_pack_source.py",
        "scripts/gate.py",
        "config/nodes.toml",
        "docs/phase-logs/PHASE-08.md",
        "results/raw/E3/run1/metrics.json",
        "results/dev/summary.csv",
        "pyproject.toml",
        "requirements.txt",
        "Makefile",
        "AGENTS.md",
        "data/silesia/dickens",
        "output/run1/manifest.json",
        ".venv/lib/site-packages/psutil/__init__.py",
        ".git/HEAD",
        "src/pcomp/__pycache__/constants.cpython-314.pyc",
        ".pytest_cache/v/cache/nodeids",
    ]
    for name in files:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"isi {name}\n", encoding="utf-8")
    return root


def test_is_excluded_rules(pack: ModuleType) -> None:
    """UT-PACK-01: aturan pengecualian sesuai PLAN.md P8-T3 dan SUBMISSION.md bagian 1."""
    for path in (
        "data/silesia/dickens",
        "output/run1/manifest.json",
        ".venv/lib/x.py",
        ".git/HEAD",
        "src/pcomp/__pycache__/a.pyc",
        "results/dev/summary.csv",
        "build/lib/x.py",
        "x/y.pyc",
    ):
        assert pack.is_excluded(path) is True, path

    for path in (
        "src/pcomp/constants.py",
        "docs/phase-logs/PHASE-08.md",
        "results/summary.csv",
        "results/figures/speedup.png",
        "AGENTS.md",
        "tests/conftest.py",
    ):
        assert pack.is_excluded(path) is False, path


def test_iter_source_files(pack: ModuleType, tmp_path: Path) -> None:
    """UT-PACK-02: pemindaian pohon sumber hanya mengambil berkas yang diizinkan."""
    root = make_repo(tmp_path / "repo")
    found = pack.iter_source_files(root)
    relative = [path.relative_to(root).as_posix() for path in found]

    assert relative == sorted(relative)
    assert "src/pcomp/constants.py" in relative
    assert "results/raw/E3/run1/metrics.json" in relative
    assert all(not item.startswith(("data/", "output/", ".venv/", ".git/")) for item in relative)
    assert "results/dev/summary.csv" not in relative
    assert not any("__pycache__" in item for item in relative)

    empty = tmp_path / "kosong"
    empty.mkdir()
    assert pack.iter_source_files(empty) == []


def test_build_zip_and_main(
    pack: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-PACK-03: ZIP terbentuk, tanpa berkas terlarang, dan `main` mencetak PACK OK."""
    root = make_repo(tmp_path / "repo")
    out = tmp_path / "hasil" / "ziphive-source.zip"
    path = pack.build_zip(root, out, pack.iter_source_files(root))

    assert path == out
    with zipfile.ZipFile(out) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert "src/pcomp/constants.py" in names
        assert "data/silesia/dickens" not in names
        assert all(not name.startswith(".venv/") for name in names)
        assert archive.read("src/pcomp/constants.py").startswith(b"isi src/pcomp")

    capsys.readouterr()
    archive_path = tmp_path / "repo-pack.zip"
    assert pack.main(["--repo", str(root), "--out", str(archive_path)]) == 0
    output = capsys.readouterr().out
    assert "PACK OK" in output
    assert archive_path.is_file()

    assert pack.default_archive_name("0.07.0") == "ziphive-source-0.07.0.zip"
