"""IT-BENCH-01: runner localhost dengan `sim`, 1 dan 2 Worker, 2 ulangan."""

from __future__ import annotations

import csv
import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcomp.bench.runner import SUMMARY_COLUMNS

pytestmark = pytest.mark.integration


def test_bench_runner_local_sim(tmp_path: Path, repo_root: Path) -> None:
    """IT-BENCH-01: summary.csv dan grafik PNG terbentuk dari run localhost."""
    out_root = tmp_path / "results"
    data_root = tmp_path / "data"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pcomp.bench.runner",
            "--exp",
            "E6",
            "--local",
            "--workers",
            "1,2",
            "--reps",
            "2",
            "--algo",
            "sim",
            "--level",
            "1",
            "--size-mb",
            "2",
            "--chunk-mb",
            "1",
            "--out-root",
            str(out_root),
            "--data-root",
            str(data_root),
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "BENCH OK" in completed.stdout

    summary = out_root / "summary.csv"
    assert summary.is_file()
    with summary.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert list(rows[0].keys()) == list(SUMMARY_COLUMNS)
    assert len(rows) == 4
    assert {row["workers"] for row in rows} == {"1", "2"}
    assert {row["mode"] for row in rows} == {"distributed"}
    assert all(row["algo"] == "sim" for row in rows)
    assert all(row["verify_ok"] == "True" for row in rows)

    figures = sorted((out_root / "figures").glob("*.png"))
    names = {path.name for path in figures}
    assert {"time_vs_workers.png", "speedup.png", "throughput.png"} <= names
    assert all(path.stat().st_size > 0 for path in figures)

    run_dirs = sorted((out_root / "E6").iterdir())
    assert len(run_dirs) == 4
    for run_dir in run_dirs:
        assert (run_dir / "env.json").is_file()
        metrics = (run_dir / "metrics.json").read_text(encoding="utf-8")
        assert '"simulated": true' in metrics
