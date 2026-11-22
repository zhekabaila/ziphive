"""Validasi kelengkapan hasil eksperimen resmi (PLAN.md P9-T1).

Payload chunk dihapus setelah `VERIFY OK` untuk menghemat disk, sehingga validasi
memakai `verify.log` sebagai bukti verifikasi, bukan dekompresi ulang.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.bench.runner import SUMMARY_COLUMNS

REQUIRED_EXPS = ("E1", "E2", "E3", "E4", "E5", "E6")
BASE_FILES = ("spec.json", "env.json", "metrics.json", "manifest.json")
MIN_REPS = 3


def load_json(path: Path) -> dict[str, Any] | None:
    """Baca JSON; None bila tidak ada atau rusak."""
    if not path.is_file():
        return None
    try:
        return dict(json.loads(path.read_text(encoding="utf-8")))
    except (json.JSONDecodeError, OSError):
        return None


def required_files(spec: dict[str, Any] | None) -> tuple[str, ...]:
    """Berkas wajib per run; `events.jsonl` hanya ditulis pada mode terdistribusi."""
    mode = (spec or {}).get("mode")
    if mode in ("sequential", "local"):
        return BASE_FILES
    return (*BASE_FILES, "events.jsonl")


def check_run(run_dir: Path) -> list[str]:
    """Daftar masalah pada satu folder run; daftar kosong berarti run lengkap."""
    spec = load_json(run_dir / "spec.json")
    problems = [
        f"tidak ada {name}" for name in required_files(spec) if not (run_dir / name).is_file()
    ]

    metrics = load_json(run_dir / "metrics.json")
    if metrics is None:
        problems.append("metrics.json tidak dapat dibaca")
    elif metrics.get("simulated") or str(metrics.get("algo")) == "sim":
        problems.append("hasil algoritma sim tidak boleh masuk results/raw")
    elif not metrics.get("tasks"):
        problems.append("metrics.tasks kosong")

    events = run_dir / "events.jsonl"
    if events.is_file():
        text = events.read_text(encoding="utf-8", errors="replace")
        if "run_started" not in text or "run_finished" not in text:
            problems.append("events.jsonl tidak memuat run_started dan run_finished")

    verify = run_dir / "verify.log"
    if not verify.is_file():
        problems.append("tidak ada verify.log")
    elif "VERIFY OK" not in verify.read_text(encoding="utf-8", errors="replace"):
        problems.append("verify.log tanpa VERIFY OK")
    return problems


def config_key(spec: dict[str, Any]) -> tuple[Any, ...]:
    """Kunci konfigurasi untuk menghitung jumlah ulangan tiap kondisi."""
    return (
        spec.get("mode"),
        spec.get("workers"),
        spec.get("procs"),
        spec.get("scheduler"),
        spec.get("throttle"),
        spec.get("kill_workers"),
    )


def collect_runs(root: Path, exp: str) -> list[Path]:
    """Folder run milik satu eksperimen, terurut menurut nama."""
    base = root / exp
    if not base.is_dir():
        return []
    return [
        path for path in sorted(base.iterdir()) if path.is_dir() and (path / "spec.json").is_file()
    ]


def validate_root(root: Path, min_reps: int = MIN_REPS) -> tuple[list[str], list[Path]]:
    """Periksa seluruh eksperimen; kembalikan (masalah, run yang diperiksa)."""
    problems: list[str] = []
    checked: list[Path] = []
    for exp in REQUIRED_EXPS:
        runs = collect_runs(root, exp)
        if not runs:
            problems.append(f"{exp}: tidak ada run")
            continue
        groups: dict[tuple[Any, ...], list[Path]] = {}
        for run in runs:
            checked.append(run)
            problems += [f"{run.relative_to(root)}: {item}" for item in check_run(run)]
            spec = load_json(run / "spec.json") or {}
            groups.setdefault(config_key(spec), []).append(run)
        for key, group in groups.items():
            if len(group) < min_reps:
                problems.append(
                    f"{exp}: konfigurasi {key} hanya {len(group)} ulangan (minimal {min_reps})"
                )
    return problems, checked


def check_summary(summary_path: Path, runs: list[Path]) -> list[str]:
    """Bandingkan summary.csv dengan skema EXPERIMENTS.md bagian 4."""
    if not summary_path.is_file():
        return [f"{summary_path} tidak ada"]
    with summary_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = reader.fieldnames or []
    problems: list[str] = []
    if tuple(columns) != tuple(SUMMARY_COLUMNS):
        problems.append("kolom summary.csv tidak sesuai skema EXPERIMENTS.md bagian 4")
    if len(rows) < len(runs):
        problems.append(f"summary.csv {len(rows)} baris, run ditemukan {len(runs)}")
    bad = [row.get("run_id", "?") for row in rows if row.get("verify_ok") != "True"]
    if bad:
        problems.append(f"summary.csv verify_ok bukan True: {', '.join(bad[:3])}")
    return problems


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI validasi hasil."""
    parser = argparse.ArgumentParser(
        prog="pcomp.tools.validate_results",
        description="Validasi kelengkapan results/raw eksperimen resmi",
    )
    parser.add_argument("root", nargs="?", default="results/raw", help="folder hasil eksperimen")
    parser.add_argument("--summary", default=None, help="path summary.csv (default: induk root)")
    parser.add_argument("--min-reps", type=int, default=MIN_REPS)
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan validasi; exit code bukan nol bila ada masalah."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    root = Path(args.root)
    summary = Path(args.summary) if args.summary else root.parent / "summary.csv"
    problems, runs = validate_root(root, args.min_reps)
    problems += check_summary(summary, runs)
    for exp in REQUIRED_EXPS:
        print(f"{exp:3}: {len(collect_runs(root, exp))} run")
    print(f"total run    : {len(runs)}")
    print(f"summary      : {summary}")
    for item in problems:
        print(f"MASALAH: {item}")
    if problems:
        print("RESULTS INVALID")
        return constants.EXIT_ERROR
    print("RESULTS VALID")
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
