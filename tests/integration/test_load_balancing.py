"""IT-LB-01..02: perbandingan static vs dynamic di localhost (PLAN.md Fase 5)."""

from __future__ import annotations

import json
import socket
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from pcomp.manifest import read_manifest, verify_entries
from pcomp.tools.make_dataset import build_dataset

pytestmark = pytest.mark.integration

FAST_WORKER = "w1"
SLOW_WORKER = "w2"
SLOW_THROTTLE = 0.5
EXPECTED_TASKS = 10  # 4 file data + dataset.json, masing-masing 1 chunk, diulang 2 kali


def wait_until_ready(port: int, proc: subprocess.Popen[str], timeout: float = 20.0) -> None:
    """Tunggu port Master menerima koneksi."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            out, err = proc.communicate(timeout=5)
            raise AssertionError(f"Master berhenti lebih awal: {out}\n{err}")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.settimeout(0.2)
            if probe.connect_ex(("127.0.0.1", port)) == 0:
                return
        time.sleep(0.05)
    raise AssertionError("Master tidak siap dalam batas waktu")


def run_cluster(
    tmp_path: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
    scheduler: str,
) -> dict:
    """Jalankan satu Master + dua Worker (satu lambat) dengan scheduler tertentu."""
    dataset = tmp_path / "data"
    build_dataset(dataset, size_mb=4, seed=1)
    out_dir = tmp_path / f"out-{scheduler}"
    master = start_master(
        "--input",
        str(dataset),
        "--out",
        str(out_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--expect-workers",
        "2",
        "--algo",
        "sim",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--repeat",
        "2",
        "--scheduler",
        scheduler,
        "--barrier-timeout",
        "15",
    )
    wait_until_ready(free_port, master)
    workers = [
        start_worker("--master", f"127.0.0.1:{free_port}", "--id", FAST_WORKER, "--procs", "1"),
        start_worker(
            "--master",
            f"127.0.0.1:{free_port}",
            "--id",
            SLOW_WORKER,
            "--procs",
            "1",
            "--throttle",
            str(SLOW_THROTTLE),
        ),
    ]

    assert master.wait(timeout=120) == 0
    for worker in workers:
        assert worker.wait(timeout=30) == 0

    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    manifest = read_manifest(out_dir / "manifest.json")
    assert all(item.ok for item in verify_entries(manifest, out_dir))
    return metrics


def tasks_per_worker(metrics: dict) -> dict[str, int]:
    return {item["worker_id"]: item["tasks_done"] for item in metrics["worker_stats"]}


def test_dynamic_has_smaller_makespan_and_imbalance(
    tmp_path: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-LB-01: dynamic lebih cepat dan lebih seimbang dari static (margin toleransi)."""
    static = run_cluster(tmp_path, start_master, start_worker, free_port, "static")
    dynamic = run_cluster(tmp_path, start_master, start_worker, free_port, "dynamic")

    assert static["scheduler"] == "static"
    assert dynamic["scheduler"] == "dynamic"
    assert static["tasks_ok"] == dynamic["tasks_ok"] == EXPECTED_TASKS
    assert static["simulated"] is True and dynamic["simulated"] is True

    assert dynamic["time_s"] <= static["time_s"] - 0.5
    assert dynamic["imbalance"] <= static["imbalance"] - 0.05


def test_static_is_even_and_dynamic_is_uneven(
    tmp_path: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-LB-02: static membagi rata, dynamic memberi lebih sedikit ke Worker lambat."""
    static = run_cluster(tmp_path, start_master, start_worker, free_port, "static")
    dynamic = run_cluster(tmp_path, start_master, start_worker, free_port, "dynamic")

    static_counts = tasks_per_worker(static)
    dynamic_counts = tasks_per_worker(dynamic)

    assert sorted(static_counts.values()) == [EXPECTED_TASKS // 2, EXPECTED_TASKS // 2]
    assert dynamic_counts[SLOW_WORKER] < dynamic_counts[FAST_WORKER]
    assert max(dynamic_counts.values()) - min(dynamic_counts.values()) >= 2
    assert sum(dynamic_counts.values()) == EXPECTED_TASKS
