"""IT-DIST-01..05: Master-Worker inti di localhost (PLAN.md Fase 4)."""

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


def read_metrics(out_dir: Path) -> dict:
    return json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("worker_count", [2, 3], ids=["IT-DIST-01", "IT-DIST-02"])
def test_workers_complete_all_tasks(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
    worker_count: int,
) -> None:
    out_dir = tmp_path / "out"
    master = start_master(
        "--input",
        str(synth_dataset),
        "--out",
        str(out_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--expect-workers",
        str(worker_count),
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--barrier-timeout",
        "15",
    )
    wait_until_ready(free_port, master)

    workers = [
        start_worker("--master", f"127.0.0.1:{free_port}", "--id", f"w{index}", "--procs", "2")
        for index in range(1, worker_count + 1)
    ]

    assert master.wait(timeout=120) == 0
    for worker in workers:
        assert worker.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["mode"] == "distributed"
    assert metrics["workers"] == worker_count
    assert metrics["tasks"] > 0
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0
    assert metrics["ratio"] > 1

    manifest = read_manifest(out_dir / "manifest.json")
    assert len(manifest.entries) == metrics["tasks"]
    assert all(item.ok for item in verify_entries(manifest, out_dir))

    events = events_of(out_dir)
    registered = {item["worker_id"] for item in events if item["event"] == "worker_registered"}
    assert registered == {f"w{index}" for index in range(1, worker_count + 1)}
    assert any(item["event"] == "run_finished" for item in events)
    assert {item["task_id"] for item in events if item["event"] == "task_done"} == {
        entry.task_id for entry in manifest.entries
    }

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout


def test_worker_with_procs_two(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-DIST-03: satu Worker dengan `--procs 2` menyelesaikan seluruh task."""
    out_dir = tmp_path / "out"
    master = start_master(
        "--input",
        str(synth_dataset),
        "--out",
        str(out_dir),
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--expect-workers",
        "1",
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--barrier-timeout",
        "15",
    )
    wait_until_ready(free_port, master)
    worker = start_worker("--master", f"127.0.0.1:{free_port}", "--id", "solo", "--procs", "2")

    assert master.wait(timeout=120) == 0
    assert worker.wait(timeout=30) == 0

    metrics = read_metrics(out_dir)
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["worker_stats"][0]["procs"] == 2
    assert metrics["worker_stats"][0]["worker_id"] == "solo"

    verified = run_verify(repo_root, out_dir / "manifest.json")
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout


def test_master_without_worker_exits_cleanly(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-DIST-04: tanpa Worker, Master berhenti rapi dengan pesan jelas."""
    master = start_master(
        "--input",
        str(synth_dataset),
        "--out",
        str(tmp_path / "out"),
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--expect-workers",
        "2",
        "--barrier-timeout",
        "1",
    )

    code = master.wait(timeout=60)
    out, err = master.communicate(timeout=10)
    assert code != 0
    assert "tidak ada Worker" in (out + err)
    assert not (tmp_path / "out" / "manifest.json").exists()


def test_worker_version_mismatch_rejected(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., subprocess.Popen[str]],
    start_worker: Callable[..., subprocess.Popen[str]],
    free_port: int,
) -> None:
    """IT-DIST-05: versi protokol berbeda ditolak Master."""
    master = start_master(
        "--input",
        str(synth_dataset),
        "--out",
        str(tmp_path / "out"),
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--expect-workers",
        "1",
        "--barrier-timeout",
        "5",
    )
    wait_until_ready(free_port, master)
    worker = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "beda",
        "--procs",
        "1",
        "--protocol-version",
        "99",
    )

    worker_code = worker.wait(timeout=60)
    worker_out, worker_err = worker.communicate(timeout=10)
    assert worker_code != 0
    assert "VERSION_MISMATCH" in (worker_out + worker_err)

    master_code = master.wait(timeout=60)
    master_out, master_err = master.communicate(timeout=10)
    assert master_code != 0
    assert "tidak ada Worker" in (master_out + master_err)
