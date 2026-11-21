"""UT-LAUNCH-01..04: pembangkit perintah Worker dari `config/nodes.toml` (PLAN.md P8-T2)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest

Loader = Callable[[str], ModuleType]

NODES_TOML = """\
[[node]]
nama = "n1"
host = "10.0.0.1"
role = "master"
user = "ani"
python = "python3"

[[node]]
nama = "n2"
host = "10.0.0.2"
role = "worker"
user = "budi"
python = "python3"
procs = 4

[[node]]
nama = "n3"
host = "10.0.0.3"
role = "worker"
user = "citra"
python = "python3"
"""

PLACEHOLDER_TOML = """\
[[node]]
nama = "n1"
host = "<IP_N1>"
role = "master"
user = "<USER_N1>"
python = "python3"

[[node]]
nama = "n2"
host = "<IP_N2>"
role = "worker"
user = "<USER_N2>"
python = "python3"
"""


@pytest.fixture
def launch(load_script: Loader) -> ModuleType:
    return load_script("launch_workers.py")


def write_toml(tmp_path: Path, text: str, name: str = "nodes.toml") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_load_nodes_and_roles(launch: ModuleType, tmp_path: Path) -> None:
    """UT-LAUNCH-01: nodes.toml dibaca dan peran dipisahkan."""
    nodes = launch.load_nodes(write_toml(tmp_path, NODES_TOML))
    assert [item.name for item in nodes] == ["n1", "n2", "n3"]
    assert nodes[1].procs == 4
    assert nodes[2].procs is None

    master, workers = launch.split_roles(nodes)
    assert master.name == "n1"
    assert [item.name for item in workers] == ["n2", "n3"]

    with pytest.raises(ValueError):
        launch.split_roles([nodes[1], nodes[2]])

    with pytest.raises(ValueError):
        launch.split_roles([nodes[0], nodes[0]])

    with pytest.raises(FileNotFoundError):
        launch.load_nodes(tmp_path / "tidak-ada.toml")

    broken = tmp_path / "rusak.toml"
    broken.write_text('[[node]]\nnama = "x"\n', encoding="utf-8")
    with pytest.raises(ValueError):
        launch.load_nodes(broken)

    bad_role = tmp_path / "salah.toml"
    bad_role.write_text('[[node]]\nnama="x"\nhost="h"\nrole="bos"\nuser="u"\n', encoding="utf-8")
    with pytest.raises(ValueError):
        launch.load_nodes(bad_role)


def test_placeholder_detection(launch: ModuleType, tmp_path: Path) -> None:
    """UT-LAUNCH-02: nilai placeholder pada inventaris dilaporkan per field."""
    nodes = launch.load_nodes(write_toml(tmp_path, PLACEHOLDER_TOML))
    assert launch.placeholder_fields(nodes[0]) == ["host", "user"]

    complete = launch.Node(name="n5", host="10.0.0.5", role="worker", user="dodi", python="python3")
    assert launch.placeholder_fields(complete) == []


def test_build_plan_commands(launch: ModuleType, tmp_path: Path) -> None:
    """UT-LAUNCH-03: perintah Worker dan argv ssh dibangkitkan sesuai DEPLOYMENT.md."""
    nodes = launch.load_nodes(write_toml(tmp_path, NODES_TOML))
    plan = launch.build_plan(nodes, port=5050, procs=2, workdir="/home/budi/ziphive")

    assert len(plan) == 2
    first = plan[0]
    assert first.worker_id == "w1"
    assert first.command == (
        "cd /home/budi/ziphive && python3 -m pcomp.worker --master 10.0.0.1:5050 --id w1 --procs 4"
    )
    assert first.ssh == ["ssh", "budi@10.0.0.2", first.command]

    second = plan[1]
    assert second.worker_id == "w2"
    assert "--procs 2" in second.command
    assert second.ssh == ["ssh", "citra@10.0.0.3", second.command]

    assert launch.worker_address(nodes[0], 5050) == "10.0.0.1:5050"
    with pytest.raises(ValueError):
        launch.build_plan(nodes, port=5050, procs=0)


def test_main_print_and_ssh_modes(
    launch: ModuleType, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """UT-LAUNCH-04: mode `--print` mencetak perintah, mode `--ssh` menolak placeholder."""
    good = write_toml(tmp_path, NODES_TOML, "lengkap.toml")
    assert launch.main(["--nodes", str(good), "--print"]) == 0
    output = capsys.readouterr().out
    assert "ssh budi@10.0.0.2" in output
    assert "--id w1" in output
    assert "LAUNCH PLAN OK" in output

    placeholder = write_toml(tmp_path, PLACEHOLDER_TOML, "placeholder.toml")
    capsys.readouterr()
    assert launch.main(["--nodes", str(placeholder), "--print"]) == 1
    assert "placeholder" in capsys.readouterr().err.lower()

    assert launch.main(["--nodes", str(good), "--ssh", "--dry-run"]) == 0
    assert "LAUNCH OK" in capsys.readouterr().out
