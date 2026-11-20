"""UT-BOOT-04: CLI `python -m pcomp` mencetak versi dan banner."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp import constants
from pcomp.__main__ import main


def test_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--version"])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert constants.__version__ in captured.out
    assert constants.PROJECT_NAME in captured.out


def test_banner_default(capsys: pytest.CaptureFixture[str], valid_group_file: Path) -> None:
    exit_code = main(["--group-config", str(valid_group_file)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Kelompok Uji" in captured.out


def test_missing_group_config_returns_error(
    capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    exit_code = main(["--group-config", str(tmp_path / "tidak-ada.toml")])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "group.toml" in captured.err
