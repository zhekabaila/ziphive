"""IT-LAN-01: harness `--lan` dengan Worker proses terpisah di localhost (PLAN.md P11-T4)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.timeout(240)
def test_runner_lan_menunggu_worker_eksternal(
    tmp_path: Path,
    repo_root: Path,
    synth_dataset: Path,
    free_port: int,
    start_worker: Callable[..., subprocess.Popen[str]],
) -> None:
    """Runner mode `--lan` menunggu dua Worker mendaftar lalu menyelesaikan run E6."""
    out_root = tmp_path / "raw"
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    env["PYTHONUNBUFFERED"] = "1"
    command = [
        sys.executable,
        "-u",
        "-m",
        "pcomp.bench.runner",
        "--exp",
        "E6",
        "--lan",
        "--host",
        "127.0.0.1",
        "--port",
        str(free_port),
        "--workers",
        "2",
        "--reps",
        "1",
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--input",
        str(synth_dataset),
        "--out-root",
        str(out_root),
        "--no-report",
        "--lan-wait",
        "90",
        "--barrier-timeout",
        "30",
        "--timeout",
        "120",
    ]
    runner = subprocess.Popen(
        command,
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    workers = [
        start_worker(
            "--master",
            f"127.0.0.1:{free_port}",
            "--id",
            f"w{index}",
            "--procs",
            "1",
        )
        for index in (1, 2)
    ]
    try:
        output, _ = runner.communicate(timeout=200)
    finally:
        if runner.poll() is None:
            runner.kill()
            runner.communicate(timeout=30)

    assert runner.returncode == 0, output
    assert "LAN: 2 Worker terdaftar" in output
    assert "BENCH OK" in output

    run_dirs = [path for path in (out_root / "E6").iterdir() if (path / "metrics.json").is_file()]
    assert len(run_dirs) == 1
    metrics = json.loads((run_dirs[0] / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["workers"] == 2
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert metrics["tasks_failed"] == 0

    for worker in workers:
        assert worker.wait(timeout=60) == 0
