"""UT-WCLI-01..03: CLI Worker (PLAN.md P4-T3)."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp import constants
from pcomp.worker import cli
from pcomp.worker.cli import build_parser, main


def test_parser_defaults() -> None:
    """UT-WCLI-01: default CLI Worker memakai versi protokol lokal."""
    args = build_parser().parse_args([])

    assert args.master is None
    assert args.worker_id is None
    assert args.protocol_version == constants.PROTOCOL_VERSION


def test_missing_config_reports_error(valid_group_file: Path, tmp_path: Path) -> None:
    """UT-WCLI-02: konfigurasi tidak ditemukan menghasilkan kode galat."""
    code = main(
        ["--group-config", str(valid_group_file), "--config", str(tmp_path / "tidak-ada.toml")]
    )

    assert code == constants.EXIT_ERROR


class FakeClient:
    """Pengganti WorkerClient agar CLI diuji tanpa jaringan."""

    def __init__(self, code: int) -> None:
        self.code = code
        self.config = None

    def run(self) -> int:
        return self.code


@pytest.mark.parametrize(
    ("code", "expected"),
    [(constants.EXIT_OK, constants.EXIT_OK), (constants.EXIT_ERROR, constants.EXIT_ERROR)],
)
def test_main_reports_client_code(
    monkeypatch: pytest.MonkeyPatch,
    valid_group_file: Path,
    tmp_path: Path,
    code: int,
    expected: int,
) -> None:
    """UT-WCLI-03: exit code CLI mengikuti hasil WorkerClient.run."""
    fake = FakeClient(code)
    monkeypatch.setattr(cli, "WorkerClient", lambda *args, **kwargs: fake)

    result = main(
        [
            "--group-config",
            str(valid_group_file),
            "--master",
            "127.0.0.1:5050",
            "--id",
            "uji",
            "--procs",
            "1",
        ]
    )

    assert result == expected


def test_failure_options_forwarded(
    monkeypatch: pytest.MonkeyPatch, valid_group_file: Path, tmp_path: Path
) -> None:
    """UT-WCLI-04: opsi injeksi kegagalan diteruskan ke WorkerConfig (PLAN.md P6-T5)."""
    captured: dict[str, object] = {}

    class CaptureClient:
        def __init__(self, config: object, **kwargs: object) -> None:
            captured["config"] = config

        def run(self) -> int:
            return constants.EXIT_OK

    monkeypatch.setattr(cli, "WorkerClient", CaptureClient)

    code = main(
        [
            "--group-config",
            str(valid_group_file),
            "--master",
            "127.0.0.1:5050",
            "--id",
            "uji",
            "--fail-after-tasks",
            "2",
            "--fail-after-sec",
            "1.5",
            "--task-fail-rate",
            "0.25",
            "--seed",
            "7",
        ]
    )

    assert code == constants.EXIT_OK
    config = captured["config"]
    assert config.fail_after_tasks == 2
    assert config.fail_after_sec == 1.5
    assert config.task_fail_rate == 0.25
    assert config.seed == 7
