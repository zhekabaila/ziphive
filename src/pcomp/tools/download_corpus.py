"""Unduh korpus benchmark dari URL resmi (PLAN.md P2-T5).

Skrip ini tidak dijalankan otomatis. URL arsip wajib diberikan user dari sumber resmi pada
ASSETS.md; agent tidak mengarang URL. Hasil unduhan (SHA-256 dan tanggal) dicetak agar user
dapat mengisi ASSETS.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pcomp import constants
from pcomp.banner import try_print_banner

DOWNLOAD_TIMEOUT_SEC = 120.0
_CHUNK = 1024 * 1024


class DownloadError(ValueError):
    """URL atau hasil unduhan tidak valid."""


@dataclass(frozen=True)
class DownloadPlan:
    """Rencana unduhan satu arsip."""

    url: str
    target: Path
    filename: str


def build_plan(url: str, out_dir: Path) -> DownloadPlan:
    """Turunkan nama file dari URL; tolak skema selain http/https."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise DownloadError(f"skema URL tidak didukung: {parsed.scheme or '(kosong)'}")
    filename = Path(parsed.path).name
    if not filename:
        raise DownloadError("URL tidak memuat nama file arsip")
    return DownloadPlan(url=url, target=out_dir / filename, filename=filename)


def sha256_file(path: Path) -> str:
    """Hitung SHA-256 sebuah file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(_CHUNK)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def download(plan: DownloadPlan, expected_sha256: str | None = None) -> dict[str, Any]:
    """Unduh arsip, verifikasi checksum bila diberikan, dan kembalikan metadata."""
    plan.target.parent.mkdir(parents=True, exist_ok=True)
    partial = plan.target.with_suffix(plan.target.suffix + ".part")
    with (
        urllib.request.urlopen(plan.url, timeout=DOWNLOAD_TIMEOUT_SEC) as response,
        partial.open("wb") as handle,
    ):
        while True:
            block = response.read(_CHUNK)
            if not block:
                break
            handle.write(block)
    actual = sha256_file(partial)
    if expected_sha256 is not None and actual != expected_sha256:
        partial.unlink(missing_ok=True)
        raise DownloadError(f"sha256 tidak cocok: {actual} != {expected_sha256}")
    partial.replace(plan.target)
    return {
        "url": plan.url,
        "file": plan.filename,
        "size_bytes": plan.target.stat().st_size,
        "sha256": actual,
        "accessed_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI download_corpus."""
    parser = argparse.ArgumentParser(
        prog="pcomp.tools.download_corpus",
        description="Unduh korpus dari URL resmi (tidak dijalankan otomatis)",
    )
    parser.add_argument("--url", required=True, help="URL arsip dari sumber resmi di ASSETS.md")
    parser.add_argument("--out", required=True, help="folder tujuan")
    parser.add_argument("--expected-sha256", default=None, help="checksum yang diharapkan")
    parser.add_argument("--dry-run", action="store_true", help="cetak rencana tanpa mengunduh")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI download_corpus."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    plan = build_plan(args.url, Path(args.out))
    print(f"url          : {plan.url}")
    print(f"target       : {plan.target}")
    if args.dry_run:
        print("DRY RUN: tidak ada unduhan")
        return constants.EXIT_OK

    metadata = download(plan, args.expected_sha256)
    report = Path(args.out) / "download-report.json"
    report.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(f"size_bytes   : {metadata['size_bytes']}")
    print(f"sha256       : {metadata['sha256']}")
    print(f"accessed_at  : {metadata['accessed_at']}")
    print("Salin SHA-256 dan tanggal akses di atas ke ASSETS.md (kolom diisi user).")
    print("DOWNLOAD OK")
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
