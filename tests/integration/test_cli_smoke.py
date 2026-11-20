"""IT-BOOT-01: entry point CLI berjalan sebagai proses nyata."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from pcomp import constants


@pytest.mark.integration
def test_module_entry_point_version(repo_root: Path) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(repo_root / "src")
    result = subprocess.run(
        [sys.executable, "-m", "pcomp", "--version"],
        cwd=repo_root,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert constants.__version__ in result.stdout
