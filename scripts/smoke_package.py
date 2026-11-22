"""Smoke test paket sumber Fase 10 (PLAN.md fase 10: "ZIP terbuat dan dapat dijalankan dari nol").

Alur: bangun ZIP memakai `scripts/pack_source.py`, ekstrak ke folder sementara,
periksa isi yang dilarang, lalu jalankan perintah dari nol sesuai `README.md`
(`make_dataset`, `sequential`, `verify`, `--version`) memakai `PYTHONPATH=src`
tanpa memasang paket. Semua langkah harus berhasil.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ENTRIES = (
    "pyproject.toml",
    "README.md",
    "src/pcomp/__init__.py",
    "src/pcomp/master/server.py",
    "src/pcomp/worker/client.py",
    "tests/unit",
    "docs/CODE_GUIDE.md",
    "docs/DEMO_SCRIPT.md",
    "docs/ANALYSIS.md",
    "results/summary.csv",
    "results/summary_agg.csv",
    "config/group.toml",
)
FORBIDDEN_PREFIXES = (
    "data/",
    "output/",
    "reports/",
    ".venv/",
    "venv/",
    ".git/",
    "dist/",
    "results/dev/",
)
FORBIDDEN_PARTS = ("__pycache__/", ".pytest_cache/", ".mypy_cache/", ".ruff_cache/")
STEP_TIMEOUT = 180


def run_step(label: str, command: list[str], workdir: Path, env: dict[str, str]) -> str:
    """Jalankan satu perintah dan kembalikan keluarannya, gagal bila rc bukan nol."""
    completed = subprocess.run(
        command,
        cwd=str(workdir),
        env=env,
        capture_output=True,
        text=True,
        timeout=STEP_TIMEOUT,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(f"{label} gagal (rc={completed.returncode}): {command}\n{output}")
    return output


def build_archive(repo_root: Path, out_path: Path) -> None:
    """Bangun ZIP sumber memakai skrip paket yang sama dengan pengumpulan."""
    completed = subprocess.run(
        [sys.executable, "scripts/pack_source.py", "--out", str(out_path)],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=STEP_TIMEOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"pack_source gagal: {completed.stdout}{completed.stderr}")


def check_entries(names: list[str]) -> list[str]:
    """Kembalikan daftar pelanggaran isi arsip."""
    problems: list[str] = []
    for name in names:
        if name.startswith(FORBIDDEN_PREFIXES):
            problems.append(f"entri terlarang: {name}")
        if any(part in name for part in FORBIDDEN_PARTS):
            problems.append(f"berkas cache ikut: {name}")
    for required in REQUIRED_ENTRIES:
        if not any(name == required or name.startswith(f"{required}/") for name in names):
            problems.append(f"entri wajib tidak ditemukan: {required}")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Titik masuk `smoke_package.py`."""
    parser = argparse.ArgumentParser(prog="smoke_package.py", description="Smoke test paket ZIP")
    parser.add_argument("--repo", default=str(REPO_ROOT), help="folder repo yang dipaketkan")
    parser.add_argument("--keep", action="store_true", help="jangan hapus folder sementara")
    args = parser.parse_args(argv)
    repo_root = Path(args.repo)

    temp_root = Path(tempfile.mkdtemp(prefix="ziphive-smoke-"))
    archive = temp_root / "ziphive-source.zip"
    work = temp_root / "extracted"
    try:
        build_archive(repo_root, archive)
        with zipfile.ZipFile(archive) as handle:
            names = handle.namelist()
            problems = check_entries(names)
            if problems:
                for problem in problems:
                    print(f"MASALAH: {problem}", file=sys.stderr)
                print("PACKAGE FAIL", file=sys.stderr)
                return 1
            handle.extractall(work)

        env = dict(os.environ)
        env["PYTHONPATH"] = str(work / "src")
        steps = [
            (
                "versi",
                [sys.executable, "-m", "pcomp", "--version"],
                "ZipHive",
            ),
            (
                "dataset",
                [
                    sys.executable,
                    "-m",
                    "pcomp.tools.make_dataset",
                    "--out",
                    "data/smoke",
                    "--size-mb",
                    "2",
                    "--files",
                    "1",
                    "--seed",
                    "1",
                ],
                "OK",
            ),
            (
                "sequential",
                [
                    sys.executable,
                    "-m",
                    "pcomp.sequential",
                    "--input",
                    "data/smoke",
                    "--out",
                    "output/smoke",
                ],
                "SEQUENTIAL OK",
            ),
            (
                "verify",
                [
                    sys.executable,
                    "-m",
                    "pcomp.tools.verify",
                    "--manifest",
                    "output/smoke/manifest.json",
                ],
                "VERIFY OK",
            ),
        ]
        for label, command, expected in steps:
            output = run_step(label, command, work, env)
            if expected not in output:
                print(
                    f"MASALAH: langkah {label} tidak mencetak {expected}\n{output}",
                    file=sys.stderr,
                )
                print("PACKAGE FAIL", file=sys.stderr)
                return 1

        size_kib = archive.stat().st_size / 1024
        print(f"arsip  : {len(names)} entri, {size_kib:.1f} KiB")
        print(f"ekstrak: dijalankan dari nol di folder sementara ({work.name})")
        print(f"PACKAGE OK: {len(names)} entri, {len(REQUIRED_ENTRIES)} entri wajib lengkap")
        return 0
    finally:
        if not args.keep:
            import shutil

            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
