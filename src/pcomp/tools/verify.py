"""Verifikasi hasil kompresi dari manifest (PLAN.md P2-T5)."""

from __future__ import annotations

import argparse
from pathlib import Path

from pcomp import constants
from pcomp.banner import try_print_banner
from pcomp.manifest import EntryVerification, read_manifest, verify_entries


def verify_run(
    manifest_path: Path, out_dir: Path | None = None
) -> tuple[bool, list[EntryVerification]]:
    """Dekompresi seluruh chunk dan bandingkan dengan manifest."""
    manifest = read_manifest(manifest_path)
    target = out_dir if out_dir is not None else manifest_path.parent
    results = verify_entries(manifest, target)
    return all(item.ok for item in results), results


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI verify."""
    parser = argparse.ArgumentParser(
        prog="pcomp.tools.verify", description="Verifikasi hasil kompresi lewat manifest"
    )
    parser.add_argument("--manifest", required=True, help="path manifest.json")
    parser.add_argument("--out", default=None, help="folder chunk (default: folder manifest)")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI verify; exit code bukan nol bila ada chunk rusak."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    ok, results = verify_run(Path(args.manifest), Path(args.out) if args.out else None)
    for item in results:
        if not item.ok:
            print(f"RUSAK: {item.entry.output} ({item.reason})")
    print(f"chunks       : {len(results)}")
    if ok:
        print("VERIFY OK")
        return constants.EXIT_OK
    print("VERIFY FAILED")
    return constants.EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
