"""Harness benchmark E1-E6 dengan metadata lingkungan (PLAN.md P7-T3, P7-T5).

Mode `--local` menjalankan Master dan Worker sebagai proses di mesin ini.
Mode `--lan` hanya menjalankan Master; Worker dijalankan manual di node lain
sesuai EXPERIMENTS.md bagian 5. Hasil algoritma `sim` ditulis ke `results/dev/`.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import socket
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

import psutil

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.bench.report import aggregate, plot_all, write_aggregate_csv
from pcomp.compressor import is_simulated
from pcomp.local_parallel import run_local
from pcomp.metrics import calc
from pcomp.metrics.events import read_events
from pcomp.metrics.system import (
    SystemLog,
    SystemSampler,
    read_system_csv,
    summarise_usage,
)
from pcomp.sequential import run_sequential
from pcomp.tools.make_dataset import build_dataset

DEFAULT_WORKERS = "1,2,4,6,9"
DEFAULT_PROCS = "1,2,4"
DEFAULT_REPS = 3
DEFAULT_SIZE_MB = 8
DEFAULT_FILES = 4
DEFAULT_TIMEOUT = 900.0

SUMMARY_COLUMNS = (
    "exp",
    "run_id",
    "rep",
    "mode",
    "workers",
    "procs",
    "scheduler",
    "kill_workers",
    "algo",
    "level",
    "chunk_mb",
    "repeat",
    "total_mb",
    "tasks",
    "time_s",
    "throughput_mbs",
    "ratio",
    "speedup_seq",
    "speedup_rel",
    "efficiency",
    "imbalance",
    "cpu_avg_master",
    "cpu_avg_workers",
    "mem_avg_master",
    "mem_avg_workers",
    "detect_s",
    "recovery_s",
    "retried_tasks",
    "verify_ok",
    "started_at",
)

DEV_ROOT = Path("results") / "dev"
RAW_ROOT = Path("results") / "raw"
REAL_SUMMARY = Path("results") / "summary.csv"
REAL_FIGURES = Path("results") / "figures"

EXPERIMENTS = ("E1", "E2", "E3", "E4", "E5", "E6")
DEFAULT_E3_WORKERS = 9


# ---------------------------------------------------------------------------
# Rencana run
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunSpec:
    """Satu konfigurasi yang dijalankan satu kali."""

    exp: str
    mode: str
    workers: int
    procs: int
    scheduler: str
    throttle: float = 0.0
    kill_workers: int = 0


def plan_runs(
    exp: str,
    *,
    workers: Sequence[int],
    procs: Sequence[int],
    reps: int,
    scheduler: str = "dynamic",
    throttle: float = 0.0,
    kill_workers: int = 1,
) -> list[RunSpec]:
    """Susun matriks run untuk eksperimen E1-E6 (EXPERIMENTS.md bagian 2)."""
    if exp == "E1":
        return [RunSpec(exp="E1", mode="sequential", workers=0, procs=1, scheduler="none")]
    if exp == "E2":
        return [
            RunSpec(exp="E2", mode="local", workers=0, procs=count, scheduler="none")
            for count in procs
        ]
    distributed = max(workers) if workers else DEFAULT_E3_WORKERS
    if exp == "E3":
        return [
            RunSpec(
                exp="E3",
                mode="distributed",
                workers=DEFAULT_E3_WORKERS,
                procs=1,
                scheduler=scheduler,
            )
        ]
    if exp == "E4":
        return [
            RunSpec(
                exp="E4",
                mode="distributed",
                workers=distributed,
                procs=1,
                scheduler=name,
                throttle=throttle,
            )
            for name in ("static", "dynamic")
        ]
    if exp == "E5":
        return [
            RunSpec(
                exp="E5",
                mode="distributed",
                workers=distributed,
                procs=1,
                scheduler=scheduler,
                kill_workers=max(1, kill_workers),
            )
        ]
    if exp == "E6":
        return [
            RunSpec(exp="E6", mode="distributed", workers=count, procs=1, scheduler=scheduler)
            for count in workers
        ]
    raise ValueError(f"eksperimen tidak dikenal: {exp} (pilihan: {', '.join(EXPERIMENTS)})")


# ---------------------------------------------------------------------------
# Lokasi keluaran (hasil sim tidak boleh masuk results/raw)
# ---------------------------------------------------------------------------


def results_root(algo: str, out_root: Path | None = None) -> Path:
    """Folder induk run: `results/dev` untuk `sim`, `results/raw` untuk algoritma nyata."""
    if out_root is not None:
        return out_root
    return DEV_ROOT if is_simulated(algo) else RAW_ROOT


def summary_path(algo: str, out_root: Path | None = None) -> Path:
    """Lokasi `summary.csv`; EXPERIMENTS.md bagian 4 memakai `results/summary.csv`."""
    if out_root is not None:
        return out_root / "summary.csv"
    return DEV_ROOT / "summary.csv" if is_simulated(algo) else REAL_SUMMARY


def figures_dir(algo: str, out_root: Path | None = None) -> Path:
    """Folder grafik PNG."""
    if out_root is not None:
        return out_root / "figures"
    return DEV_ROOT / "figures" if is_simulated(algo) else REAL_FIGURES


# ---------------------------------------------------------------------------
# Metadata lingkungan (P7-T5)
# ---------------------------------------------------------------------------


def collect_env() -> dict[str, Any]:
    """Metadata lingkungan yang ikut dicatat pada setiap run."""
    total_ram = psutil.virtual_memory().total / (1024**3)
    return {
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "os": f"{platform.system()} {platform.release()}",
        "python_version": platform.python_version(),
        "cpu": platform.processor() or platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False) or 1,
        "logical_cores": psutil.cpu_count(logical=True) or 1,
        "ram_gb": round(total_ram, 3),
        "date": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def write_env(run_dir: Path, env: Mapping[str, Any]) -> Path:
    """Tulis `env.json` pada folder run."""
    path = run_dir / constants.BENCH_ENV_NAME
    path.write_text(json.dumps(dict(env), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Baris ringkasan
# ---------------------------------------------------------------------------


def build_row(
    metrics: Mapping[str, Any],
    *,
    exp: str,
    run_id: str,
    rep: int,
    mode: str,
    workers: int,
    procs: int,
    scheduler: str,
    kill_workers: int = 0,
    speedup_seq: float | None = None,
    speedup_rel: float | None = None,
    imbalance: float | None = None,
    detect_s: float | None = None,
    recovery_s: float | None = None,
    retried_tasks: int | None = None,
    verify_ok: bool = False,
    cpu_avg_master: float | None = None,
    cpu_avg_workers: float | None = None,
    mem_avg_master: float | None = None,
    mem_avg_workers: float | None = None,
) -> dict[str, Any]:
    """Susun satu baris summary.csv dari metrics.json plus hasil hitungan."""
    time_s = float(metrics.get("time_s", 0.0) or 0.0)
    total_mb = float(metrics.get("total_mb", 0.0) or 0.0)
    throughput = metrics.get("throughput_mbs")
    if throughput is None:
        throughput = total_mb / time_s if time_s > 0 else 0.0

    units = workers if mode == "distributed" else (procs if mode == "local" else 1)
    eff = None if speedup_seq is None else calc.efficiency(float(speedup_seq), units)

    imbalance = metrics.get("imbalance") if imbalance is None else imbalance
    if imbalance is None:
        busy = metrics.get("busy_per_process")
        if isinstance(busy, Mapping) and busy:
            imbalance = calc.imbalance_factor([float(value) for value in busy.values()])

    values: dict[str, Any] = {
        "exp": exp,
        "run_id": run_id,
        "rep": rep,
        "mode": mode,
        "workers": workers,
        "procs": procs,
        "scheduler": scheduler,
        "kill_workers": int(kill_workers),
        "algo": str(metrics.get("algo", "")),
        "level": metrics.get("level", 0),
        "chunk_mb": metrics.get("chunk_mb", 0),
        "repeat": metrics.get("repeat", 0),
        "total_mb": round(total_mb, 6),
        "tasks": int(metrics.get("tasks", 0) or 0),
        "time_s": round(time_s, 6),
        "throughput_mbs": round(float(throughput), 6),
        "ratio": metrics.get("ratio", 0.0),
        "speedup_seq": None if speedup_seq is None else round(float(speedup_seq), 6),
        "speedup_rel": None if speedup_rel is None else round(float(speedup_rel), 6),
        "efficiency": None if eff is None else round(eff, 6),
        "imbalance": None if imbalance is None else round(float(imbalance), 6),
        "cpu_avg_master": cpu_avg_master,
        "cpu_avg_workers": cpu_avg_workers,
        "mem_avg_master": mem_avg_master,
        "mem_avg_workers": mem_avg_workers,
        "detect_s": detect_s,
        "recovery_s": recovery_s,
        "retried_tasks": retried_tasks,
        "verify_ok": bool(verify_ok),
        "started_at": metrics.get("started_at", ""),
    }
    return {column: values[column] for column in SUMMARY_COLUMNS}


def append_summary(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    """Tambahkan baris ke summary.csv; header ditulis bila file baru."""
    path.parent.mkdir(parents=True, exist_ok=True)
    has_rows = path.is_file() and path.stat().st_size > 0
    import csv

    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_COLUMNS))
        if not has_rows:
            writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    column: ("" if row.get(column) is None else row.get(column))
                    for column in SUMMARY_COLUMNS
                }
            )
    return path


def read_summary_rows(path: Path) -> list[dict[str, Any]]:
    """Baca seluruh baris summary.csv agar grafik mencakup semua eksperimen."""
    import csv

    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]


def run_dirs_from_rows(root: Path, rows: Sequence[Mapping[str, Any]]) -> list[Path]:
    """Folder run yang dirujuk summary, dipakai grafik beban dan timeline pemulihan."""
    paths = [root / str(row.get("exp")) / str(row.get("run_id")) for row in rows]
    return [path for path in paths if path.is_dir()]


def fill_speedup_rel(rows: Sequence[dict[str, Any]]) -> None:
    """Isi S_rel = T(1 Worker) / T(n) dari run 1 Worker pada eksperimen yang sama."""
    baselines: dict[str, float] = {}
    for row in rows:
        if row["workers"] == 1 and row["time_s"] > 0:
            baselines.setdefault(row["exp"], float(row["time_s"]))
    for row in rows:
        base = baselines.get(row["exp"])
        if base is None or row["workers"] <= 1:
            continue
        if row["time_s"] > 0:
            row["speedup_rel"] = round(base / float(row["time_s"]), 6)


# ---------------------------------------------------------------------------
# Eksekusi satu run
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _spawn(
    module: str, args: Sequence[str], log_path: Path
) -> tuple[subprocess.Popen[str], TextIO]:
    """Jalankan satu modul dengan keluaran ke file log agar pipe tidak penuh."""
    handle = log_path.open("w", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, "-m", module, *args],
        stdout=handle,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=dict(os.environ),
    )
    return process, handle


def _wait_port(port: int, process: subprocess.Popen[str], timeout: float = 60.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"Master berhenti sebelum siap (kode {process.returncode})")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise RuntimeError("Master tidak siap dalam batas waktu")


def _read_metrics(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "metrics.json"
    if not path.is_file():
        raise RuntimeError(f"metrics.json tidak ditemukan di {run_dir}")
    return dict(json.loads(path.read_text(encoding="utf-8")))


def _sample_around(run_dir: Path, action: Any) -> Any:
    """Jalankan `action` sambil mencatat system.csv untuk run non-distributed."""
    log = SystemLog(run_dir / constants.SYSTEM_CSV_NAME)
    sampler = SystemSampler(
        log.write,
        role="local",
        node=socket.gethostname(),
        interval=constants.SYSTEM_SAMPLE_INTERVAL,
    )
    sampler.sample_once()
    sampler.start()
    try:
        return action()
    finally:
        sampler.stop()
        log.close()


def _run_sequential(args: argparse.Namespace, run_dir: Path) -> dict[str, Any]:
    def action() -> Any:
        return run_sequential(
            args.input_dir,
            run_dir,
            algo=args.algo,
            level=args.level,
            chunk_mb=args.chunk_mb,
            repeat=args.repeat,
        )

    result = _sample_around(run_dir, action)
    return dict(result.metrics)


def _run_local(args: argparse.Namespace, spec: RunSpec, run_dir: Path) -> dict[str, Any]:
    def action() -> Any:
        return run_local(
            args.input_dir,
            run_dir,
            algo=args.algo,
            level=args.level,
            chunk_mb=args.chunk_mb,
            repeat=args.repeat,
            procs=spec.procs,
        )

    result = _sample_around(run_dir, action)
    return dict(result.metrics)


def _inject_kills(
    run_dir: Path,
    workers: Sequence[subprocess.Popen[str]],
    count: int,
    fraction: float,
    timeout: float,
) -> None:
    """Hentikan `count` Worker pertama setelah sebagian task selesai (E5)."""
    events_path = run_dir / "events.jsonl"
    deadline = time.monotonic() + timeout
    expected: int | None = None
    while time.monotonic() < deadline:
        rows: list[dict[str, Any]] = []
        if events_path.is_file():
            try:
                rows = read_events(events_path)
            except (json.JSONDecodeError, OSError):
                rows = []
        for row in rows:
            if row.get("event") == "run_started" and expected is None:
                expected = int(row.get("tasks", 0))
        done = sum(1 for row in rows if row.get("event") == "task_done")
        if expected and done >= max(1, int(expected * fraction)):
            break
        time.sleep(0.05)

    for index, process in enumerate(list(workers)[:count], start=1):
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pcomp.tools.inject_failure",
                "--events",
                str(events_path),
                "--pid",
                str(process.pid),
                "--worker-id",
                f"w{index}",
                "--reason",
                "bench-e5",
            ],
            check=False,
            timeout=60,
        )


def _master_args(args: argparse.Namespace, spec: RunSpec, run_dir: Path, port: int) -> list[str]:
    return [
        "--input",
        str(args.input_dir),
        "--out",
        str(run_dir),
        "--host",
        args.host,
        "--port",
        str(port),
        "--expect-workers",
        str(spec.workers),
        "--algo",
        args.algo,
        "--level",
        str(args.level),
        "--chunk-mb",
        str(args.chunk_mb),
        "--repeat",
        str(args.repeat),
        "--scheduler",
        spec.scheduler,
        "--barrier-timeout",
        str(args.barrier_timeout),
    ]


def _worker_args(args: argparse.Namespace, spec: RunSpec, port: int, index: int) -> list[str]:
    extra: list[str] = []
    if spec.throttle > 0 and index == spec.workers:
        extra += ["--throttle", str(spec.throttle)]
    return [
        "--master",
        f"127.0.0.1:{port}",
        "--id",
        f"w{index}",
        "--procs",
        str(args.worker_procs),
        *extra,
    ]


def _run_distributed(args: argparse.Namespace, spec: RunSpec, run_dir: Path) -> dict[str, Any]:
    port = _free_port()
    master, master_log = _spawn(
        "pcomp.master", _master_args(args, spec, run_dir, port), run_dir / "master.log"
    )
    handles: list[TextIO] = [master_log]
    workers: list[subprocess.Popen[str]] = []
    try:
        _wait_port(port, master)
        for index in range(1, spec.workers + 1):
            process, handle = _spawn(
                "pcomp.worker",
                _worker_args(args, spec, port, index),
                run_dir / f"worker-w{index}.log",
            )
            workers.append(process)
            handles.append(handle)
        if spec.kill_workers > 0:
            _inject_kills(run_dir, workers, spec.kill_workers, args.kill_fraction, args.timeout)

        code = master.wait(timeout=args.timeout)
        if code != 0:
            raise RuntimeError(f"Master keluar dengan kode {code}; lihat {run_dir / 'master.log'}")
        for process in workers:
            process.wait(timeout=args.timeout)
    finally:
        for process in [master, *workers]:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
        for handle in handles:
            handle.close()
    return _read_metrics(run_dir)


def _run_lan(args: argparse.Namespace, spec: RunSpec, run_dir: Path) -> dict[str, Any]:
    port = args.port or _free_port()
    master, master_log = _spawn(
        "pcomp.master", _master_args(args, spec, run_dir, port), run_dir / "master.log"
    )
    try:
        print(f"LAN: jalankan {spec.workers} Worker di node menuju {args.host}:{port}")
        code = master.wait(timeout=args.timeout)
        if code != 0:
            raise RuntimeError(f"Master keluar dengan kode {code}; lihat {run_dir / 'master.log'}")
    finally:
        if master.poll() is None:
            master.terminate()
            master.wait(timeout=30)
        master_log.close()
    return _read_metrics(run_dir)


def _verify(run_dir: Path) -> bool:
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcomp.tools.verify",
            "--manifest",
            str(run_dir / "manifest.json"),
        ],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        env=dict(os.environ),
    )
    return completed.returncode == 0 and "VERIFY OK" in completed.stdout


def _execute(args: argparse.Namespace, spec: RunSpec, run_dir: Path) -> dict[str, Any]:
    if spec.mode == "sequential":
        return _run_sequential(args, run_dir)
    if spec.mode == "local":
        return _run_local(args, spec, run_dir)
    if args.lan:
        return _run_lan(args, spec, run_dir)
    return _run_distributed(args, spec, run_dir)


def _event_stats(run_dir: Path) -> calc.RecoveryStats:
    path = run_dir / "events.jsonl"
    if not path.is_file():
        return calc.RecoveryStats(None, None, None, None, 0)
    try:
        return calc.recovery_stats(read_events(path))
    except (json.JSONDecodeError, OSError):
        return calc.RecoveryStats(None, None, None, None, 0)


def _prepare_dataset(args: argparse.Namespace) -> Path:
    if args.input:
        return Path(args.input)
    target = Path(args.data_root)
    build_dataset(target, size_mb=args.size_mb, files=args.files)
    return target


def _run_baseline(args: argparse.Namespace, root: Path) -> float:
    """Ukur T_seq sekali per pemanggilan untuk kolom speedup_seq."""
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
    run_dir = root / "baseline" / f"seq-{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    write_env(run_dir, collect_env())
    metrics = _run_sequential(args, run_dir)
    return float(metrics.get("time_s", 0.0))


def pause_between_runs(seconds: float) -> None:
    """Jeda antar run agar node kembali dingin (EXPERIMENTS.md bagian 1)."""
    if seconds > 0:
        time.sleep(seconds)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_list(text: str) -> list[int]:
    values = [int(part.strip()) for part in text.split(",") if part.strip()]
    if not values:
        raise ValueError("daftar angka tidak boleh kosong")
    return values


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen harness benchmark."""
    parser = argparse.ArgumentParser(
        prog="pcomp.bench.runner", description="Harness benchmark E1-E6 ZipHive"
    )
    parser.add_argument("--exp", required=True, choices=list(EXPERIMENTS))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--local", action="store_true", help="jalankan Master dan Worker di mesin ini"
    )
    mode.add_argument("--lan", action="store_true", help="Worker dijalankan manual di node lain")
    parser.add_argument(
        "--workers", default=DEFAULT_WORKERS, help="daftar jumlah Worker, mis. 1,2,9"
    )
    parser.add_argument("--procs", default=DEFAULT_PROCS, help="daftar proses untuk E2, mis. 1,2,4")
    parser.add_argument(
        "--worker-procs", type=int, default=2, help="proses per Worker (distributed)"
    )
    parser.add_argument("--reps", type=int, default=DEFAULT_REPS, help="ulangan tiap konfigurasi")
    parser.add_argument(
        "--pause",
        type=float,
        default=0.0,
        help="jeda detik antar run; EXPERIMENTS.md bagian 1 menetapkan 30",
    )
    parser.add_argument("--algo", default="lzma", choices=["gzip", "bz2", "lzma", "sim"])
    parser.add_argument("--level", type=int, default=constants.DEFAULT_LEVEL)
    parser.add_argument("--chunk-mb", type=int, default=constants.DEFAULT_CHUNK_MB)
    parser.add_argument("--repeat", type=int, default=constants.DEFAULT_REPEAT)
    parser.add_argument("--scheduler", choices=["static", "dynamic"], default="dynamic")
    parser.add_argument("--throttle", type=float, default=0.0, help="jeda Worker terakhir (E4)")
    parser.add_argument("--kill-workers", type=int, default=1, help="Worker yang dimatikan pada E5")
    parser.add_argument(
        "--kill-fraction", type=float, default=0.5, help="fraksi task selesai saat kill"
    )
    parser.add_argument(
        "--input", default=None, help="folder dataset; kosong = bangun dataset sintetis"
    )
    parser.add_argument("--data-root", default=str(Path("data") / "bench"))
    parser.add_argument("--size-mb", type=int, default=DEFAULT_SIZE_MB)
    parser.add_argument("--files", type=int, default=DEFAULT_FILES)
    parser.add_argument("--out-root", default=None, help="timpa folder induk hasil")
    parser.add_argument("--host", default="127.0.0.1", help="alamat bind Master")
    parser.add_argument("--port", type=int, default=0, help="port Master (0 = pilih otomatis)")
    parser.add_argument("--barrier-timeout", type=float, default=120.0)
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="batas waktu satu run"
    )
    parser.add_argument("--no-report", action="store_true", help="lewati pembuatan grafik")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan satu eksperimen lengkap dan tulis summary beserta grafik."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    args.input_dir = _prepare_dataset(args)
    out_root = Path(args.out_root) if args.out_root else None
    root = results_root(args.algo, out_root)
    env = collect_env()

    try:
        baseline = None if args.exp == "E1" else _run_baseline(args, root)
        pause_between_runs(args.pause)
        specs = plan_runs(
            args.exp,
            workers=_parse_list(args.workers),
            procs=_parse_list(args.procs),
            reps=args.reps,
            scheduler=args.scheduler,
            throttle=args.throttle,
            kill_workers=args.kill_workers,
        )

        rows: list[dict[str, Any]] = []
        run_dirs: list[Path] = []
        # Ulangan di luar, konfigurasi di dalam: mengurangi bias bila beban mesin bergeser
        # selama eksperimen berjalan.
        for rep in range(1, args.reps + 1):
            for spec in specs:
                stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%f")
                run_id = f"{spec.exp}-w{spec.workers}-p{spec.procs}-{spec.scheduler}-r{rep}-{stamp}"
                run_dir = root / spec.exp / run_id
                run_dir.mkdir(parents=True, exist_ok=True)
                write_env(run_dir, env)
                (run_dir / "spec.json").write_text(
                    json.dumps(
                        {
                            "exp": spec.exp,
                            "mode": spec.mode,
                            "workers": spec.workers,
                            "procs": spec.procs,
                            "scheduler": spec.scheduler,
                            "throttle": spec.throttle,
                            "kill_workers": spec.kill_workers,
                            "algo": args.algo,
                            "level": args.level,
                            "chunk_mb": args.chunk_mb,
                            "repeat": args.repeat,
                            "rep": rep,
                        },
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )

                metrics = _execute(args, spec, run_dir)
                time_s = float(metrics.get("time_s", 0.0) or 0.0)
                if baseline is not None and time_s > 0:
                    speedup_seq: float | None = baseline / time_s
                elif spec.exp == "E1":
                    speedup_seq = 1.0
                else:
                    speedup_seq = None

                usage = summarise_usage(read_system_csv(run_dir / constants.SYSTEM_CSV_NAME))
                stats = _event_stats(run_dir)
                verify_ok = _verify(run_dir)
                row = build_row(
                    metrics,
                    exp=spec.exp,
                    run_id=run_id,
                    rep=rep,
                    mode=spec.mode,
                    workers=spec.workers,
                    procs=spec.procs,
                    scheduler=spec.scheduler,
                    kill_workers=spec.kill_workers,
                    speedup_seq=speedup_seq,
                    detect_s=stats.detect_s,
                    recovery_s=stats.recovery_s,
                    retried_tasks=stats.retried_tasks,
                    verify_ok=verify_ok,
                    cpu_avg_master=usage.cpu_avg_master,
                    cpu_avg_workers=usage.cpu_avg_workers,
                    mem_avg_master=usage.mem_avg_master,
                    mem_avg_workers=usage.mem_avg_workers,
                )
                rows.append(row)
                run_dirs.append(run_dir)
                print(
                    f"{run_id}: workers={spec.workers} procs={spec.procs} "
                    f"time_s={row['time_s']} tasks={row['tasks']} verify={verify_ok}"
                )
                if not verify_ok:
                    raise RuntimeError(f"verifikasi gagal pada {run_dir} (lihat manifest.json)")
                pause_between_runs(args.pause)

        fill_speedup_rel(rows)
        summary = append_summary(summary_path(args.algo, out_root), rows)

        figures: list[Path] = []
        if not args.no_report:
            # Grafik dan agregat dibuat dari SELURUH baris summary.csv, bukan hanya
            # eksperimen terakhir, agar artefak laporan tidak saling menimpa.
            all_rows = read_summary_rows(summary_path(args.algo, out_root))
            all_dirs = run_dirs_from_rows(root, all_rows)
            figures = plot_all(
                all_rows, run_dirs=all_dirs, out_dir=figures_dir(args.algo, out_root)
            )
            aggregate_path = figures_dir(args.algo, out_root).parent / "summary_agg.csv"
            write_aggregate_csv(aggregate_path, aggregate(all_rows))
    except (RuntimeError, OSError, ValueError) as exc:
        print(f"BENCH GAGAL: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR

    print(f"exp          : {args.exp}")
    print(f"mode         : {'lan' if args.lan else 'local'}")
    print(f"runs         : {len(rows)}")
    print(f"baseline_s   : {baseline if baseline is None else round(baseline, 6)}")
    print(f"summary      : {summary}")
    print(f"figures      : {len(figures)} berkas di {figures_dir(args.algo, out_root)}")
    print("BENCH OK")
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
