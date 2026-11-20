"""Baseline sequential: satu proses, keluaran manifest dan metrics (PLAN.md P2-T6)."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.chunker import copy_index, plan_tasks, read_chunk
from pcomp.compressor import compress, is_simulated
from pcomp.manifest import (
    Manifest,
    ManifestEntry,
    build_manifest,
    chunk_output_name,
    make_entry,
    write_manifest,
)


@dataclass(frozen=True)
class SequentialResult:
    """Hasil satu run sequential."""

    manifest: Manifest
    metrics: dict[str, Any]


def run_sequential(
    input_dir: Path,
    out_dir: Path,
    *,
    algo: str = constants.DEFAULT_ALGO,
    level: int = constants.DEFAULT_LEVEL,
    chunk_mb: int = constants.DEFAULT_CHUNK_MB,
    repeat: int = constants.DEFAULT_REPEAT,
    clock: Callable[[], float] = time.perf_counter,
) -> SequentialResult:
    """Kompres seluruh dataset pada satu proses dan tulis manifest serta metrics."""
    tasks = plan_tasks(input_dir, chunk_mb=chunk_mb, repeat=repeat)
    out_dir.mkdir(parents=True, exist_ok=True)
    per_copy = len(tasks) // repeat
    started_at = datetime.now(UTC).isoformat(timespec="seconds")

    entries: list[ManifestEntry] = []
    start = clock()
    for task in tasks:
        raw = read_chunk(input_dir, task)
        packed = compress(algo, level, raw)
        copy = copy_index(task.task_id, per_copy)
        relative = chunk_output_name(task.file, task.index, algo, copy=copy, repeat=repeat)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(packed)
        entries.append(
            make_entry(
                task,
                sha256=hashlib.sha256(raw).hexdigest(),
                length=len(raw),
                comp_size=len(packed),
                output=relative,
                copy=copy,
            )
        )
    elapsed = clock() - start

    manifest = build_manifest(
        algo=algo, level=level, chunk_mb=chunk_mb, repeat=repeat, entries=entries
    )
    write_manifest(out_dir / "manifest.json", manifest)

    total_mb = manifest.total_orig_bytes / constants.MIB
    metrics: dict[str, Any] = {
        "mode": "sequential",
        "algo": algo,
        "level": level,
        "chunk_mb": chunk_mb,
        "repeat": repeat,
        "tasks": len(entries),
        "total_orig_bytes": manifest.total_orig_bytes,
        "total_comp_bytes": manifest.total_comp_bytes,
        "total_mb": round(total_mb, 6),
        "ratio": round(manifest.ratio, 6),
        "time_s": round(elapsed, 6),
        "throughput_mbs": round(total_mb / elapsed, 6) if elapsed > 0 else 0.0,
        "simulated": is_simulated(algo),
        "started_at": started_at,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return SequentialResult(manifest=manifest, metrics=metrics)


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI sequential."""
    parser = argparse.ArgumentParser(
        prog="pcomp.sequential", description="Baseline kompresi sequential satu proses"
    )
    parser.add_argument("--input", required=True, help="folder dataset")
    parser.add_argument("--out", required=True, help="folder keluaran")
    parser.add_argument(
        "--algo", default=constants.DEFAULT_ALGO, choices=["gzip", "bz2", "lzma", "sim"]
    )
    parser.add_argument("--level", type=int, default=constants.DEFAULT_LEVEL)
    parser.add_argument("--chunk-mb", type=int, default=constants.DEFAULT_CHUNK_MB)
    parser.add_argument("--repeat", type=int, default=constants.DEFAULT_REPEAT)
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI sequential."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    result = run_sequential(
        Path(args.input),
        Path(args.out),
        algo=args.algo,
        level=args.level,
        chunk_mb=args.chunk_mb,
        repeat=args.repeat,
    )
    metrics = result.metrics
    print(f"tasks        : {metrics['tasks']}")
    print(f"total_mb     : {metrics['total_mb']}")
    print(f"ratio        : {metrics['ratio']}")
    print(f"time_s       : {metrics['time_s']}")
    print(f"throughput   : {metrics['throughput_mbs']} MB/s")
    print("SEQUENTIAL OK")
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
