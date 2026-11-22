"""Siapkan satu laptop ZipHive: venv lokal, dependensi, dan pemeriksaan node (P11-T6).

Dijalankan sekali di setiap laptop (Master maupun Worker) melalui wrapper
`setup-node.command` (macOS), `setup-node.sh` (Linux), atau `setup-node.bat` (Windows).
Python sistem tidak diubah: semua paket dipasang di `.venv` dalam folder proyek.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from node_common import (  # noqa: E402
    MIN_PYTHON,
    VERSION_HINT,
    bootstrap_commands,
    describe_version,
    format_command,
    package_env,
    venv_python,
    venv_ready,
    version_ok,
)

EXIT_OK = 0
EXIT_FAIL = 1


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen penyiapan node."""
    parser = argparse.ArgumentParser(
        prog="bootstrap_node", description="Siapkan venv dan dependensi ZipHive di laptop ini"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="hanya periksa Python lalu cetak SETUP OK"
    )
    parser.add_argument(
        "--no-install", action="store_true", help="buat venv tanpa memasang paket (offline)"
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="interpreter yang dipakai membuat venv (default: python yang menjalankan skrip)",
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="folder proyek")
    return parser


def run(command: Sequence[str], root: Path) -> int:
    """Jalankan satu perintah dan kembalikan exit code-nya."""
    print(f"$ {format_command(command)}", flush=True)
    completed = subprocess.run(list(command), cwd=root, env=package_env(root), check=False)
    return completed.returncode


def main(argv: list[str] | None = None) -> int:
    """Periksa Python, siapkan venv, pasang paket, lalu jalankan `check_node.py`."""
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    python = venv_python(root)

    print(f"ZipHive setup node di {root}", flush=True)
    print(f"Python yang dipakai: {describe_version(sys.version_info)} ({sys.executable})")
    if not version_ok(sys.version_info):
        print(
            f"SETUP GAGAL: butuh Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} atau lebih baru. "
            f"{VERSION_HINT}",
            file=sys.stderr,
        )
        return EXIT_FAIL

    if args.check_only:
        state = "sudah ada" if venv_ready(root) else "belum dibuat"
        print(f"venv: {python} ({state})")
        print("SETUP OK (mode periksa; jalankan tanpa --check-only untuk menyiapkan)")
        return EXIT_OK

    if not venv_ready(root):
        create_command, install_command = bootstrap_commands(root, args.python)
        if run(create_command, root) != 0:
            print("SETUP GAGAL: pembuatan venv tidak berhasil", file=sys.stderr)
            return EXIT_FAIL
    else:
        print(f"venv sudah ada: {python}")
        install_command = bootstrap_commands(root, args.python)[1]

    if not args.no_install and run(install_command, root) != 0:
        print(
            "SETUP GAGAL: pemasangan paket tidak berhasil (periksa koneksi internet)",
            file=sys.stderr,
        )
        return EXIT_FAIL

    check = [str(python), str(root / "scripts" / "check_node.py")]
    if run(check, root) != 0:
        print("SETUP GAGAL: check_node.py melaporkan masalah", file=sys.stderr)
        return EXIT_FAIL

    print("SETUP OK")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
