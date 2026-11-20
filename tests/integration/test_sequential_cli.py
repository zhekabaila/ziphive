"""IT-SEQ-01: make_dataset lalu sequential lalu verify pada dataset sintetis kecil."""

from __future__ import annotations

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
        timeout=120,
        check=False,
    )


@pytest.mark.integration
def test_sequential_then_verify(repo_root: Path, tmp_path: Path) -> None:
    dataset = tmp_path / "synth"
    out_dir = tmp_path / "out"

    made = run_module(
        repo_root, "pcomp.tools.make_dataset", "--out", str(dataset), "--size-mb", "2"
    )
    assert made.returncode == 0, made.stderr
    assert (dataset / "dataset.json").is_file()

    sequential = run_module(
        repo_root,
        "pcomp.sequential",
        "--input",
        str(dataset),
        "--out",
        str(out_dir),
        "--algo",
        "gzip",
        "--level",
        "1",
        "--chunk-mb",
        "1",
    )
    assert sequential.returncode == 0, sequential.stderr
    assert (out_dir / "manifest.json").is_file()
    assert (out_dir / "metrics.json").is_file()

    verified = run_module(
        repo_root, "pcomp.tools.verify", "--manifest", str(out_dir / "manifest.json")
    )
    assert verified.returncode == 0, verified.stderr
    assert "VERIFY OK" in verified.stdout
