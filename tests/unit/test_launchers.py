"""UT-LAUN-01..06: launcher laptop fisik (PLAN.md P11-T6, P11-T7, P11-T8)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

Loader = Callable[[str], ModuleType]


@pytest.fixture
def fake_root(tmp_path: Path) -> Path:
    """Folder proyek tiruan dengan `.venv` siap pakai."""
    python = tmp_path / ".venv" / "bin" / "python"
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    return tmp_path


def test_bootstrap_check_only_mencetak_setup_ok(
    load_script: Loader, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-01: mode periksa tidak mengubah apa pun dan mencetak SETUP OK."""
    module = load_script("bootstrap_node.py")
    code = module.main(["--check-only"])
    out = capsys.readouterr().out
    assert code == 0
    assert "SETUP OK" in out


def test_bootstrap_menolak_python_lama(
    load_script: Loader, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-02: Python di bawah 3.11 ditolak dengan pesan yang jelas."""
    module = load_script("bootstrap_node.py")
    monkeypatch.setattr(module.sys, "version_info", (3, 9, 18, "final", 0))
    code = module.main(["--check-only"])
    captured = capsys.readouterr()
    assert code == 1
    assert "SETUP GAGAL" in captured.err


def test_start_master_print_plan(
    load_script: Loader, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-03: rencana Master memuat perintah untuk setiap laptop Worker."""
    module = load_script("start_master.py")
    code = module.main(
        [
            "--print-plan",
            "--workers",
            "3",
            "--input",
            str(tmp_path / "data"),
            "--root",
            str(tmp_path),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "PLAN OK" in out
    assert "start_worker.py --master" in out
    assert out.count("start_worker.py") == 3
    assert "--id w3" in out


def test_start_master_plan_lines_menyebut_injeksi(load_script: Loader, tmp_path: Path) -> None:
    """UT-LAUN-04: rencana E5 menyebut jumlah Worker yang akan dimatikan."""
    module = load_script("start_master.py")
    args = module.build_parser().parse_args(
        ["--inject-kills", "3", "--inject-kill-fraction", "0.5"]
    )
    lines = module.plan_lines(args, "10.0.0.5")
    assert any("KILL" in line and "3 Worker" in line for line in lines)
    assert any("10.0.0.5:5050" in line for line in lines)


def test_start_worker_print_command(
    load_script: Loader, fake_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-05: perintah Worker dicetak dan pengaturan disimpan."""
    module = load_script("start_worker.py")
    code = module.main(
        [
            "--print-command",
            "--master",
            "10.0.0.5:5050",
            "--id",
            "w4",
            "--root",
            str(fake_root),
        ]
    )
    out = capsys.readouterr().out
    assert code == 0
    assert "-m pcomp.worker" in out
    assert "--id w4" in out
    stored = (fake_root / "config" / "worker.local.toml").read_text(encoding="utf-8")
    assert 'worker_id = "w4"' in stored
    assert 'master = "10.0.0.5:5050"' in stored


def test_start_worker_wajib_master_dan_id(
    load_script: Loader, fake_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-06: tanpa --master/--id pada mode non-interaktif launcher gagal jelas."""
    module = load_script("start_worker.py")
    code = module.main(["--print-command", "--no-prompt", "--root", str(fake_root)])
    captured = capsys.readouterr()
    assert code == 1
    assert "WORKER GAGAL" in captured.err
    assert "--master" in captured.err


def test_start_worker_memakai_ingatan_sebelumnya(
    load_script: Loader, fake_root: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUN-07: pemanggilan kedua cukup tanpa argumen karena berkas ingatan ada."""
    module = load_script("start_worker.py")
    first = module.main(
        ["--print-command", "--master", "10.0.0.5:5050", "--id", "w2", "--root", str(fake_root)]
    )
    assert first == 0
    capsys.readouterr()
    second = module.main(["--print-command", "--no-prompt", "--root", str(fake_root)])
    out = capsys.readouterr().out
    assert second == 0
    assert "--id w2" in out
