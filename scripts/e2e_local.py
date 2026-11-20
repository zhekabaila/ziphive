"""End-to-end localhost: 1 Master + N Worker (PLAN.md P4-T6).

Menjalankan proses nyata lewat subprocess, memilih port bebas, lalu memverifikasi
manifest. Keluaran akhir `E2E OK` bila seluruh rangkaian lulus.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"


def free_port() -> int:
    """Cari port TCP bebas di localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_for_port(port: int, proc: subprocess.Popen[str], timeout: float = 30.0) -> None:
    """Tunggu Master menerima koneksi pertama."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=5)
            raise RuntimeError(f"Master berhenti sebelum siap:\n{out}\n{err}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("Master tidak siap dalam batas waktu")


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen skrip e2e."""
    parser = argparse.ArgumentParser(
        prog="e2e_local.py", description="Uji end-to-end Master-Worker di localhost"
    )
    parser.add_argument("--workers", type=int, default=3, help="jumlah Worker")
    parser.add_argument("--input", default=None, help="folder dataset (default: sintetis baru)")
    parser.add_argument("--out", default="output/e2e", help="folder keluaran Master")
    parser.add_argument("--size-mb", type=int, default=8, help="ukuran dataset sintetis (MiB)")
    parser.add_argument("--chunk-mb", type=int, default=2, help="ukuran chunk (MiB)")
    parser.add_argument(
        "--algo", default="lzma", choices=["gzip", "bz2", "lzma", "sim"], help="algoritma"
    )
    parser.add_argument("--level", type=int, default=6, help="level kompresi")
    parser.add_argument("--worker-procs", type=int, default=2, help="proses kompresi per Worker")
    parser.add_argument("--timeout", type=float, default=300.0, help="batas waktu total (detik)")
    return parser


def _module(args: list[str], env: dict[str, str]) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-m", *args],
        cwd=REPO_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def main(argv: list[str] | None = None) -> int:
    """Jalankan Master dan N Worker, lalu verifikasi hasil."""
    args = build_parser().parse_args(argv)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(SRC_DIR) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )

    if args.input is None:
        from pcomp.tools.make_dataset import build_dataset

        dataset = REPO_ROOT / "data" / "e2e-synth"
        build_dataset(dataset, size_mb=args.size_mb, seed=1)
        input_dir = dataset
    else:
        input_dir = Path(args.input)
    out_dir = Path(args.out)

    port = free_port()
    master: subprocess.Popen[str] | None = None
    workers: list[subprocess.Popen[str]] = []
    try:
        master = _module(
            [
                "pcomp.master",
                "--input",
                str(input_dir),
                "--out",
                str(out_dir),
                "--host",
                "127.0.0.1",
                "--port",
                str(port),
                "--expect-workers",
                str(args.workers),
                "--algo",
                args.algo,
                "--level",
                str(args.level),
                "--chunk-mb",
                str(args.chunk_mb),
                "--barrier-timeout",
                "60",
            ],
            env,
        )
        wait_for_port(port, master)
        for index in range(1, args.workers + 1):
            workers.append(
                _module(
                    [
                        "pcomp.worker",
                        "--master",
                        f"127.0.0.1:{port}",
                        "--id",
                        f"w{index}",
                        "--procs",
                        str(args.worker_procs),
                    ],
                    env,
                )
            )

        master_code = master.wait(timeout=args.timeout)
        master_out, master_err = master.communicate(timeout=10)
        if master_code != 0:
            print(master_out, end="")
            print(master_err, end="", file=sys.stderr)
            print("E2E GAGAL: Master keluar dengan kode bukan nol")
            return 1

        for worker in workers:
            worker_code = worker.wait(timeout=60)
            worker_out, worker_err = worker.communicate(timeout=10)
            if worker_code != 0:
                print(worker_out, end="")
                print(worker_err, end="", file=sys.stderr)
                print("E2E GAGAL: ada Worker keluar dengan kode bukan nol")
                return 1

        verify = subprocess.run(
            [
                sys.executable,
                "-m",
                "pcomp.tools.verify",
                "--manifest",
                str(out_dir / "manifest.json"),
            ],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if verify.returncode != 0 or "VERIFY OK" not in verify.stdout:
            print(verify.stdout, end="")
            print(verify.stderr, end="", file=sys.stderr)
            print("E2E GAGAL: verifikasi manifest gagal")
            return 1

        metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
        print(f"workers      : {metrics['workers']}")
        print(f"tasks        : {metrics['tasks']}")
        print(f"tasks_ok     : {metrics['tasks_ok']}")
        print(f"tasks_failed : {metrics['tasks_failed']}")
        print(f"total_mb     : {metrics['total_mb']}")
        print(f"ratio        : {metrics['ratio']}")
        print(f"time_s       : {metrics['time_s']}")
        print(verify.stdout.strip().splitlines()[-1])
        print("E2E OK")
        return 0
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"E2E GAGAL: {exc}")
        return 1
    finally:
        for proc in [*workers, master]:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)


if __name__ == "__main__":
    raise SystemExit(main())
