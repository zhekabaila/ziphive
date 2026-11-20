"""UT-MCLI-01..04: CLI Master (PLAN.md P4-T1)."""

from __future__ import annotations

from pathlib import Path

from pcomp import constants
from pcomp.master.cli import build_parser, main


def test_parser_defaults() -> None:
    """UT-MCLI-01: default CLI Master memakai nilai constants."""
    args = build_parser().parse_args([])

    assert args.host is None
    assert args.port is None
    assert args.barrier_timeout == constants.DEFAULT_BARRIER_TIMEOUT
    assert Path(args.config) == constants.DEFAULT_MASTER_CONFIG


def test_static_scheduler_rejected(valid_group_file: Path, tmp_path: Path) -> None:
    """UT-MCLI-02: scheduler static ditolak karena baru tersedia pada Fase 5."""
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

    assert code == constants.EXIT_ERROR


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
