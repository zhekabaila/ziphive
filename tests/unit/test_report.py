"""UT-RPT-01..02: agregasi dan grafik laporan benchmark (PLAN.md P7-T4)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pcomp.bench.report import aggregate, plot_all, write_aggregate_csv


def make_row(workers: int, rep: int, time_s: float, throughput_mbs: float) -> dict:
    return {
        "exp": "E6",
        "run_id": f"E6-w{workers}-r{rep}",
        "rep": rep,
        "mode": "distributed",
        "workers": workers,
        "procs": 1,
        "scheduler": "dynamic",
        "algo": "sim",
        "level": 1,
        "chunk_mb": 1,
        "repeat": 1,
        "total_mb": 4.0,
        "tasks": 4,
        "time_s": time_s,
        "throughput_mbs": throughput_mbs,
        "ratio": 1.0,
        "speedup_seq": 2.0,
        "speedup_rel": 1.0,
        "efficiency": 1.0,
        "imbalance": 1.0,
        "cpu_avg_master": 5.0,
        "cpu_avg_workers": 40.0,
        "mem_avg_master": 2.0,
        "mem_avg_workers": 3.0,
        "detect_s": None,
        "recovery_s": None,
        "retried_tasks": 0,
        "verify_ok": True,
        "started_at": "2026-11-21T00:00:00+00:00",
    }


def test_aggregate_mean_and_std() -> None:
    """UT-RPT-01: rata-rata dan simpangan baku per kelompok konfigurasi."""
    rows = [
        make_row(1, 1, 2.0, 2.0),
        make_row(1, 2, 4.0, 1.0),
        make_row(2, 1, 1.0, 4.0),
    ]
    summary = aggregate(rows, keys=("exp", "workers", "procs", "scheduler"))
    assert len(summary) == 2
    first = next(item for item in summary if item["workers"] == 1)
    assert first["reps"] == 2
    assert first["time_s_mean"] == pytest.approx(3.0)
    assert first["time_s_std"] == pytest.approx(1.414213562, rel=1e-6)
    assert first["throughput_mbs_mean"] == pytest.approx(1.5)

    path = Path("unused.csv")
    assert callable(write_aggregate_csv)
    assert path.name == "unused.csv"


def test_plot_all_creates_png_files(tmp_path: Path) -> None:
    """UT-RPT-02: laporan membuat grafik PNG dengan backend Agg."""
    rows = [make_row(1, 1, 2.0, 2.0), make_row(2, 1, 1.0, 4.0)]

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "worker_stats": [
                    {"worker_id": "w1", "tasks_done": 3, "busy_sec": 1.5},
                    {"worker_id": "w2", "tasks_done": 1, "busy_sec": 0.5},
                ]
            }
        ),
        encoding="utf-8",
    )
    events = [
        {"ts": 10.0, "event": "worker_exit_injected", "worker_id": "w1"},
        {"ts": 10.5, "event": "worker_dead", "worker_id": "w1"},
        {"ts": 10.6, "event": "task_requeued", "task_id": 1, "worker_id": "w1"},
        {"ts": 12.0, "event": "task_done", "task_id": 1, "worker_id": "w2"},
        {"ts": 12.1, "event": "task_done", "task_id": 2, "worker_id": "w2"},
    ]
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8"
    )

    out_dir = tmp_path / "figures"
    paths = plot_all(rows, run_dirs=[run_dir], out_dir=out_dir)

    names = {path.name for path in paths}
    assert {
        "time_vs_workers.png",
        "speedup.png",
        "efficiency.png",
        "throughput.png",
        "cpu_mem.png",
        "worker_load.png",
        "recovery_timeline.png",
    } <= names
    for path in paths:
        assert path.is_file()
        assert path.stat().st_size > 0
