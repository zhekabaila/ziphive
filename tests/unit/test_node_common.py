"""UT-NODE-01..08: helper lintas platform launcher laptop fisik (PLAN.md P11-T5)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

Loader = Callable[[str], ModuleType]


@pytest.fixture
def node(load_script: Loader) -> ModuleType:
    return load_script("node_common.py")


def test_venv_python_per_sistem(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-01: path interpreter `.venv` mengikuti aturan POSIX dan Windows."""
    assert node.venv_python(tmp_path, "darwin") == tmp_path / ".venv" / "bin" / "python"
    assert node.venv_python(tmp_path, "linux") == tmp_path / ".venv" / "bin" / "python"
    assert node.venv_python(tmp_path, "win32") == tmp_path / ".venv" / "Scripts" / "python.exe"
    assert node.is_windows("win32") is True
    assert node.is_windows("darwin") is False


def test_venv_ready(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-02: venv dianggap siap hanya bila interpreter benar-benar ada."""
    assert node.venv_ready(tmp_path, "linux") is False
    python = node.venv_python(tmp_path, "linux")
    python.parent.mkdir(parents=True)
    python.write_text("", encoding="utf-8")
    assert node.venv_ready(tmp_path, "linux") is True


def test_version_ok(node: ModuleType) -> None:
    """UT-NODE-03: batas minimum Python 3.11 diterapkan pada (major, minor)."""
    assert node.MIN_PYTHON == (3, 11)
    assert node.version_ok((3, 11, 0)) is True
    assert node.version_ok((3, 14, 4)) is True
    assert node.version_ok((3, 9, 18)) is False
    assert node.version_ok((4, 0)) is True
    assert node.describe_version((3, 14, 4, "final", 0)) == "3.14.4"


def test_master_address_dan_parse(node: ModuleType) -> None:
    """UT-NODE-04: alamat Master divalidasi sebelum dipakai Worker."""
    assert node.master_address("10.0.0.5", 5050) == "10.0.0.5:5050"
    assert node.parse_master_address("10.0.0.5:5050") == ("10.0.0.5", 5050)
    for bad in ("10.0.0.5", ":5050", "10.0.0.5:", "10.0.0.5:0", "10.0.0.5:70000"):
        with pytest.raises(ValueError):
            node.parse_master_address(bad)


def test_worker_command(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-05: perintah Worker memuat master, id, dan procs resmi."""
    command = node.worker_command(tmp_path / "py", "10.0.0.5:5050", "w3")
    assert command[1:3] == ["-m", "pcomp.worker"]
    assert command[command.index("--master") + 1] == "10.0.0.5:5050"
    assert command[command.index("--id") + 1] == "w3"
    assert command[command.index("--procs") + 1] == "1"
    assert "--throttle" not in command

    slow = node.worker_command(tmp_path / "py", "10.0.0.5:5050", "w9", 2, 0.25)
    assert slow[slow.index("--procs") + 1] == "2"
    assert slow[slow.index("--throttle") + 1] == "0.25"


def test_master_command_inject_kills(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-06: opsi injeksi E5 hanya muncul bila diminta."""
    plain = node.master_command(tmp_path / "py", "data", "out", 9)
    assert plain[plain.index("--expect-workers") + 1] == "9"
    assert "--inject-kills" not in plain

    killing = node.master_command(tmp_path / "py", "data", "out", 9, inject_kills=3)
    assert killing[killing.index("--inject-kills") + 1] == "3"
    assert killing[killing.index("--inject-kill-fraction") + 1] == "0.5"


def test_worker_local_config_bolak_balik(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-07: pilihan operator disimpan dan dibaca kembali."""
    path = node.local_config_path(tmp_path)
    assert node.read_worker_local_config(path) == {}

    node.write_worker_local_config(path, "10.0.0.5:5050", "w7", 1, 0.25)
    stored = node.read_worker_local_config(path)
    assert stored == {
        "master": "10.0.0.5:5050",
        "worker_id": "w7",
        "procs": 1,
        "throttle": 0.25,
    }


def test_package_env_dan_bootstrap_commands(node: ModuleType, tmp_path: Path) -> None:
    """UT-NODE-08: PYTHONPATH menunjuk src dan bootstrap tidak menyentuh Python sistem."""
    env = node.package_env(tmp_path, {"PYTHONPATH": "/lain"})
    assert env["PYTHONPATH"].startswith(str(tmp_path / "src"))
    assert "/lain" in env["PYTHONPATH"]
    assert env["PYTHONUNBUFFERED"] == "1"

    commands = node.bootstrap_commands(tmp_path, "python3", "linux")
    assert commands[0][1:] == ["-m", "venv", str(tmp_path / ".venv")]
    assert commands[1][0] == str(tmp_path / ".venv" / "bin" / "python")
    assert commands[1][1:] == ["-m", "pip", "install", "-e", str(tmp_path)]
    assert node.format_command(["a b", "c"]) == '"a b" c'
