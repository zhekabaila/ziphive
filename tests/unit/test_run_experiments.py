"""UT-EXP-01..05: orkestrasi eksperimen 10 node virtual (ADR-015)."""

from __future__ import annotations

import json
from collections.abc import Callable
from types import ModuleType

Loader = Callable[[str], ModuleType]


def test_container_specs_satu_per_worker(load_script: Loader) -> None:
    """UT-EXP-01: satu container per Worker dengan hostname berurutan."""
    mod = load_script("run_experiments.py")
    specs = mod.container_specs(3)
    assert [item.name for item in specs] == ["ziphive-w1", "ziphive-w2", "ziphive-w3"]
    assert [item.worker_id for item in specs] == ["w1", "w2", "w3"]
    assert all(item.throttle == 0.0 for item in specs)


def test_container_specs_throttle_hanya_worker_terakhir(load_script: Loader) -> None:
    """UT-EXP-02: `--throttle` hanya diberikan ke Worker terakhir seperti runner E4."""
    mod = load_script("run_experiments.py")
    specs = mod.container_specs(4, 0.25)
    assert [item.throttle for item in specs] == [0.0, 0.0, 0.0, 0.25]


def test_read_progress_menghitung_task(load_script: Loader, tmp_path) -> None:
    """UT-EXP-03: progres E5 dihitung dari run_started dan task_done."""
    mod = load_script("run_experiments.py")
    events = tmp_path / "events.jsonl"
    rows = [
        {"ts": 1.0, "event": "run_started", "tasks": 4},
        {"ts": 2.0, "event": "task_done", "task_id": 0},
        {"ts": 3.0, "event": "task_done", "task_id": 1},
    ]
    events.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
    assert mod.read_progress(events) == (2, 4)


def test_read_progress_tanpa_file(load_script: Loader, tmp_path) -> None:
    """UT-EXP-04: file event yang belum ada dianggap progres nol."""
    mod = load_script("run_experiments.py")
    assert mod.read_progress(tmp_path / "tidak-ada.jsonl") == (0, 0)


def test_next_run_dir_melewati_yang_sudah_ditangani(load_script: Loader, tmp_path) -> None:
    """UT-EXP-05: folder run diproses berurutan dan tidak diulang."""
    mod = load_script("run_experiments.py")
    base = tmp_path / "E6"
    for name in ("run-b", "run-a"):
        (base / name).mkdir(parents=True)
        (base / name / "spec.json").write_text("{}", encoding="utf-8")
    first = mod.next_run_dir(tmp_path, "E6", set())
    assert first is not None and first.name == "run-a"
    second = mod.next_run_dir(tmp_path, "E6", {"run-a"})
    assert second is not None and second.name == "run-b"
    for name in ("run-a", "run-b"):
        (base / name / "metrics.json").write_text("{}", encoding="utf-8")
    assert mod.next_run_dir(tmp_path, "E6", set()) is None
    assert mod.next_run_dir(tmp_path, "E9", set()) is None


def test_experiment_args_memilih_mode(load_script: Loader) -> None:
    """UT-EXP-06: E1/E2 mode lokal, E3/E4/E6 mode container dengan jumlah Worker benar."""
    mod = load_script("run_experiments.py")
    args = mod.build_parser().parse_args([])
    common = ["--reps", "3"]

    e1, lan1 = mod.experiment_args("E1", args, common)
    assert "--local" in e1 and not lan1
    e2, lan2 = mod.experiment_args("E2", args, common)
    assert e2[e2.index("--procs") + 1] == "1,2,4,8" and not lan2
    e6, lan6 = mod.experiment_args("E6", args, common)
    assert "--lan" in e6 and lan6
    assert e6[e6.index("--workers") + 1] == "1,2,4,6,9"
    assert mod.uses_containers(e6) is True
    assert mod.uses_containers(e1) is False


def test_required_artifacts_sadar_mode(load_script: Loader, tmp_path) -> None:
    """UT-EXP-07: events.jsonl hanya wajib pada mode terdistribusi."""
    mod = load_script("run_experiments.py")
    distributed = tmp_path / "dist"
    distributed.mkdir()
    (distributed / "spec.json").write_text('{"mode": "distributed"}', encoding="utf-8")
    assert "events.jsonl" in mod.required_artifacts(distributed)

    for mode in ("sequential", "local"):
        local = tmp_path / mode
        local.mkdir()
        (local / "spec.json").write_text(f'{{"mode": "{mode}"}}', encoding="utf-8")
        assert "events.jsonl" not in mod.required_artifacts(local)
        assert "metrics.json" in mod.required_artifacts(local)


def test_mode_external_memakai_port_tetap(load_script: Loader) -> None:
    """UT-EXP-08: mode external memakai port tetap dan lan-wait, bukan container."""
    mod = load_script("run_experiments.py")
    args = mod.build_parser().parse_args(
        ["--worker-mode", "external", "--port", "5055", "--lan-wait", "120"]
    )
    common = ["--reps", "1"]

    e6, lan = mod.experiment_args("E6", args, common)
    assert "--lan" in e6 and lan
    assert e6[e6.index("--port") + 1] == "5055"
    assert e6[e6.index("--lan-wait") + 1] == "120.0"
    assert mod.uses_containers(e6) is True

    e5_base = mod.lan_args(args, common)
    assert e5_base[e5_base.index("--port") + 1] == "5055"

    docker = mod.build_parser().parse_args([])
    assert docker.worker_mode == "docker"
    plain = mod.lan_args(docker, common)
    assert "--port" not in plain
