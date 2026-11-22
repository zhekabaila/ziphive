"""Jalankan Worker ZipHive di laptop fisik dengan satu perintah (P11-T7).

Skrip mengingat `master`, `id`, dan `procs` di `config/worker.local.toml`, lalu menjalankan
`python -m pcomp.worker` berulang: setelah satu run selesai (SHUTDOWN) Worker langsung siap
untuk run berikutnya. Worker yang dimatikan Master lewat pesan `KILL` (E5) juga diulang,
tetapi Master menolak pendaftarannya sampai run itu selesai sehingga skenario fault
tolerance tetap terukur dan operator tidak perlu menyalakan launcher lagi.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from node_common import (  # noqa: E402
    DEFAULT_MASTER_PORT,
    DEFAULT_PROCS,
    DEFAULT_THROTTLE,
    DEFAULT_WORKER_ID,
    format_command,
    local_config_path,
    master_address,
    package_env,
    parse_master_address,
    read_worker_local_config,
    venv_python,
    venv_ready,
    worker_command,
    write_worker_local_config,
)
from pcomp import constants  # noqa: E402

EXIT_OK = 0
EXIT_FAIL = 1
DEFAULT_RETRY_DELAY = 5.0


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen launcher Worker."""
    parser = argparse.ArgumentParser(
        prog="start_worker", description="Jalankan Worker ZipHive di laptop ini"
    )
    parser.add_argument("--master", help="alamat Master host:port, mis. 192.168.43.10:5050")
    parser.add_argument("--id", dest="worker_id", help="identitas Worker, mis. w3")
    parser.add_argument("--procs", type=int, help="jumlah proses kompresi (resmi: 1)")
    parser.add_argument("--throttle", type=float, help="jeda per task (hanya untuk E4)")
    parser.add_argument(
        "--config", help="berkas ingatan launcher (default config/worker.local.toml)"
    )
    parser.add_argument("--once", action="store_true", help="jalankan satu proses lalu keluar")
    parser.add_argument(
        "--retry-delay", type=float, default=DEFAULT_RETRY_DELAY, help="jeda sebelum mencoba lagi"
    )
    parser.add_argument(
        "--print-command", action="store_true", help="cetak perintah Worker lalu keluar"
    )
    parser.add_argument(
        "--no-prompt", action="store_true", help="jangan bertanya interaktif; gagal bila kurang"
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="folder proyek")
    parser.add_argument("--log-dir", default=None, help="folder log (default <root>/logs)")
    return parser


def resolve_settings(args: argparse.Namespace) -> tuple[str, str, int, float]:
    """Gabungkan berkas ingatan dan argumen CLI menjadi (master, id, procs, throttle)."""
    root = Path(args.root).resolve()
    stored = read_worker_local_config(Path(args.config) if args.config else local_config_path(root))
    master = args.master or str(stored.get("master", ""))
    worker_id = args.worker_id or str(stored.get("worker_id", ""))
    procs = args.procs if args.procs is not None else int(stored.get("procs", DEFAULT_PROCS))
    if args.throttle is not None:
        throttle = args.throttle
    else:
        throttle = float(stored.get("throttle", DEFAULT_THROTTLE))
    return master, worker_id, procs, throttle


def ask_missing(master: str, worker_id: str, *, no_prompt: bool) -> tuple[str, str]:
    """Tanya operator bila master atau id belum ada; ValueError bila tidak interaktif."""
    if master and worker_id:
        return master, worker_id
    if no_prompt or not sys.stdin.isatty():
        missing = []
        if not master:
            missing.append("--master")
        if not worker_id:
            missing.append("--id")
        raise ValueError(f"{' dan '.join(missing)} wajib diisi pada pemanggilan pertama")
    if not master:
        host = input(f"IP Master (tanpa port, port {DEFAULT_MASTER_PORT}): ").strip()
        master = master_address(host, DEFAULT_MASTER_PORT)
    if not worker_id:
        worker_id = input(f"ID Worker (mis. {DEFAULT_WORKER_ID}): ").strip() or DEFAULT_WORKER_ID
    return master, worker_id


def stream(command: Sequence[str], root: Path, log_path: Path) -> int:
    """Jalankan Worker sambil menampilkan dan menyimpan keluarannya."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            list(command),
            cwd=root,
            env=package_env(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        assert process.stdout is not None
        for line in process.stdout:
            print(line, end="", flush=True)
            log.write(line)
            log.flush()
        return process.wait()


def main(argv: list[str] | None = None) -> int:
    """Jalankan Worker berulang sampai operator menghentikannya atau Master mengirim KILL."""
    args = build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    python = venv_python(root)
    if not venv_ready(root):
        print(
            f"WORKER GAGAL: {python} belum ada. Jalankan setup-node lebih dulu.",
            file=sys.stderr,
        )
        return EXIT_FAIL

    master, worker_id, procs, throttle = resolve_settings(args)
    try:
        master, worker_id = ask_missing(master, worker_id, no_prompt=args.no_prompt)
        host, port = parse_master_address(master)
    except ValueError as exc:
        print(f"WORKER GAGAL: {exc}", file=sys.stderr)
        return EXIT_FAIL
    master = master_address(host, port)
    config_path = Path(args.config) if args.config else local_config_path(root)
    write_worker_local_config(config_path, master, worker_id, procs, throttle)

    command = worker_command(python, master, worker_id, procs, throttle)
    if args.print_command:
        print(format_command(command))
        return EXIT_OK

    log_dir = Path(args.log_dir) if args.log_dir else root / "logs"
    log_path = log_dir / f"worker-{worker_id}.log"
    print(f"Worker {worker_id} -> {master} (procs={procs}, throttle={throttle})")
    print(f"Log: {log_path}")
    print("Tekan Ctrl+C untuk berhenti.")

    stop = False
    try:
        while not stop:
            code = stream(command, root, log_path)
            if args.once:
                return code
            if code == constants.EXIT_KILLED:
                print(
                    "Worker dihentikan Master lewat KILL (skenario E5). Menunggu run "
                    "berikutnya; Master akan menolak pendaftaran sampai run ini selesai.",
                    flush=True,
                )
            elif code == constants.EXIT_OK:
                print("Run selesai (SHUTDOWN). Menunggu run berikutnya...", flush=True)
            else:
                print(
                    f"Worker berhenti dengan kode {code}; mencoba lagi dalam "
                    f"{args.retry_delay:.0f} detik.",
                    flush=True,
                )
            time.sleep(args.retry_delay)
    except KeyboardInterrupt:
        stop = True
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
