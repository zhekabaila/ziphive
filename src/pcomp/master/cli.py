"""CLI Master: `python -m pcomp.master` (PLAN.md P4-T1)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.config import ConfigError, load_master_config
from pcomp.logging_setup import setup_logging
from pcomp.master.server import MasterServer

OVERRIDE_KEYS = (
    "host",
    "port",
    "input",
    "out",
    "algo",
    "level",
    "chunk_mb",
    "repeat",
    "expect_workers",
    "scheduler",
)


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen Master; CLI menimpa nilai TOML."""
    parser = argparse.ArgumentParser(prog="pcomp.master", description="Master ZipHive")
    parser.add_argument("--config", default=str(constants.DEFAULT_MASTER_CONFIG))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--input")
    parser.add_argument("--out")
    parser.add_argument("--algo", choices=["gzip", "bz2", "lzma", "sim"])
    parser.add_argument("--level", type=int)
    parser.add_argument("--chunk-mb", type=int)
    parser.add_argument("--repeat", type=int)
    parser.add_argument("--expect-workers", type=int)
    parser.add_argument("--scheduler", choices=["dynamic", "static"])
    parser.add_argument(
        "--barrier-timeout",
        type=float,
        default=constants.DEFAULT_BARRIER_TIMEOUT,
        help="detik menunggu Worker sebelum mulai atau berhenti",
    )
    parser.add_argument("--group-config", default=str(constants.DEFAULT_GROUP_CONFIG))
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan Master; exit code bukan nol bila ada task gagal atau tanpa Worker."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    setup_logging(level=args.log_level)
    overrides = {key: getattr(args, key) for key in OVERRIDE_KEYS}
    try:
        config = load_master_config(Path(args.config), overrides)
    except (FileNotFoundError, ConfigError) as exc:
        print(f"MASTER GAGAL: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR

    try:
        server = MasterServer(config, barrier_timeout=args.barrier_timeout)
    except (FileNotFoundError, OSError, ValueError) as exc:
        print(f"MASTER GAGAL: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR

    code = server.run()
    if server.last_error:
        print(f"MASTER GAGAL: {server.last_error}", file=sys.stderr)
    elif server.metrics:
        metrics = server.metrics
        print(f"tasks        : {metrics['tasks']}")
        print(f"tasks_ok     : {metrics['tasks_ok']}")
        print(f"tasks_failed : {metrics['tasks_failed']}")
        print(f"workers      : {metrics['workers']}")
        print(f"total_mb     : {metrics['total_mb']}")
        print(f"ratio        : {metrics['ratio']}")
        print(f"time_s       : {metrics['time_s']}")
        print(f"throughput   : {metrics['throughput_mbs']} MB/s")
    if code == constants.EXIT_OK:
        print("MASTER OK")
    else:
        print("MASTER FAILED")
    return code
