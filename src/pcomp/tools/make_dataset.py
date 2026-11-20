"""Dataset sintetis deterministik untuk test dan smoke (PLAN.md P2-T5)."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pcomp import constants
from pcomp.banner import try_print_banner

_WORDS = (
    "kompresi data terdistribusi master worker chunk paralel jaringan proses antrean",
    "hash verifikasi manifest throughput latensi pengukuran eksperimen laporan",
    "sistem terdistribusi komputasi paralel universitas siliwangi informatika",
)


def _text_bytes(size: int, rng: random.Random) -> bytes:
    parts: list[bytes] = []
    total = 0
    while total < size:
        line = " ".join(rng.choice(_WORDS).split()) + "\n"
        encoded = line.encode("utf-8")
        parts.append(encoded)
        total += len(encoded)
    return b"".join(parts)[:size]


def _repeat_bytes(size: int, rng: random.Random) -> bytes:
    pattern = rng.randbytes(1024)
    repeats = size // len(pattern) + 1
    return (pattern * repeats)[:size]


def _mixed_bytes(size: int, rng: random.Random) -> bytes:
    half = size // 2
    return _text_bytes(half, rng) + rng.randbytes(size - half)


_KINDS = {
    "text": ("txt", _text_bytes),
    "random": ("bin", lambda size, rng: rng.randbytes(size)),
    "repeat": ("dat", _repeat_bytes),
    "mixed": ("dat", _mixed_bytes),
}


def build_dataset(out_dir: Path, size_mb: int, seed: int = 0, files: int = 4) -> dict[str, Any]:
    """Buat dataset sintetis berukuran `size_mb` MiB dan tulis metadata `dataset.json`."""
    if size_mb < 1:
        raise ValueError("size_mb minimal 1")
    if files < 1:
        raise ValueError("files minimal 1")

    out_dir.mkdir(parents=True, exist_ok=True)
    total_bytes = size_mb * constants.MIB
    base = total_bytes // files
    sizes = [base] * files
    sizes[-1] += total_bytes - base * files

    kind_names = list(_KINDS)
    rng = random.Random(seed)
    records: list[dict[str, Any]] = []
    for position, size in enumerate(sizes):
        kind = kind_names[position % len(kind_names)]
        extension, generator = _KINDS[kind]
        payload = generator(size, rng)
        name = f"{kind}_{position:02d}.{extension}"
        (out_dir / name).write_bytes(payload)
        records.append(
            {
                "name": name,
                "kind": kind,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )

    metadata: dict[str, Any] = {
        "seed": seed,
        "size_mb": size_mb,
        "files": records,
        "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    (out_dir / "dataset.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return metadata


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen CLI make_dataset."""
    parser = argparse.ArgumentParser(
        prog="pcomp.tools.make_dataset", description="Buat dataset sintetis deterministik"
    )
    parser.add_argument("--out", required=True, help="folder keluaran dataset")
    parser.add_argument("--size-mb", type=int, required=True, help="total ukuran dalam MiB")
    parser.add_argument("--seed", type=int, default=0, help="seed pembangkit data")
    parser.add_argument("--files", type=int, default=4, help="jumlah file")
    parser.add_argument(
        "--group-config",
        default=str(constants.DEFAULT_GROUP_CONFIG),
        help="path group.toml untuk banner",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan CLI make_dataset."""
    args = build_parser().parse_args(argv)
    try_print_banner(Path(args.group_config))
    metadata = build_dataset(Path(args.out), args.size_mb, args.seed, args.files)
    total = sum(item["size"] for item in metadata["files"])
    print(f"dataset      : {args.out}")
    print(f"files        : {len(metadata['files'])}")
    print(f"total_bytes  : {total}")
    print(f"seed         : {metadata['seed']}")
    print("DATASET OK")
    return constants.EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
