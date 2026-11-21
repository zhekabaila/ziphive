"""Paket ZIP sumber untuk pengumpulan (PLAN.md P8-T3, SUBMISSION.md bagian 1).

Arsip dibuat dari daftar putih: kode, test, skrip, konfigurasi, dokumen `.md`, dan
folder `results/` (ringkasan serta grafik). `data/`, `output/`, `.venv`, `.git`,
cache, dan `results/dev` (hasil algoritma `sim`) tidak ikut dipaketkan.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
import zipfile
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = "dist"

# Folder tingkat atas yang ikut dipaketkan.
INCLUDED_TOP_LEVEL = frozenset(
    {
        "src",
        "tests",
        "scripts",
        "config",
        "docs",
        "results",
        "Makefile",
        "pyproject.toml",
        "requirements.txt",
        "requirements-worker.txt",
        "requirements-dev.txt",
    }
)
# Dokumen tingkat atas ikut lewat akhiran `.md`.
INCLUDED_SUFFIXES = frozenset({".md"})
EXCLUDED_DIRS = frozenset(
    {
        ".git",
        ".venv",
        "venv",
        "data",
        "output",
        "build",
        "dist",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".idea",
        ".vscode",
        "htmlcov",
    }
)
EXCLUDED_FILE_SUFFIXES = frozenset({".pyc", ".pyo"})
EXCLUDED_PATHS = frozenset({"results/dev"})
EXIT_OK = 0
EXIT_FAIL = 1


def is_excluded(relative: str) -> bool:
    """True bila path relatif tidak boleh masuk arsip sumber."""
    path = Path(relative)
    parts = path.as_posix().split("/")
    if any(part in EXCLUDED_DIRS for part in parts[:-1]):
        return True
    if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return True
    posix = path.as_posix()
    return any(posix == blocked or posix.startswith(f"{blocked}/") for blocked in EXCLUDED_PATHS)


def iter_source_files(repo_root: Path) -> list[Path]:
    """Pindai pohon repo dan kembalikan berkas yang boleh dipaketkan."""
    repo_root = Path(repo_root)
    if not repo_root.is_dir():
        raise FileNotFoundError(f"folder repo tidak ditemukan: {repo_root}")

    found: list[Path] = []
    for entry in sorted(repo_root.iterdir(), key=lambda item: item.name):
        if entry.is_dir():
            if entry.name not in INCLUDED_TOP_LEVEL or entry.name in EXCLUDED_DIRS:
                continue
            candidates = [path for path in entry.rglob("*") if path.is_file()]
        else:
            is_doc = entry.suffix.lower() in INCLUDED_SUFFIXES
            if entry.name not in INCLUDED_TOP_LEVEL and not is_doc:
                continue
            candidates = [entry]
        for path in candidates:
            relative = path.relative_to(repo_root).as_posix()
            if not is_excluded(relative):
                found.append(path)
    return sorted(found, key=lambda path: path.relative_to(repo_root).as_posix())


def build_zip(repo_root: Path, out_path: Path, files: Sequence[Path]) -> Path:
    """Tulis arsip ZIP berisi `files` dengan nama relatif terhadap `repo_root`."""
    repo_root = Path(repo_root)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, path.relative_to(repo_root).as_posix())
    return out_path


def read_version(repo_root: Path) -> str:
    """Ambil versi proyek dari `pyproject.toml`."""
    path = Path(repo_root) / "pyproject.toml"
    if not path.is_file():
        return "0.0.0"
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return str(data.get("project", {}).get("version", "0.0.0"))


def default_archive_name(version: str) -> str:
    """Nama berkas arsip baku."""
    return f"ziphive-source-{version}.zip"


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen `pack_source.py`."""
    parser = argparse.ArgumentParser(
        prog="pack_source.py", description="Paketkan sumber ZipHive menjadi ZIP"
    )
    parser.add_argument("--repo", default=str(REPO_ROOT), help="folder repo yang dipaketkan")
    parser.add_argument("--out", default=None, help="path arsip (bawaan: dist/<nama baku>)")
    parser.add_argument("--list", action="store_true", help="cetak daftar berkas tanpa membuat ZIP")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Buat arsip sumber dan cetak ringkasannya."""
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo)
    try:
        files = iter_source_files(repo_root)
    except FileNotFoundError as exc:
        print(f"PACK GAGAL: {exc}", file=sys.stderr)
        return EXIT_FAIL

    if args.list:
        for path in files:
            print(path.relative_to(repo_root).as_posix())
        print(f"PACK OK: {len(files)} berkas (tidak ada arsip dibuat)")
        return EXIT_OK

    out_path = (
        Path(args.out)
        if args.out
        else repo_root / DEFAULT_OUT_DIR / default_archive_name(read_version(repo_root))
    )
    try:
        build_zip(repo_root, out_path, files)
    except OSError as exc:
        print(f"PACK GAGAL: {exc}", file=sys.stderr)
        return EXIT_FAIL

    size_kib = out_path.stat().st_size / 1024
    print(f"berkas : {len(files)}")
    print(f"arsip  : {out_path}")
    print(f"ukuran : {size_kib:.1f} KiB")
    print("PACK OK")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
