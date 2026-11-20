"""Baseline paralel satu mesin memakai multiprocessing (PLAN.md P3-T1..T3).

Semua fungsi kerja bersifat top-level dan seluruh argumen/keluaran dapat dipickle,
sehingga aman untuk start method `spawn` di Windows dan macOS (AGENTS.md aturan 8).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from multiprocessing.context import SpawnContext
from pathlib import Path
from typing import Any, cast

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.chunker import copy_index, plan_tasks, read_chunk
from pcomp.compressor import TaskResult, compress_task, is_simulated
from pcomp.manifest import (
    Manifest,
    build_manifest,
    chunk_output_name,
    make_entry,
    write_manifest,
)
from pcomp.tasks import Task

LOCAL_START_METHOD = "spawn"


@dataclass(frozen=True)
class LocalResult:
    """Hasil satu run local parallel."""

    manifest: Manifest
    metrics: dict[str, Any]


def pool_context() -> SpawnContext:
    """Konteks multiprocessing dengan start method spawn (AGENTS.md aturan 8)."""
    return cast(SpawnContext, mp.get_context(LOCAL_START_METHOD))


def run_task(payload: tuple[Task, str, str, int]) -> tuple[int, TaskResult]:
    """Fungsi kerja top-level: baca chunk dari disk lalu kompres di proses pool."""
    task, input_dir, algo, level = payload
    try:
        raw = read_chunk(Path(input_dir), task)
    except OSError as exc:
        # Kegagalan baca adalah error task, bukan error fatal pool (P3-T3).
        return os.getpid(), TaskResult(
            task_id=task.task_id,
            ok=False,
            sha256="",
            comp_size=0,
            data=None,
            error=f"{type(exc).__name__}: {exc}",
            compute_sec=0.0,
        )
    return os.getpid(), compress_task(task, raw, algo, level)


def run_local(
    input_dir: Path,
    out_dir: Path,
    *,
    algo: str = constants.DEFAULT_ALGO,
    level: int = constants.DEFAULT_LEVEL,
    chunk_mb: int = constants.DEFAULT_CHUNK_MB,
    repeat: int = constants.DEFAULT_REPEAT,
    procs: int = constants.DEFAULT_PROCS,
    tasks: Sequence[Task] | None = None,
    clock: Callable[[], float] = time.perf_counter,
) -> LocalResult:
    """Kompres dataset dengan pool proses; manifest sama dengan baseline sequential."""
    if procs < 1:
        raise ValueError("procs minimal 1")
    planned = (
        list(tasks)
        if tasks is not None
        else plan_tasks(input_dir, chunk_mb=chunk_mb, repeat=repeat)
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    per_copy = len(planned) // repeat if repeat > 0 else 0
    by_id = {task.task_id: task for task in planned}
    started_at = datetime.now(UTC).isoformat(timespec="seconds")

    results: list[TaskResult] = []
    busy: dict[int, float] = {}
    start = clock()
    if planned:
        payloads = [(task, str(input_dir), algo, level) for task in planned]
        with pool_context().Pool(processes=procs) as pool:
            for pid, result in pool.imap_unordered(run_task, payloads):
                busy[pid] = busy.get(pid, 0.0) + result.compute_sec
                results.append(result)
    elapsed = clock() - start

    entries = []
    errors: list[dict[str, Any]] = []
    for result in sorted(results, key=lambda item: item.task_id):
        task = by_id[result.task_id]
        if not result.ok or result.data is None:
            errors.append(
                {
                    "task_id": task.task_id,
                    "file": task.file,
                    "index": task.index,
                    "error": result.error or "tidak diketahui",
                }
            )
            continue
        copy = copy_index(task.task_id, per_copy) if per_copy > 0 else 0
        relative = chunk_output_name(task.file, task.index, algo, copy=copy, repeat=repeat)
        target = out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(result.data)
        entries.append(
            make_entry(
                task,
                sha256=result.sha256,
                length=task.length,
                comp_size=result.comp_size,
                output=relative,
                copy=copy,
            )
        )

    manifest = build_manifest(
        algo=algo, level=level, chunk_mb=chunk_mb, repeat=repeat, entries=entries
    )
    write_manifest(out_dir / "manifest.json", manifest)

    total_mb = manifest.total_orig_bytes / constants.MIB
    metrics: dict[str, Any] = {
        "mode": "local",
        "procs": procs,
        "algo": algo,
        "level": level,
        "chunk_mb": chunk_mb,
        "repeat": repeat,
        "tasks": len(planned),
        "tasks_ok": len(entries),
        "tasks_failed": len(errors),
        "total_orig_bytes": manifest.total_orig_bytes,
        "total_comp_bytes": manifest.total_comp_bytes,
        "total_mb": round(total_mb, 6),
        "ratio": round(manifest.ratio, 6),
        "time_s": round(elapsed, 6),
        "throughput_mbs": round(total_mb / elapsed, 6) if elapsed > 0 else 0.0,
        "busy_per_process": {str(pid): round(sec, 6) for pid, sec in sorted(busy.items())},
        "errors": errors,
        "simulated": is_simulated(algo),
        "started_at": started_at,
    }
    (out_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return LocalResult(manifest=manifest, metrics=metrics)


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI local parallel."""
    parser = argparse.ArgumentParser(
        prog="pcomp.local_parallel", description="Baseline kompresi paralel satu mesin"
    )
    parser.add_argument("--input", required=True, help="folder dataset")
    parser.add_argument("--out", required=True, help="folder keluaran")
    parser.add_argument(
        "--algo", default=constants.DEFAULT_ALGO, choices=["gzip", "bz2", "lzma", "sim"]
    )
    parser.add_argument("--level", type=int, default=constants.DEFAULT_LEVEL)
    parser.add_argument("--chunk-mb", type=int, default=constants.DEFAULT_CHUNK_MB)
    parser.add_argument("--repeat", type=int, default=constants.DEFAULT_REPEAT)
    parser.add_argument("--procs", type=int, default=constants.DEFAULT_PROCS, help="jumlah proses")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI local parallel."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    result = run_local(
        Path(args.input),
        Path(args.out),
        algo=args.algo,
        level=args.level,
        chunk_mb=args.chunk_mb,
        repeat=args.repeat,
        procs=args.procs,
    )
    metrics = result.metrics
    print(f"tasks        : {metrics['tasks']}")
    print(f"procs        : {metrics['procs']}")
    print(f"tasks_ok     : {metrics['tasks_ok']}")
    print(f"tasks_failed : {metrics['tasks_failed']}")
    print(f"total_mb     : {metrics['total_mb']}")
    print(f"ratio        : {metrics['ratio']}")
    print(f"time_s       : {metrics['time_s']}")
    print(f"throughput   : {metrics['throughput_mbs']} MB/s")
    for item in metrics["errors"]:
        print(f"ERROR task {item['task_id']} ({item['file']}): {item['error']}")
    if metrics["tasks_failed"] == 0:
        print("LOCAL OK")
        return constants.EXIT_OK
    print("LOCAL FAILED")
    return constants.EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
