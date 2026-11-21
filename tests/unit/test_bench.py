"""UT-BEN-01..07: matriks eksperimen dan baris summary (PLAN.md P7-T3, P7-T5)."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import pytest

from pcomp.bench import runner as bench
from pcomp.bench.runner import (
    SUMMARY_COLUMNS,
    RunSpec,
    append_summary,
    build_row,
    collect_env,
    figures_dir,
    plan_runs,
    results_root,
    summary_path,
    write_env,
)

EXPECTED_COLUMNS = (
    "exp,run_id,rep,mode,workers,procs,scheduler,algo,level,chunk_mb,repeat,total_mb,tasks,"
    "time_s,throughput_mbs,ratio,speedup_seq,speedup_rel,efficiency,imbalance,cpu_avg_master,"
    "cpu_avg_workers,mem_avg_master,mem_avg_workers,detect_s,recovery_s,retried_tasks,"
    "verify_ok,started_at"
)


def test_plan_runs_for_each_experiment() -> None:
    """UT-BEN-01: matriks E1, E2, E4, E6 dibentuk sesuai EXPERIMENTS.md bagian 2."""
    assert plan_runs("E1", workers=[1, 2], procs=[1, 2], reps=2) == [
        RunSpec(exp="E1", mode="sequential", workers=0, procs=1, scheduler="none")
    ]

    local = plan_runs("E2", workers=[1, 2], procs=[1, 2, 4], reps=2)
    assert [(item.mode, item.procs) for item in local] == [
        ("local", 1),
        ("local", 2),
        ("local", 4),
    ]

    balance = plan_runs("E4", workers=[2, 4], procs=[1], reps=1, throttle=0.3)
    assert [(item.scheduler, item.workers, item.throttle) for item in balance] == [
        ("static", 4, 0.3),
        ("dynamic", 4, 0.3),
    ]

    scaling = plan_runs("E6", workers=[1, 2, 4], procs=[1], reps=1)
    assert [item.workers for item in scaling] == [1, 2, 4]
    assert all(item.mode == "distributed" for item in scaling)

    with pytest.raises(ValueError):
        plan_runs("E9", workers=[1], procs=[1], reps=1)


def test_results_paths_and_columns() -> None:
    """UT-BEN-02: hasil sim ke results/dev, hasil nyata ke results/raw dan results/summary.csv."""
    assert results_root("sim") == Path("results/dev")
    assert results_root("gzip") == Path("results/raw")
    assert summary_path("sim") == Path("results/dev/summary.csv")
    assert summary_path("gzip") == Path("results/summary.csv")
    assert figures_dir("sim") == Path("results/dev/figures")
    assert figures_dir("gzip") == Path("results/figures")
    assert summary_path("sim", Path("tmp/out")) == Path("tmp/out/summary.csv")
    assert ",".join(SUMMARY_COLUMNS) == EXPECTED_COLUMNS


def test_build_row_derives_metrics() -> None:
    """UT-BEN-03: baris summary menurunkan throughput, efficiency, dan kolom kosong."""
    metrics = {
        "mode": "distributed",
        "tasks": 8,
        "total_mb": 8.0,
        "time_s": 4.0,
        "ratio": 2.5,
        "imbalance": 1.5,
        "started_at": "2026-11-21T00:00:00+00:00",
    }
    row = build_row(
        metrics,
        exp="E6",
        run_id="E6-w2-r1",
        rep=1,
        mode="distributed",
        workers=2,
        procs=1,
        scheduler="dynamic",
        speedup_seq=2.0,
        speedup_rel=1.25,
        detect_s=None,
        recovery_s=None,
        retried_tasks=0,
        verify_ok=True,
        cpu_avg_master=5.0,
        cpu_avg_workers=55.0,
        mem_avg_master=2.0,
        mem_avg_workers=3.0,
    )
    assert tuple(row) == SUMMARY_COLUMNS
    assert row["throughput_mbs"] == pytest.approx(2.0)
    assert row["efficiency"] == pytest.approx(1.0)
    assert row["imbalance"] == pytest.approx(1.5)
    assert row["detect_s"] is None
    assert row["verify_ok"] is True
    assert row["total_mb"] == pytest.approx(8.0)
    assert row["time_s"] == pytest.approx(4.0)


def test_build_row_local_uses_procs_as_unit() -> None:
    """UT-BEN-03b: pada mode local, efficiency dibagi jumlah proses."""
    metrics = {"mode": "local", "tasks": 4, "total_mb": 4.0, "time_s": 2.0, "ratio": 1.0}
    row = build_row(
        metrics,
        exp="E2",
        run_id="E2-p4-r1",
        rep=1,
        mode="local",
        workers=0,
        procs=4,
        scheduler="none",
        speedup_seq=2.0,
        imbalance=1.0,
        verify_ok=True,
    )
    assert row["efficiency"] == pytest.approx(0.5)
    assert row["speedup_rel"] is None
    assert row["detect_s"] is None


def test_collect_env_and_write_env(tmp_path: Path) -> None:
    """UT-BEN-04: metadata lingkungan memuat CPU, OS, Python, core, dan tanggal."""
    env = collect_env()
    for key in ("hostname", "platform", "python_version", "cpu", "logical_cores", "ram_gb", "date"):
        assert key in env
    assert env["logical_cores"] >= 1
    assert env["ram_gb"] > 0

    run_dir = tmp_path / "run"
    run_dir.mkdir()
    path = write_env(run_dir, env)
    assert path == run_dir / "env.json"
    assert json.loads(path.read_text(encoding="utf-8"))["python_version"] == env["python_version"]


def test_summary_csv_written_with_columns(tmp_path: Path) -> None:
    """UT-BEN-04b: penulisan summary memakai kolom persis EXPERIMENTS.md bagian 4."""
    path = tmp_path / "summary.csv"
    metrics = {"tasks": 1, "total_mb": 1.0, "time_s": 1.0, "ratio": 1.0}
    row = build_row(
        metrics,
        exp="E1",
        run_id="r1",
        rep=1,
        mode="sequential",
        workers=0,
        procs=1,
        scheduler="none",
        speedup_seq=1.0,
        verify_ok=True,
    )
    append_summary(path, [row])
    append_summary(path, [row])

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0] == list(SUMMARY_COLUMNS)
    assert len(rows) == 3
    assert rows[1][0] == "E1"


def make_args(**overrides: object) -> argparse.Namespace:
    """Argumen CLI runner dengan nilai default untuk unit test."""
    base = vars(bench.build_parser().parse_args(["--exp", "E6", "--local"]))
    base.update(overrides)
    return argparse.Namespace(**base)


def test_parse_list_and_argument_composition(tmp_path: Path) -> None:
    """UT-BEN-05: parsing daftar angka dan penyusunan argumen Master serta Worker."""
    assert bench._parse_list("1, 2 ,4") == [1, 2, 4]
    with pytest.raises(ValueError):
        bench._parse_list(" , ")

    args = make_args(host="127.0.0.1", algo="sim", level=1, chunk_mb=1)
    args.input_dir = tmp_path
    run_dir = tmp_path / "run"
    spec = RunSpec(
        exp="E4", mode="distributed", workers=3, procs=1, scheduler="static", throttle=0.5
    )

    master = bench._master_args(args, spec, run_dir, 5150)
    assert "--port" in master and master[master.index("--port") + 1] == "5150"
    assert master[master.index("--expect-workers") + 1] == "3"
    assert master[master.index("--scheduler") + 1] == "static"

    slowest = bench._worker_args(args, spec, 5150, 3)
    assert slowest[slowest.index("--id") + 1] == "w3"
    assert slowest[slowest.index("--throttle") + 1] == "0.5"
    fast = bench._worker_args(args, spec, 5150, 1)
    assert "--throttle" not in fast


def test_helpers_for_metrics_events_and_dataset(tmp_path: Path) -> None:
    """UT-BEN-06: pembacaan metrics, rekap events, speedup relatif, dan dataset sintetis."""
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    with pytest.raises(RuntimeError):
        bench._read_metrics(run_dir)

    (run_dir / "metrics.json").write_text(json.dumps({"time_s": 2.0}), encoding="utf-8")
    assert bench._read_metrics(run_dir) == {"time_s": 2.0}

    assert bench._event_stats(run_dir).retried_tasks == 0
    events = [
        {"ts": 5.0, "event": "worker_exit_injected", "worker_id": "w1"},
        {"ts": 5.2, "event": "worker_dead", "worker_id": "w1"},
        {"ts": 5.3, "event": "task_requeued", "task_id": 4, "worker_id": "w1"},
        {"ts": 7.0, "event": "task_done", "task_id": 4, "worker_id": "w2"},
    ]
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(item) for item in events) + "\n", encoding="utf-8"
    )
    stats = bench._event_stats(run_dir)
    assert stats.detect_s == pytest.approx(0.2)
    assert stats.recovery_s == pytest.approx(2.0)
    assert stats.retried_tasks == 1

    rows = [
        {"exp": "E6", "workers": 1, "time_s": 4.0, "speedup_rel": None},
        {"exp": "E6", "workers": 2, "time_s": 2.0, "speedup_rel": None},
        {"exp": "E6", "workers": 2, "time_s": 0.0, "speedup_rel": None},
    ]
    bench.fill_speedup_rel(rows)
    assert rows[1]["speedup_rel"] == pytest.approx(2.0)
    assert rows[0]["speedup_rel"] is None
    assert rows[2]["speedup_rel"] is None

    data_root = tmp_path / "data"
    args = make_args(data_root=str(data_root), size_mb=1, files=2)
    assert bench._prepare_dataset(args) == data_root
    assert len(list(data_root.glob("*"))) >= 2

    args.input = str(run_dir)
    assert bench._prepare_dataset(args) == run_dir


def test_main_sequential_end_to_end(
    tmp_path: Path, repo_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-BEN-07: `main` mode sequential menulis summary, env, dan grafik di folder keluaran."""
    out_root = tmp_path / "out"
    code = bench.main(
        [
            "--exp",
            "E1",
            "--local",
            "--algo",
            "sim",
            "--level",
            "1",
            "--size-mb",
            "1",
            "--files",
            "2",
            "--chunk-mb",
            "1",
            "--reps",
            "1",
            "--data-root",
            str(tmp_path / "data"),
            "--out-root",
            str(out_root),
            "--group-config",
            str(repo_root / "config" / "group.toml"),
        ]
    )
    assert code == 0
    output = capsys.readouterr().out
    assert "BENCH OK" in output

    with (out_root / "summary.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["exp"] == "E1"
    assert rows[0]["mode"] == "sequential"
    assert rows[0]["speedup_seq"] == "1.0"
    assert rows[0]["verify_ok"] == "True"

    run_dirs = sorted((out_root / "E1").iterdir())
    assert len(run_dirs) == 1
    assert (run_dirs[0] / "env.json").is_file()
    assert (run_dirs[0] / "spec.json").is_file()
    assert (run_dirs[0] / "system.csv").is_file()
    assert (out_root / "summary_agg.csv").is_file()
    assert (out_root / "figures" / "time_vs_workers.png").is_file()
