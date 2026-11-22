"""Jalankan Master ZipHive di laptop fisik dan tampilkan perintah untuk 9 Worker (P11-T8).

Skrip ini menyiapkan dataset bila belum ada, mencetak IP Master beserta perintah yang harus
dijalankan di setiap laptop Worker, lalu menjalankan `python -m pcomp.master`. Gunakan
`--print-plan` untuk melihat rencana tanpa menjalankan Master.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from node_common import (  # noqa: E402
    DEFAULT_MASTER_PORT,
    format_command,
    local_ip,
    master_address,
    master_command,
    venv_python,
    venv_ready,
)
from pcomp import constants  # noqa: E402
from pcomp.master.cli import main as master_main  # noqa: E402
from pcomp.tools.make_dataset import build_dataset  # noqa: E402

EXIT_OK = 0
EXIT_FAIL = 1
DEFAULT_SIZE_MB = 2048
# Dataset resmi (ASSETS.md bagian 1.1): 8 berkas, 256 MiB per berkas, seed 20261122.
DEFAULT_FILES = 8
DEFAULT_SEED = 20261122


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen launcher Master."""
    parser = argparse.ArgumentParser(
        prog="start_master", description="Jalankan Master ZipHive untuk 9 laptop Worker"
    )
    parser.add_argument("--input", default="data/bench", help="folder dataset di laptop Master")
    parser.add_argument("--out", default="output/master", help="folder hasil run")
    parser.add_argument("--workers", type=int, default=9, help="jumlah Worker yang ditunggu")
    parser.add_argument("--port", type=int, default=DEFAULT_MASTER_PORT)
    parser.add_argument("--scheduler", choices=["dynamic", "static"], default="dynamic")
    parser.add_argument("--algo", default="lzma", choices=["gzip", "bz2", "lzma", "sim"])
    parser.add_argument("--level", type=int, default=constants.DEFAULT_LEVEL)
    parser.add_argument("--chunk-mb", type=int, default=constants.DEFAULT_CHUNK_MB)
    parser.add_argument("--repeat", type=int, default=constants.DEFAULT_REPEAT)
    parser.add_argument("--size-mb", type=int, default=DEFAULT_SIZE_MB, help="ukuran dataset baru")
    parser.add_argument(
        "--files", type=int, default=DEFAULT_FILES, help="jumlah berkas dataset baru"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="seed dataset baru")
    parser.add_argument(
        "--inject-kills", type=int, default=0, help="jumlah Worker yang dimatikan Master (E5)"
    )
    parser.add_argument("--inject-kill-fraction", type=float, default=0.5)
    parser.add_argument("--print-plan", action="store_true", help="cetak rencana lalu keluar")
    parser.add_argument("--no-dataset", action="store_true", help="jangan bangun dataset otomatis")
    parser.add_argument("--root", default=str(REPO_ROOT), help="folder proyek")
    return parser


def plan_lines(args: argparse.Namespace, ip: str) -> list[str]:
    """Baris rencana: alamat Master dan perintah di setiap laptop Worker."""
    address = master_address(ip, args.port)
    lines = [
        f"Master  : {address} (bind 0.0.0.0, port {args.port})",
        f"Dataset : {args.input}",
        f"Hasil   : {args.out}",
        f"Worker  : {args.workers} laptop, procs 1, scheduler {args.scheduler}",
        (
            f"Kompresi: {args.algo} level {args.level}, chunk {args.chunk_mb} MiB, "
            f"repeat {args.repeat}"
        ),
        "Perintah di setiap laptop Worker (setelah setup-node):",
    ]
    for index in range(1, args.workers + 1):
        lines.append(f"  python scripts/start_worker.py --master {address} --id w{index}")
    if args.inject_kills > 0:
        lines.append(
            f"E5: Master mengirim KILL ke {args.inject_kills} Worker setelah "
            f"{round(args.inject_kill_fraction * 100)}% task selesai"
        )
    return lines


def ensure_dataset(args: argparse.Namespace) -> int:
    """Bangun dataset bila belum ada; kembalikan exit code."""
    target = Path(args.input)
    if target.is_dir() and any(target.iterdir()):
        print(f"Dataset siap: {target}")
        return EXIT_OK
    if args.no_dataset:
        print(f"MASTER GAGAL: dataset {target} tidak ada (--no-dataset aktif)", file=sys.stderr)
        return EXIT_FAIL
    print(f"Membuat dataset {args.size_mb} MiB di {target} (sekali saja, perlu beberapa menit)")
    build_dataset(target, size_mb=args.size_mb, files=args.files, seed=args.seed)
    print(f"Dataset siap: {target}")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    """Siapkan dataset, cetak rencana, lalu jalankan Master."""
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    ip = local_ip()
    for line in plan_lines(args, ip):
        print(line, flush=True)

    if args.print_plan:
        print("PLAN OK")
        return EXIT_OK

    python = venv_python(root)
    if not venv_ready(root):
        print(
            f"MASTER GAGAL: {python} belum ada. Jalankan setup-node lebih dulu.",
            file=sys.stderr,
        )
        return EXIT_FAIL

    if ensure_dataset(args) != EXIT_OK:
        return EXIT_FAIL

    command = master_command(
        python,
        args.input,
        args.out,
        args.workers,
        port=args.port,
        scheduler=args.scheduler,
        algo=args.algo,
        level=args.level,
        chunk_mb=args.chunk_mb,
        repeat=args.repeat,
        inject_kills=args.inject_kills,
        inject_kill_fraction=args.inject_kill_fraction,
    )
    print(f"$ {format_command(command)}", flush=True)
    # Buang tiga elemen pertama (interpreter, -m, nama modul) agar sisa argv diteruskan
    # ke parser Master tanpa menjalankan proses Python kedua.
    return master_main(command[3:])


if __name__ == "__main__":
    raise SystemExit(main())
