"""Injeksi kegagalan Worker dari luar proses (PLAN.md P6-T5)."""

from __future__ import annotations

import argparse
import os
import signal
import sys
from pathlib import Path

from pcomp import constants
from pcomp.metrics.events import EventLog


def inject(pid: int, worker_id: str, events_path: Path, reason: str = "manual") -> None:
    """Catat `worker_exit_injected` lebih dulu, lalu hentikan PID Worker."""
    log = EventLog(events_path)
    try:
        log.emit("worker_exit_injected", worker_id=worker_id, pid=pid, reason=reason)
    finally:
        log.close()
    os.kill(pid, signal.SIGTERM)


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen injeksi kegagalan."""
    parser = argparse.ArgumentParser(
        prog="pcomp.tools.inject_failure",
        description="Catat event lalu hentikan proses Worker tertentu",
    )
    parser.add_argument("--events", required=True, help="path events.jsonl tujuan")
    parser.add_argument("--pid", required=True, type=int, help="PID proses Worker")
    parser.add_argument("--worker-id", default="worker", help="identitas Worker")
    parser.add_argument("--reason", default="manual", help="alasan injeksi")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan injeksi; kode keluar bukan nol bila PID tidak dapat dihentikan."""
    args = build_parser().parse_args(argv)
    try:
        inject(args.pid, args.worker_id, Path(args.events), args.reason)
    except OSError as exc:
        print(f"INJECT GAGAL: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
