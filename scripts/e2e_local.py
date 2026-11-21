"""End-to-end localhost: 1 Master + N Worker (PLAN.md P4-T6, P5-T5).

Menjalankan proses nyata lewat subprocess, memilih port bebas, lalu memverifikasi
manifest. Keluaran akhir `E2E OK` untuk satu scheduler, atau `LB COMPARE OK` bila
`--compare` membandingkan static dan dynamic dengan satu Worker lambat.
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
    parser.add_argument("--repeat", type=int, default=1, help="ulangi seluruh daftar task")
    parser.add_argument(
        "--algo", default="lzma", choices=["gzip", "bz2", "lzma", "sim"], help="algoritma"
    )
    parser.add_argument("--level", type=int, default=6, help="level kompresi")
    parser.add_argument("--worker-procs", type=int, default=2, help="proses kompresi per Worker")
    parser.add_argument(
        "--scheduler", default="dynamic", choices=["static", "dynamic"], help="jenis scheduler"
    )
    parser.add_argument(
        "--throttle", type=float, default=None, help="detik jeda per task pada Worker terakhir"
    )
    parser.add_argument(
        "--compare",
        action="store_true",
        help="jalankan static lalu dynamic dengan satu Worker lambat dan cetak perbandingan",
    )
    parser.add_argument(
        "--slow-throttle",
        type=float,
        default=0.5,
        help="jeda per task untuk Worker lambat pada mode --compare",
    )
    parser.add_argument(
        "--fail-after-tasks",
        type=int,
        default=0,
        help="Worker pertama keluar paksa setelah K task (0 = nonaktif)",
    )
    parser.add_argument(
        "--fail-after-sec",
        type=float,
        default=0.0,
        help="Worker pertama keluar paksa setelah S detik (0 = nonaktif)",
    )
    parser.add_argument(
        "--task-fail-rate",
        type=float,
        default=0.0,
        help="peluang task gagal pada semua Worker (0.0 sampai 1.0)",
    )
    parser.add_argument("--seed", type=int, default=1, help="seed kegagalan task")
    parser.add_argument("--heartbeat-interval", type=float, default=None)
    parser.add_argument("--heartbeat-timeout", type=float, default=None)
    parser.add_argument("--max-attempts", type=int, default=None)
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


def run_once(
    args: argparse.Namespace,
    env: dict[str, str],
    input_dir: Path,
    out_dir: Path,
    scheduler: str,
    slow_throttle: float,
) -> dict:
    """Jalankan satu konfigurasi Master + N Worker dan kembalikan isi metrics.json."""
    port = free_port()
    # EventLog menambah baris ke file yang sudah ada; hapus agar hitungan event
    # hanya berasal dari run ini.
    (out_dir / "events.jsonl").unlink(missing_ok=True)
    master: subprocess.Popen[str] | None = None
    workers: list[subprocess.Popen[str]] = []
    master_extra: list[str] = []
    if args.heartbeat_interval is not None:
        master_extra += ["--heartbeat-interval", str(args.heartbeat_interval)]
    if args.heartbeat_timeout is not None:
        master_extra += ["--heartbeat-timeout", str(args.heartbeat_timeout)]
    if args.max_attempts is not None:
        master_extra += ["--max-attempts", str(args.max_attempts)]
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
                "--repeat",
                str(args.repeat),
                "--scheduler",
                scheduler,
                "--barrier-timeout",
                "60",
                *master_extra,
            ],
            env,
        )
        wait_for_port(port, master)
        for index in range(1, args.workers + 1):
            extra: list[str] = []
            if slow_throttle > 0 and index == args.workers:
                extra = ["--throttle", str(slow_throttle)]
            if index == 1 and args.fail_after_tasks > 0:
                extra += ["--fail-after-tasks", str(args.fail_after_tasks)]
            if index == 1 and args.fail_after_sec > 0:
                extra += ["--fail-after-sec", str(args.fail_after_sec)]
            if args.task_fail_rate > 0:
                extra += [
                    "--task-fail-rate",
                    str(args.task_fail_rate),
                    "--seed",
                    str(args.seed),
                ]
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
                        *extra,
                    ],
                    env,
                )
            )

        master_code = master.wait(timeout=args.timeout)
        master_out, master_err = master.communicate(timeout=10)
        if master_code != 0:
            raise RuntimeError(
                f"Master keluar dengan kode {master_code}:\n{master_out}\n{master_err}"
            )

        injected = args.fail_after_tasks > 0 or args.fail_after_sec > 0
        for index, worker in enumerate(workers, start=1):
            worker_code = worker.wait(timeout=60)
            worker_out, worker_err = worker.communicate(timeout=10)
            if worker_code != 0 and not (injected and index == 1):
                raise RuntimeError(
                    f"Worker keluar dengan kode {worker_code}:\n{worker_out}\n{worker_err}"
                )

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
            raise RuntimeError(f"verifikasi manifest gagal:\n{verify.stdout}\n{verify.stderr}")
        metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
        if injected:
            events = _read_events(out_dir / "events.jsonl")
            dead = [item for item in events if item.get("event") == "worker_dead"]
            if not dead:
                raise RuntimeError("event worker_dead tidak ditemukan pada events.jsonl")
            metrics["_worker_dead"] = len(dead)
        return metrics
    finally:
        for proc in [*workers, master]:
            if proc is not None and proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)


def _counts_text(metrics: dict) -> str:
    items = [f"{item['worker_id']}={item['tasks_done']}" for item in metrics["worker_stats"]]
    return ",".join(items)


def _read_events(path: Path) -> list[dict]:
    """Baca events.jsonl tanpa ketergantungan paket (skrip dapat dijalankan langsung)."""
    rows: list[dict] = []
    if not path.is_file():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _print_metrics(metrics: dict) -> None:
    print(f"workers      : {metrics['workers']}")
    print(f"tasks        : {metrics['tasks']}")
    print(f"tasks_ok     : {metrics['tasks_ok']}")
    print(f"tasks_failed : {metrics['tasks_failed']}")
    print(f"total_mb     : {metrics['total_mb']}")
    print(f"ratio        : {metrics['ratio']}")
    print(f"time_s       : {metrics['time_s']}")


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

    try:
        if args.compare:
            static = run_once(
                args, env, input_dir, out_dir / "static", "static", args.slow_throttle
            )
            dynamic = run_once(
                args, env, input_dir, out_dir / "dynamic", "dynamic", args.slow_throttle
            )
            print("scheduler  time_s   imbalance  tasks_per_worker")
            print(
                f"static     {static['time_s']:<8} {static['imbalance']:<10} {_counts_text(static)}"
            )
            print(
                f"dynamic    {dynamic['time_s']:<8} {dynamic['imbalance']:<10} "
                f"{_counts_text(dynamic)}"
            )
            if dynamic["time_s"] > static["time_s"] - 0.1:
                print("LB COMPARE GAGAL: dynamic tidak lebih cepat dari static")
                return 1
            if dynamic["imbalance"] > static["imbalance"]:
                print("LB COMPARE GAGAL: dynamic tidak lebih seimbang dari static")
                return 1
            print("LB COMPARE OK")
            return 0

        throttle = args.throttle if args.throttle is not None else 0.0
        metrics = run_once(args, env, input_dir, out_dir, args.scheduler, throttle)
        _print_metrics(metrics)
        if "_worker_dead" in metrics:
            print(f"worker_dead  : {metrics['_worker_dead']}")
        print("VERIFY OK")
        print("E2E OK")
        return 0
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"E2E GAGAL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
