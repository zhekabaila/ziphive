"""IT-FULL-01: Master menolak Worker di luar kuota run (PLAN.md P11-T2)."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path

import pytest

from pcomp.metrics.events import read_events

pytestmark = pytest.mark.integration


def wait_for_event(out_dir: Path, name: str, timeout: float = 30.0) -> dict:
    """Tunggu satu event muncul di `events.jsonl`."""
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


def test_worker_berlebih_ditolak_server_full(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., object],
    start_worker: Callable[..., object],
    free_port: int,
) -> None:
    """Worker kedua pada `--expect-workers 1` menerima SERVER_FULL dan tidak ikut run."""
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
        "--repeat",
        "8",
        "--scheduler",
        "dynamic",
        "--heartbeat-interval",
        "0.2",
        "--heartbeat-timeout",
        "3",
        "--barrier-timeout",
        "20",
    )
    busy = start_worker(
        "--master",
        f"127.0.0.1:{free_port}",
        "--id",
        "w1",
        "--procs",
        "1",
        "--throttle",
        "0.2",
    )
    wait_for_event(out_dir, "worker_registered")

    extra = start_worker("--master", f"127.0.0.1:{free_port}", "--id", "w2", "--procs", "1")
    extra_out, extra_err = extra.communicate(timeout=60)
    assert extra.returncode != 0
    assert "SERVER_FULL" in (extra_err + extra_out)

    assert busy.wait(timeout=120) == 0
    assert master.wait(timeout=120) == 0

    ids = [row.get("worker_id") for row in read_events(out_dir / "events.jsonl")]
    assert ids.count("w2") == 0
    assert ids.count("w1") >= 1
