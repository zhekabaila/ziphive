"""SL-9W-01: 9 Worker lokal pada satu mesin (PLAN.md P8-T6, marker `slow`)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = [pytest.mark.slow, pytest.mark.timeout(600)]


def test_nine_workers_local(repo_root: Path, tmp_path: Path) -> None:
    """SL-9W-01: Master + 9 Worker menyelesaikan semua task dan `VERIFY OK`."""
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    out_dir = tmp_path / "out"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/e2e_local.py",
            "--workers",
            "9",
            "--algo",
            "sim",
            "--size-mb",
            "2",
            "--chunk-mb",
            "1",
            "--worker-procs",
            "1",
            "--out",
            str(out_dir),
            "--timeout",
            "480",
        ],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=540,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "VERIFY OK" in completed.stdout
    assert "E2E OK" in completed.stdout

    metrics = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["workers"] == 9
    assert metrics["tasks_ok"] == metrics["tasks"]
    assert len(metrics["worker_stats"]) == 9
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "events.jsonl").is_file()
