"""UT-MCLI-01..04: CLI Master (PLAN.md P4-T1)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp import constants
from pcomp.config import MasterConfig
from pcomp.master import cli
from pcomp.master.cli import build_parser, main


class FakeServer:
    """Pengganti MasterServer agar CLI diuji tanpa jaringan."""

    last_scheduler: str | None = None

    def __init__(self, config: MasterConfig, *, barrier_timeout: float) -> None:
        self.config = config
        self.barrier_timeout = barrier_timeout
        self.last_error = None
        self.metrics: dict = {}
        FakeServer.last_scheduler = config.scheduler

    def run(self) -> int:
        return constants.EXIT_OK


def test_parser_defaults() -> None:
    """UT-MCLI-01: default CLI Master memakai nilai constants."""
    args = build_parser().parse_args([])

    assert args.host is None
    assert args.port is None
    assert args.barrier_timeout == constants.DEFAULT_BARRIER_TIMEOUT
    assert Path(args.config) == constants.DEFAULT_MASTER_CONFIG


def test_static_scheduler_accepted(
    monkeypatch: pytest.MonkeyPatch, valid_group_file: Path, tmp_path: Path
) -> None:
    """UT-MCLI-02: opsi --scheduler static diteruskan ke MasterServer (PLAN.md P5-T4)."""
    monkeypatch.setattr(cli, "MasterServer", FakeServer)

    code = main(
        [
            "--group-config",
            str(valid_group_file),
            "--scheduler",
            "static",
            "--out",
            str(tmp_path / "out"),
        ]
    )

    assert code == constants.EXIT_OK
    assert FakeServer.last_scheduler == "static"


def test_missing_config_reports_error(valid_group_file: Path, tmp_path: Path) -> None:
    """UT-MCLI-03: file konfigurasi tidak ada menghasilkan pesan galat, bukan traceback."""
    code = main(
        ["--group-config", str(valid_group_file), "--config", str(tmp_path / "tidak-ada.toml")]
    )

    assert code == constants.EXIT_ERROR


def test_missing_input_dir_reports_error(valid_group_file: Path, tmp_path: Path) -> None:
    """UT-MCLI-04: folder input tidak ada ditolak dengan pesan MASTER GAGAL."""
    code = main(
        [
            "--group-config",
            str(valid_group_file),
            "--input",
            str(tmp_path / "input-tidak-ada"),
            "--out",
            str(tmp_path / "out"),
        ]
    )

    assert code == constants.EXIT_ERROR
