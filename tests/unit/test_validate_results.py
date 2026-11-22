"""UT-VAL-01..06: validasi kelengkapan `results/raw` (PLAN.md P9-T1)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pcomp.bench.runner import SUMMARY_COLUMNS
from pcomp.tools import validate_results


def make_run(root: Path, exp: str, name: str, **spec: object) -> Path:
    """Buat satu folder run lengkap dengan nilai default yang sah."""
    run = root / exp / name
    run.mkdir(parents=True)
    payload = {
        "exp": exp,
        "mode": "sequential" if exp == "E1" else "distributed",
        "workers": 0 if exp == "E1" else 9,
        "procs": 1,
        "scheduler": "dynamic",
        "throttle": 0.0,
        "kill_workers": 0,
        **spec,
    }
    (run / "spec.json").write_text(json.dumps(payload), encoding="utf-8")
    (run / "env.json").write_text("{}", encoding="utf-8")
    (run / "metrics.json").write_text(
        json.dumps({"algo": "lzma", "simulated": False, "tasks": 5}), encoding="utf-8"
    )
    (run / "events.jsonl").write_text(
        '{"event": "run_started"}\n{"event": "run_finished"}\n', encoding="utf-8"
    )
    (run / "manifest.json").write_text("{}", encoding="utf-8")
    (run / "verify.log").write_text("chunks : 5\nVERIFY OK\n", encoding="utf-8")
    return run


def make_root(tmp_path: Path, reps: int = 3) -> Path:
    """Bangun results/raw dengan enam eksperimen dan tiga ulangan per kondisi."""
    root = tmp_path / "raw"
    for exp in validate_results.REQUIRED_EXPS:
        for rep in range(1, reps + 1):
            make_run(root, exp, f"{exp}-r{rep}")
    return root


def write_summary(root: Path, rows: int) -> Path:
    """Tulis summary.csv dengan skema resmi."""
    path = root.parent / "summary.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(SUMMARY_COLUMNS))
        writer.writeheader()
        for _ in range(rows):
            writer.writerow({column: "1" for column in SUMMARY_COLUMNS} | {"verify_ok": "True"})
    return path


def test_run_lengkap_tanpa_masalah(tmp_path: Path) -> None:
    """UT-VAL-01: run dengan seluruh berkas wajib dianggap lengkap."""
    run = make_run(tmp_path, "E3", "E3-r1")
    assert validate_results.check_run(run) == []


def test_run_tanpa_metrics_dan_verify(tmp_path: Path) -> None:
    """UT-VAL-02: berkas wajib yang hilang dilaporkan."""
    run = make_run(tmp_path, "E3", "E3-r1")
    (run / "metrics.json").unlink()
    (run / "verify.log").write_text("VERIFY FAILED\n", encoding="utf-8")
    problems = validate_results.check_run(run)
    assert any("metrics.json" in item for item in problems)
    assert any("VERIFY OK" in item for item in problems)


def test_run_algo_sim_ditolak(tmp_path: Path) -> None:
    """UT-VAL-03: hasil algoritma `sim` tidak boleh masuk `results/raw`."""
    run = make_run(tmp_path, "E3", "E3-r1")
    (run / "metrics.json").write_text(json.dumps({"algo": "sim", "tasks": 5}), encoding="utf-8")
    assert any("sim" in item for item in validate_results.check_run(run))


def test_jumlah_ulangan_kurang(tmp_path: Path) -> None:
    """UT-VAL-04: konfigurasi dengan dua ulangan dilaporkan kurang."""
    root = tmp_path / "raw"
    for rep in (1, 2):
        make_run(root, "E1", f"E1-r{rep}")
    problems, runs = validate_results.validate_root(root)
    assert len(runs) == 2
    assert any("hanya 2 ulangan" in item for item in problems)
    assert any("E6: tidak ada run" in item for item in problems)


def test_root_lengkap_valid(tmp_path: Path) -> None:
    """UT-VAL-05: enam eksperimen dengan tiga ulangan dan summary sesuai skema valid."""
    root = make_root(tmp_path)
    write_summary(root, rows=18)
    problems, runs = validate_results.validate_root(root)
    assert len(runs) == 18
    assert validate_results.check_summary(root.parent / "summary.csv", runs) == []
    assert problems == []


def test_summary_tidak_sesuai_skema(tmp_path: Path) -> None:
    """UT-VAL-06: kolom ringkas yang tidak sesuai skema dilaporkan."""
    root = make_root(tmp_path)
    path = root.parent / "summary.csv"
    path.write_text("exp,run_id\nE1,E1-r1\n", encoding="utf-8")
    problems = validate_results.check_summary(path, validate_results.validate_root(root)[1])
    assert any("skema" in item for item in problems)


def test_run_tanpa_events_hanya_sah_untuk_mode_non_distributed(tmp_path: Path) -> None:
    """UT-VAL-07: mode sequential dan local tidak menulis events.jsonl, bukan pelanggaran."""
    for exp, name, mode in (("E1", "E1-r1", "sequential"), ("E2", "E2-r1", "local")):
        run = make_run(tmp_path, exp, name, mode=mode, workers=0)
        (run / "events.jsonl").unlink()
        assert validate_results.check_run(run) == []
    assert "events.jsonl" in validate_results.required_files({"mode": "distributed"})
