"""Entry point CLI: `python -m pcomp`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pcomp import constants
from pcomp.banner import load_group_info, print_banner


def build_parser() -> argparse.ArgumentParser:
    """Bangun parser argumen tingkat paket."""
    parser = argparse.ArgumentParser(
        prog="pcomp",
        description=f"{constants.PROJECT_NAME} - kompresi data terdistribusi Master-Worker",
    )
    parser.add_argument("--version", action="store_true", help="cetak versi lalu keluar")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path file group.toml (default: config/group.toml)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI dan kembalikan exit code."""
    args = build_parser().parse_args(argv)
    if args.version:
        print(f"{constants.PROJECT_NAME} {constants.__version__}")
        return constants.EXIT_OK

    try:
        info = load_group_info(Path(args.group_config))
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return constants.EXIT_ERROR

    print_banner(info)
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
