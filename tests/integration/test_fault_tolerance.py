"""IT-FT-01..07: fault tolerance Master-Worker di localhost (PLAN.md Fase 6)."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from pcomp.manifest import read_manifest, verify_entries
from pcomp.metrics.events import read_events

pytestmark = pytest.mark.integration


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


def wait_for_event(out_dir: Path, name: str, timeout: float = 15.0) -> dict:
    """Tunggu satu event muncul di events.jsonl dan kembalikan entrinya."""
    path = out_dir / "events.jsonl"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.is_file():
            try:
                rows = read_events(path)
            except (json.JSONDecodeError, OSError):
                rows = []
            for row in rows:
                if row.get("event") == name:
                    return row
        time.sleep(0.05)
    raise AssertionError(f"event '{name}' tidak muncul dalam {timeout} detik")


def read_metrics(out_dir: Path) -> dict:
    return json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))


def run_verify(repo_root: Path, manifest: Path) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, "-m", "pcomp.tools.verify", "--manifest", str(manifest)],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )


def master_args(
    input_dir: Path,
    out_dir: Path,
    port: int,
    workers: int,
    *,
    repeat: int = 2,
    timeout: float = 1.0,
) -> list[str]:
    return [
        "--input",
        str(input_dir),
        "--out",
        str(out_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--expect-workers",
        str(workers),
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--repeat",
        str(repeat),
        "--scheduler",
        "dynamic",
        "--heartbeat-interval",
        "0.2",
        "--heartbeat-timeout",
        str(timeout),
        "--max-attempts",
        "3",
        "--barrier-timeout",
        "20",
    ]


def test_one_worker_dies_and_all_tasks_finish(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-FT-01: satu Worker mati di tengah proses, seluruh task tetap selesai."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 2))
    wait_until_ready(free_port, master)

    dying = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "1",
        "--throttle",
        "1.2",
        "--fail-after-sec",
        "1.0",
    )
    survivor = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w2",
        "--procs",
        "2",
        "--throttle",
        "0.3",
    )

    assert master.wait(timeout=120) == 0
    assert dying.wait(timeout=30) != 0
    assert survivor.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0

    manifest = read_manifest(out_dir / "manifest.json")
    assert len(manifest.entries) == metrics["tasks"]
    assert all(item.ok for item in verify_entries(manifest, out_dir))

    names = [item["event"] for item in events_of(out_dir)]
    assert "worker_dead" in names
    assert names.count("task_requeued") >= 1

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout


def test_two_workers_die_together(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-FT-02: dua Worker mati bersamaan, sisa Worker menyelesaikan seluruh task."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 3))
    wait_until_ready(free_port, master)

    dying = [
        start_worker(
            "--master",
            f"127.0.0.1:{free_port}",
            "--id",
            f"w{index}",
            "--procs",
            "1",
            "--throttle",
            "1.2",
            "--fail-after-sec",
            "0.8",
        )
        for index in (1, 2)
    ]
    survivor = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w3",
        "--procs",
        "2",
        "--throttle",
        "0.2",
    )

    assert master.wait(timeout=120) == 0
    assert all(worker.wait(timeout=30) != 0 for worker in dying)
    assert survivor.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0

    events = events_of(out_dir)
    dead_ids = {item["worker_id"] for item in events if item["event"] == "worker_dead"}
    assert dead_ids == {"w1", "w2"}
    assert sum(1 for item in events if item["event"] == "task_requeued") >= 2

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout


def test_all_workers_die_master_aborts_cleanly(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-FT-03: semua Worker mati, Master berhenti rapi dengan pesan jelas."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 2))
    wait_until_ready(free_port, master)

    workers = [
        start_worker(
            "--master",
            f"127.0.0.1:{free_port}",
            "--id",
            f"w{index}",
            "--procs",
            "1",
            "--throttle",
            "2.0",
            "--fail-after-sec",
            "0.8",
        )
        for index in (1, 2)
    ]

    code = master.wait(timeout=120)
    out, err = master.communicate(timeout=10)
    assert code != 0
    assert "semua Worker mati" in (out + err)
    assert all(worker.wait(timeout=30) != 0 for worker in workers)

    metrics = read_metrics(out_dir)
    assert metrics["tasks_failed"] > 0
    assert metrics["tasks_ok"] < metrics["tasks"]

    manifest = read_manifest(out_dir / "manifest.json")
    assert len(manifest.failed) > 0
    assert all(item.reason for item in manifest.failed)
    assert any(item.attempts >= 1 for item in manifest.failed)


def test_poison_task_fails_after_three_attempts(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-FT-04: task yang selalu gagal menjadi FAILED setelah tiga percobaan."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 1, repeat=1))
    wait_until_ready(free_port, master)
    worker = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "toxic",
        "--procs",
        "1",
        "--task-fail-rate",
        "1.0",
        "--seed",
        "1",
    )

    code = master.wait(timeout=120)
    assert code != 0
    assert worker.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["tasks_ok"] == 0
    assert metrics["tasks_failed"] == metrics["tasks"]

    manifest = read_manifest(out_dir / "manifest.json")
    assert len(manifest.failed) == metrics["tasks"]
    assert all(item.attempts == 3 for item in manifest.failed)
    assert all(item.reason for item in manifest.failed)

    events = events_of(out_dir)
    names = [item["event"] for item in events]
    assert names.count("task_failed") == metrics["tasks"]
    assert names.count("task_requeued") == metrics["tasks"] * 2

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr


def test_worker_rejoins_with_same_id(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-FT-05: Worker baru dengan `worker_id` sama diterima dan meneruskan task."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 1))
    wait_until_ready(free_port, master)
    first = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "1",
        "--throttle",
        "0.5",
        "--fail-after-sec",
        "0.6",
    )
    wait_for_event(out_dir, "worker_dead")
    assert first.wait(timeout=30) != 0

    replacement = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "2",
        "--throttle",
        "0.1",
    )

    assert master.wait(timeout=120) == 0
    assert replacement.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0

    events = events_of(out_dir)
    names = [item["event"] for item in events]
    assert "worker_rejoined" in names

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout


def test_recovery_events_have_timestamps(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-FT-06: events pemulihan memuat timestamp yang dapat dipakai menghitung Recovery Time."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 2))
    wait_until_ready(free_port, master)

    dying = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "1",
        "--throttle",
        "1.2",
        "--fail-after-sec",
        "1.0",
    )
    survivor = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w2",
        "--procs",
        "2",
        "--throttle",
        "0.2",
    )

    assert master.wait(timeout=120) == 0
    assert dying.wait(timeout=30) != 0
    assert survivor.wait(timeout=30) == 0

    events = events_of(out_dir)
    dead = [item for item in events if item["event"] == "worker_dead"]
    requeued = [item for item in events if item["event"] == "task_requeued"]
    assert dead and requeued
    assert all(isinstance(item["ts"], float) for item in dead + requeued)

    for item in requeued:
        later = [
            done
            for done in events
            if done["event"] == "task_done"
            and done["task_id"] == item["task_id"]
            and done["ts"] >= item["ts"]
        ]
        assert later, f"task {item['task_id']} tidak selesai setelah requeue"


def test_worker_exits_when_master_is_lost(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-FT-07: Worker mendeteksi Master hilang lalu keluar dengan pesan jelas."""
    out_dir = tmp_path / "out"
    master = start_master(*master_args(synth_dataset, out_dir, free_port, 1))
    wait_until_ready(free_port, master)
    worker = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "1",
        "--throttle",
        "1.0",
    )
    wait_for_event(out_dir, "worker_registered")

    master.terminate()
    master.wait(timeout=20)

    code = worker.wait(timeout=40)
    out, err = worker.communicate(timeout=10)
    assert code != 0
    assert "MASTER HILANG" in (out + err)
