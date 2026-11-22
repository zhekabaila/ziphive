"""IT-KILL-01..02: injeksi KILL dari Master untuk E5 pada node fisik (PLAN.md P11-T2, P11-T3)."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path

import pytest

from pcomp import constants
from pcomp.metrics import calc
from pcomp.metrics.events import read_events

pytestmark = pytest.mark.integration


def master_args(
    input_dir: Path,
    out_dir: Path,
    port: int,
    workers: int,
    *,
    inject_kills: int,
    fraction: float,
) -> list[str]:
    """Argumen Master dengan injeksi KILL aktif."""
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
        "3",
        "--scheduler",
        "dynamic",
        "--heartbeat-interval",
        "0.2",
        "--heartbeat-timeout",
        "3",
        "--barrier-timeout",
        "20",
        "--inject-kills",
        str(inject_kills),
        "--inject-kill-fraction",
        str(fraction),
    ]


def worker_args(port: int, worker_id: str) -> list[str]:
    """Argumen Worker dengan jeda kecil agar run tidak selesai sebelum kill."""
    return [
        "--master",
        f"127.0.0.1:{port}",
        "--id",
        worker_id,
        "--procs",
        "1",
        "--throttle",
        "0.05",
    ]


def test_kill_membuat_metrik_e5_terukur(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., object],
    start_worker: Callable[..., object],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-KILL-01: Worker yang menerima KILL mati tanpa BYE dan metrik E5 terisi."""
    out_dir = tmp_path / "out"
    master = start_master(
        *master_args(synth_dataset, out_dir, free_port, 2, inject_kills=1, fraction=0.2)
    )
    workers = [start_worker(*worker_args(free_port, f"w{index}")) for index in (1, 2)]

    assert master.wait(timeout=120) == 0
    codes = [worker.wait(timeout=30) for worker in workers]
    assert constants.EXIT_KILLED in codes
    assert codes.count(constants.EXIT_OK) == 1

    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0

    events = events_of(out_dir)
    names = [row["event"] for row in events]
    assert names.count("worker_exit_injected") == 1
    assert "worker_dead" in names
    assert "task_requeued" in names

    injected = next(row for row in events if row["event"] == "worker_exit_injected")
    assert injected["worker_id"] == "w1"
    assert injected["reason"] == "master-kill"

    dead = next(row for row in events if row["event"] == "worker_dead")
    assert dead["ts"] > injected["ts"]

    detect = calc.detection_latency(events, float(injected["ts"]))
    assert detect is not None and detect >= 0.0
    stats = calc.recovery_stats(events)
    assert stats.detect_s is not None
    assert stats.retried_tasks >= 1


def test_kill_dua_worker_sekaligus(
    tmp_path: Path,
    synth_dataset: Path,
    start_master: Callable[..., object],
    start_worker: Callable[..., object],
    events_of: Callable[[Path], list[dict]],
    free_port: int,
) -> None:
    """IT-KILL-02: dua Worker dimatikan bersamaan; sisa Worker tetap menyelesaikan run."""
    out_dir = tmp_path / "out"
    master = start_master(
        *master_args(synth_dataset, out_dir, free_port, 3, inject_kills=2, fraction=0.2)
    )
    workers = [start_worker(*worker_args(free_port, f"w{index}")) for index in (1, 2, 3)]

    assert master.wait(timeout=120) == 0
    codes = [worker.wait(timeout=30) for worker in workers]
    assert codes.count(constants.EXIT_KILLED) == 2
    assert codes.count(constants.EXIT_OK) == 1

    events = read_events(out_dir / "events.jsonl")
    injected = [row["worker_id"] for row in events if row["event"] == "worker_exit_injected"]
    assert sorted(injected) == ["w1", "w2"]

    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0
