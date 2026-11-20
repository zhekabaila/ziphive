"""CLI Worker: `python -m pcomp.worker` (PLAN.md P4-T3)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.config import ConfigError, load_worker_config
from pcomp.logging_setup import setup_logging
from pcomp.worker.client import WorkerClient

OVERRIDE_KEYS = ("master", "worker_id", "procs")


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen Worker; CLI menimpa nilai TOML."""
    parser = argparse.ArgumentParser(prog="pcomp.worker", description="Worker ZipHive")
    parser.add_argument("--config", default=str(constants.DEFAULT_WORKER_CONFIG))
    parser.add_argument("--master", help="alamat Master host:port")
    parser.add_argument("--id", dest="worker_id", help="identitas Worker")
    parser.add_argument("--procs", type=int, help="jumlah proses kompresi")
    parser.add_argument(
        "--protocol-version",
        type=int,
        default=constants.PROTOCOL_VERSION,
        help="versi protokol yang dikirim saat REGISTER (untuk uji penolakan)",
    )
    parser.add_argument("--group-config", default=str(constants.DEFAULT_GROUP_CONFIG))
    parser.add_argument("--log-level", default="INFO")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan Worker sampai Master mengirim SHUTDOWN."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    setup_logging(level=args.log_level)
    overrides = {key: getattr(args, key) for key in OVERRIDE_KEYS}
    try:
        config = load_worker_config(Path(args.config), overrides)
    except (FileNotFoundError, ConfigError) as exc:
        print(f"WORKER GAGAL: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR

    client = WorkerClient(config, protocol_version=args.protocol_version)
    code = client.run()
    if code == constants.EXIT_OK:
        print(f"WORKER OK ({config.worker_id})")
    else:
        print(f"WORKER FAILED ({config.worker_id})")
    return code
