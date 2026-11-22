"""Orkestrasi eksperimen E1-E6 pada 10 node.

Dua mode Worker (`--worker-mode`):
- `docker` (ADR-015): Worker berjalan sebagai container `ziphive-node:min` di satu laptop.
  Skrip menyalakan container sebelum tiap run dan mematikannya pada E5.
- `external` (ADR-016): Worker berjalan di 9 laptop fisik lewat `scripts/start_worker.py`.
  Skrip hanya menyiapkan argumen, mencetak instruksi, dan menunggu Worker terdaftar; E5
  dijalankan Master sendiri lewat pesan `KILL`.

Pada kedua mode, `verify.log` disimpan dan payload chunk dihapus agar disk tidak penuh
(metrics, events, manifest, dan log tetap disimpan).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from pcomp.metrics.events import EventLog, read_events

REPO = Path(__file__).resolve().parent.parent
IMAGE = "ziphive-node:min"
POLL_SEC = 0.2


@dataclass(frozen=True)
class ContainerSpec:
    """Satu container Worker beserta jeda per task (E4)."""

    name: str
    worker_id: str
    throttle: float


def container_specs(workers: int, throttle: float = 0.0) -> list[ContainerSpec]:
    """Satu container per Worker; throttle hanya untuk Worker terakhir (seperti E4 runner)."""
    specs: list[ContainerSpec] = []
    for index in range(1, workers + 1):
        slow = throttle if throttle > 0 and index == workers else 0.0
        specs.append(ContainerSpec(f"ziphive-w{index}", f"w{index}", slow))
    return specs


def read_progress(events_path: Path) -> tuple[int, int]:
    """(task selesai, task yang diharapkan) dari `events.jsonl`."""
    if not events_path.is_file():
        return 0, 0
    try:
        rows = read_events(events_path)
    except (json.JSONDecodeError, OSError):
        return 0, 0
    expected = 0
    done = 0
    for row in rows:
        if row.get("event") == "run_started" and not expected:
            expected = int(row.get("tasks", 0) or 0)
        elif row.get("event") == "task_done":
            done += 1
    return done, expected


def wait_port(port: int, timeout: float = 90.0) -> None:
    """Tunggu Master menerima koneksi TCP."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(POLL_SEC)
    raise RuntimeError(f"Master tidak siap pada port {port}")


def docker(*args: str) -> subprocess.CompletedProcess[str]:
    """Jalankan perintah docker tanpa melempar eksepsi."""
    return subprocess.run(["docker", *args], capture_output=True, text=True, check=False)


def start_container(spec: ContainerSpec, port: int) -> None:
    """Jalankan satu container Worker yang menunjuk Master di host."""
    docker("rm", "-f", spec.name)
    command = [
        "run",
        "-d",
        "--name",
        spec.name,
        "--hostname",
        spec.worker_id,
        "-v",
        f"{REPO}:/app:ro",
        "-e",
        "PYTHONPATH=/app/src",
        "-w",
        "/app",
        IMAGE,
        "python3",
        "-m",
        "pcomp.worker",
        "--master",
        f"host.docker.internal:{port}",
        "--id",
        spec.worker_id,
        "--procs",
        "1",
    ]
    if spec.throttle > 0:
        command += ["--throttle", str(spec.throttle)]
    result = docker(*command)
    if result.returncode != 0:
        raise RuntimeError(f"gagal menjalankan {spec.name}: {result.stderr.strip()}")


def emit_kill(events_path: Path, worker_id: str, reason: str) -> None:
    """Catat `worker_exit_injected` agar detection latency dan recovery time terukur."""
    log = EventLog(events_path)
    try:
        log.emit("worker_exit_injected", worker_id=worker_id, pid=0, reason=reason)
    finally:
        log.close()


def kill_at_fraction(
    run_dir: Path, specs: list[ContainerSpec], fraction: float, timeout: float
) -> None:
    """Matikan Worker pertama setelah sebagian task selesai (E5)."""
    events_path = run_dir / "events.jsonl"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        done, expected = read_progress(events_path)
        if expected and done >= max(1, int(expected * fraction)):
            break
        time.sleep(POLL_SEC)
    for spec in specs:
        emit_kill(events_path, spec.worker_id, "bench-e5")
        docker("kill", spec.name)
        print(f"  E5: {spec.worker_id} dimatikan setelah {done}/{expected} task", flush=True)


def wait_master_port(master_log: Path, timeout: float = 120.0) -> int:
    """Baca port Master dari log run itu sendiri (runner memilih port bebas)."""
    deadline = time.monotonic() + timeout
    pattern = re.compile(r"mendengarkan di \S+:(\d+)")
    while time.monotonic() < deadline:
        if master_log.is_file():
            match = pattern.search(master_log.read_text(encoding="utf-8", errors="replace"))
            if match is not None:
                return int(match.group(1))
        time.sleep(POLL_SEC)
    raise RuntimeError(f"port Master tidak terbaca dari {master_log}")


def wait_run_line(run_id: str, log_path: Path, timeout: float) -> None:
    """Tunggu baris hasil run pada log harness (ditulis setelah verify selesai)."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.is_file() else ""
        if f"{run_id}: " in text:
            for line in text.splitlines():
                if line.startswith(f"{run_id}: ") and "verify=" in line:
                    if "verify=True" not in line:
                        raise RuntimeError(line)
                    return
        if "BENCH GAGAL" in text:
            raise RuntimeError(text.strip().splitlines()[-1])
        time.sleep(POLL_SEC)
    raise RuntimeError(f"run {run_id} tidak selesai dalam batas waktu")


def collect_logs(run_dir: Path, specs: list[ContainerSpec]) -> None:
    """Simpan log tiap container ke folder run."""
    for spec in specs:
        result = docker("logs", spec.name)
        text = (result.stdout or "") + (result.stderr or "")
        (run_dir / f"worker-{spec.worker_id}.log").write_text(text, encoding="utf-8")


def remove_containers(specs: list[ContainerSpec]) -> None:
    """Bersihkan container setelah run selesai."""
    for spec in specs:
        docker("rm", "-f", spec.name)


def required_artifacts(run_dir: Path) -> tuple[str, ...]:
    """Berkas wajib per run; `events.jsonl` hanya ditulis pada mode terdistribusi."""
    names = ["metrics.json", "manifest.json"]
    spec = run_dir / "spec.json"
    distributed = True
    if spec.is_file():
        try:
            distributed = json.loads(spec.read_text(encoding="utf-8")).get("mode") == "distributed"
        except (json.JSONDecodeError, OSError):
            distributed = True
    if distributed:
        names.append("events.jsonl")
    return tuple(names)


def check_artifacts(run_dir: Path) -> None:
    """Pastikan berkas hasil wajib ada sebelum verifikasi."""
    for name in required_artifacts(run_dir):
        if not (run_dir / name).is_file():
            raise RuntimeError(f"{name} tidak ada di {run_dir}")


def finalize_run(run_dir: Path, keep_payload: bool) -> None:
    """Jalankan verify, simpan keluarannya, lalu hapus payload chunk bila diminta."""
    check_artifacts(run_dir)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pcomp.tools.verify", "--manifest", str(run_dir / "manifest.json")],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    (run_dir / "verify.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode != 0 or "VERIFY OK" not in result.stdout:
        raise RuntimeError(f"VERIFY gagal pada {run_dir}")
    chunks = run_dir / "chunks"
    if not keep_payload and chunks.is_dir():
        shutil.rmtree(chunks)
        (run_dir / "cleanup.txt").write_text(
            "payload chunks dihapus setelah VERIFY OK untuk menghemat disk; "
            "manifest.json menyimpan hash tiap chunk.\n",
            encoding="utf-8",
        )


def next_run_dir(root: Path, exp: str, handled: set[str]) -> Path | None:
    """Folder run berikutnya yang belum ditangani."""
    base = root / exp
    if not base.is_dir():
        return None
    for path in sorted(base.iterdir()):
        if not path.is_dir() or path.name in handled:
            continue
        if (path / "metrics.json").is_file():
            continue
        if (path / "spec.json").is_file():
            return path
    return None


def run_experiment(
    exp: str,
    extra: list[str],
    root: Path,
    *,
    manage_containers: bool,
    kill_fraction: float,
    timeout: float,
    keep_payload: bool,
    wait_extra: float = 0.0,
) -> int:
    """Jalankan satu eksperimen lengkap sambil mengelola container per run."""
    log_path = root / exp / "bench.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO / "src")
    env["PYTHONUNBUFFERED"] = "1"
    command = [sys.executable, "-u", "-m", "pcomp.bench.runner", "--exp", exp, *extra]
    handled: set[str] = set()
    with log_path.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            command, stdout=handle, stderr=subprocess.STDOUT, text=True, env=env
        )
        try:
            while True:
                finished = process.poll() is not None
                run_dir = next_run_dir(root, exp, handled)
                if run_dir is None:
                    if finished:
                        break
                    time.sleep(POLL_SEC)
                    continue
                if manage_containers:
                    spec = json.loads((run_dir / "spec.json").read_text(encoding="utf-8"))
                    specs = container_specs(
                        int(spec.get("workers", 0) or 0), float(spec.get("throttle", 0.0) or 0.0)
                    )
                    kills = int(spec.get("kill_workers", 0) or 0)
                    try:
                        port = wait_master_port(run_dir / "master.log", timeout)
                        wait_port(port)
                        for item in specs:
                            start_container(item, port)
                        if kills:
                            kill_at_fraction(run_dir, specs[:kills], kill_fraction, timeout)
                        wait_run_line(run_dir.name, log_path, timeout)
                    finally:
                        collect_logs(run_dir, specs)
                        remove_containers(specs)
                else:
                    # Worker sudah berjalan di laptop masing-masing; harness menunggu
                    # registrasi sampai --lan-wait sebelum run dihitung.
                    wait_run_line(run_dir.name, log_path, timeout + wait_extra)
                finalize_run(run_dir, keep_payload)
                print(f"  selesai: {run_dir.name}", flush=True)
                handled.add(run_dir.name)
        finally:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=30)
    return process.returncode


def clean_baselines(root: Path) -> None:
    """Hapus payload pada run baseline sequential setelah eksperimen selesai."""
    base = root / "baseline"
    if not base.is_dir():
        return
    for path in sorted(base.iterdir()):
        chunks = path / "chunks"
        if chunks.is_dir() and (path / "metrics.json").is_file():
            shutil.rmtree(chunks)
            (path / "cleanup.txt").write_text(
                "payload chunks dihapus setelah metrics.json tertulis.\n", encoding="utf-8"
            )


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen orkestrasi eksperimen."""
    parser = argparse.ArgumentParser(prog="run_experiments", description="Orkestrasi E1-E6")
    parser.add_argument("--exps", default="E1,E2,E3,E4,E5,E6", help="daftar eksperimen")
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--pause", type=float, default=30.0, help="jeda antar run (detik)")
    parser.add_argument("--input", default="data/bench")
    parser.add_argument("--algo", default="lzma")
    parser.add_argument("--level", type=int, default=6)
    parser.add_argument("--chunk-mb", type=int, default=4)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--workers", default="1,2,4,6,9", help="jumlah Worker untuk E6")
    parser.add_argument("--procs", default="1,2,4,8", help="jumlah proses untuk E2")
    parser.add_argument("--throttle", type=float, default=0.25, help="jeda per task Worker E4")
    parser.add_argument("--kill-workers", default="1,3", help="skenario E5")
    parser.add_argument("--kill-fraction", type=float, default=0.5)
    parser.add_argument("--out-root", default="results/raw")
    parser.add_argument("--timeout", type=float, default=1800.0)
    parser.add_argument("--keep-payload", action="store_true", help="jangan hapus chunk")
    parser.add_argument(
        "--worker-mode",
        choices=["docker", "external"],
        default="docker",
        help="docker = container di satu laptop; external = 9 laptop fisik",
    )
    parser.add_argument(
        "--port", type=int, default=5050, help="port Master pada mode external (harus tetap)"
    )
    parser.add_argument(
        "--lan-wait",
        type=float,
        default=900.0,
        help="detik menunggu Worker terdaftar pada mode external",
    )
    return parser


def uses_containers(extra: list[str]) -> bool:
    """True bila run memakai container (mode `--lan`)."""
    return "--lan" in extra


def lan_args(args: argparse.Namespace, common: list[str]) -> list[str]:
    """Argumen runner untuk run terdistribusi.

    Mode `external` memakai port tetap dan `--lan-wait` besar agar Worker di laptop lain
    punya waktu menyala dan mendaftar.
    """
    extra = [*common, "--lan", "--host", "0.0.0.0", "--barrier-timeout", "300"]
    if getattr(args, "worker_mode", "docker") == "external":
        extra += ["--port", str(args.port), "--lan-wait", str(args.lan_wait)]
    return extra


def experiment_args(
    exp: str, args: argparse.Namespace, common: list[str]
) -> tuple[list[str], bool]:
    """Susun argumen runner untuk satu eksperimen (EXPERIMENTS.md bagian 2)."""
    if exp == "E1":
        return [*common, "--local"], False
    if exp == "E2":
        return [*common, "--local", "--procs", args.procs], False
    lan = lan_args(args, common)
    if exp == "E3":
        return [*lan, "--workers", "9"], True
    if exp == "E4":
        return [*lan, "--workers", "9", "--throttle", str(args.throttle)], True
    if exp == "E6":
        return [*lan, "--workers", args.workers], True
    raise ValueError(f"eksperimen tidak dikenal: {exp}")


def main(argv: list[str] | None = None) -> int:
    """Jalankan seluruh eksperimen yang diminta."""
    args = build_parser().parse_args(argv)
    root = Path(args.out_root)
    common = [
        "--reps",
        str(args.reps),
        "--pause",
        str(args.pause),
        "--input",
        args.input,
        "--algo",
        args.algo,
        "--level",
        str(args.level),
        "--chunk-mb",
        str(args.chunk_mb),
        "--repeat",
        str(args.repeat),
    ]
    if args.out_root != "results/raw":
        common += ["--out-root", args.out_root]

    for exp in [item.strip() for item in args.exps.split(",") if item.strip()]:
        print(f"=== {exp} ===", flush=True)
        attempts: list[list[str]] = []
        if exp == "E5":
            lan_base = lan_args(args, common)
            for scenario in [item.strip() for item in args.kill_workers.split(",") if item.strip()]:
                attempts.append(
                    [
                        *lan_base,
                        "--workers",
                        "9",
                        "--kill-workers",
                        scenario,
                        "--kill-fraction",
                        str(args.kill_fraction),
                    ]
                )
        else:
            extra, _ = experiment_args(exp, args, common)
            attempts.append(extra)

        for extra in attempts:
            code = run_experiment(
                exp,
                extra,
                root,
                manage_containers=args.worker_mode == "docker",
                kill_fraction=args.kill_fraction,
                timeout=args.timeout,
                keep_payload=args.keep_payload,
                wait_extra=args.lan_wait,
            )
            if code != 0:
                print(
                    f"{exp} GAGAL (kode {code}); lihat {root / exp / 'bench.log'}", file=sys.stderr
                )
                return code
            clean_baselines(root)
    print("SEMUA EKSPERIMEN SELESAI")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
