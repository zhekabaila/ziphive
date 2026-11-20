"""IT-LOC-01: sequential dan local parallel menghasilkan manifest ekuivalen."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


def run_module(repo_root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    return subprocess.run(
        [sys.executable, "-m", *args],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )


@pytest.mark.integration
def test_local_parallel_matches_sequential(repo_root: Path, tmp_path: Path) -> None:
    dataset = tmp_path / "synth"
    seq_out = tmp_path / "seq"
    local_out = tmp_path / "local"

    made = run_module(
        repo_root, "pcomp.tools.make_dataset", "--out", str(dataset), "--size-mb", "2"
    )
    assert made.returncode == 0, made.stderr

    sequential = run_module(
        repo_root,
        "pcomp.sequential",
        "--input",
        str(dataset),
        "--out",
        str(seq_out),
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
    )
    assert sequential.returncode == 0, sequential.stderr

    local = run_module(
        repo_root,
        "pcomp.local_parallel",
        "--input",
        str(dataset),
        "--out",
        str(local_out),
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
        "--procs",
        "2",
    )
    assert local.returncode == 0, local.stderr
    assert "LOCAL OK" in local.stdout

    seq_manifest = json.loads((seq_out / "manifest.json").read_text(encoding="utf-8"))
    local_manifest = json.loads((local_out / "manifest.json").read_text(encoding="utf-8"))
    assert local_manifest == seq_manifest

    metrics = json.loads((local_out / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["mode"] == "local"
    assert metrics["procs"] == 2
    assert metrics["tasks_failed"] == 0

    for run_dir in (seq_out, local_out):
        verified = run_module(
            repo_root, "pcomp.tools.verify", "--manifest", str(run_dir / "manifest.json")
        )
        assert verified.returncode == 0, verified.stderr
        assert "VERIFY OK" in verified.stdout
