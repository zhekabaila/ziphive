"""Manifest hasil kompresi: tulis, baca, rekonstruksi, verifikasi (PLAN.md P2-T4)."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pcomp.compressor import decompress, file_extension
from pcomp.tasks import Task

MANIFEST_VERSION = 1


class ManifestError(ValueError):
    """Isi manifest tidak valid atau tidak lengkap."""


@dataclass(frozen=True)
class ManifestEntry:
    """Satu chunk pada manifest."""

    task_id: int
    file: str
    index: int
    offset: int
    length: int
    sha256: str
    output: str
    comp_size: int
    copy: int = 0


@dataclass(frozen=True)
class FailedEntry:
    """Satu task dead-letter pada manifest (P6-T2)."""

    task_id: int
    file: str
    index: int
    offset: int
    length: int
    attempts: int
    reason: str


@dataclass(frozen=True)
class Manifest:
    """Seluruh isi manifest.json."""

    version: int
    algo: str
    level: int
    chunk_mb: int
    repeat: int
    total_orig_bytes: int
    total_comp_bytes: int
    entries: tuple[ManifestEntry, ...]
    failed: tuple[FailedEntry, ...] = ()

    @property
    def ratio(self) -> float:
        """Rasio kompresi = ukuran asli / ukuran hasil (0.0 bila hasil kosong)."""
        if self.total_comp_bytes == 0:
            return 0.0
        return self.total_orig_bytes / self.total_comp_bytes


@dataclass(frozen=True)
class EntryVerification:
    """Hasil verifikasi satu chunk."""

    entry: ManifestEntry
    ok: bool
    reason: str = ""


def chunk_output_name(file: str, index: int, algo: str, *, copy: int, repeat: int) -> str:
    """Nama file chunk hasil. Salinan `--repeat` diberi folder rN agar tidak bertabrakan."""
    name = f"{file}.{index:04d}.{file_extension(algo)}"
    if repeat > 1:
        return f"chunks/r{copy}/{name}"
    return f"chunks/{name}"


def make_entry(
    task: Task, *, sha256: str, length: int, comp_size: int, output: str, copy: int
) -> ManifestEntry:
    """Susun entri manifest untuk satu task yang selesai dikompres."""
    return ManifestEntry(
        task_id=task.task_id,
        file=task.file,
        index=task.index,
        offset=task.offset,
        length=length,
        sha256=sha256,
        output=output,
        comp_size=comp_size,
        copy=copy,
    )


def build_manifest(
    *,
    algo: str,
    level: int,
    chunk_mb: int,
    repeat: int,
    entries: Sequence[ManifestEntry],
    failed: Sequence[FailedEntry] = (),
) -> Manifest:
    """Susun manifest dan hitung total ukuran."""
    return Manifest(
        version=MANIFEST_VERSION,
        algo=algo,
        level=level,
        chunk_mb=chunk_mb,
        repeat=repeat,
        total_orig_bytes=sum(entry.length for entry in entries),
        total_comp_bytes=sum(entry.comp_size for entry in entries),
        entries=tuple(entries),
        failed=tuple(failed),
    )


def to_dict(manifest: Manifest) -> dict[str, Any]:
    """Ubah manifest menjadi struktur siap JSON."""
    return {
        "version": manifest.version,
        "algo": manifest.algo,
        "level": manifest.level,
        "chunk_mb": manifest.chunk_mb,
        "repeat": manifest.repeat,
        "total_orig_bytes": manifest.total_orig_bytes,
        "total_comp_bytes": manifest.total_comp_bytes,
        "entries": [
            {
                "task_id": entry.task_id,
                "file": entry.file,
                "index": entry.index,
                "offset": entry.offset,
                "length": entry.length,
                "sha256": entry.sha256,
                "output": entry.output,
                "comp_size": entry.comp_size,
                "copy": entry.copy,
            }
            for entry in manifest.entries
        ],
        "failed": [
            {
                "task_id": entry.task_id,
                "file": entry.file,
                "index": entry.index,
                "offset": entry.offset,
                "length": entry.length,
                "attempts": entry.attempts,
                "reason": entry.reason,
            }
            for entry in manifest.failed
        ],
    }


def _require(data: dict[str, Any], key: str, kind: type) -> Any:
    if key not in data:
        raise ManifestError(f"field '{key}' wajib ada di manifest")
    value = data[key]
    if kind is int:
        if not isinstance(value, int) or isinstance(value, bool):
            raise ManifestError(f"field '{key}' wajib int")
    elif not isinstance(value, kind):
        raise ManifestError(f"field '{key}' bertipe {type(value).__name__}, wajib {kind.__name__}")
    return value


def from_dict(data: dict[str, Any]) -> Manifest:
    """Bangun manifest dari struktur JSON dan validasi field wajib."""
    raw_entries = data.get("entries")
    if not isinstance(raw_entries, list):
        raise ManifestError("field 'entries' wajib berupa list")
    entries: list[ManifestEntry] = []
    for raw in raw_entries:
        if not isinstance(raw, dict):
            raise ManifestError("setiap entri manifest wajib berupa objek")
        entries.append(
            ManifestEntry(
                task_id=_require(raw, "task_id", int),
                file=_require(raw, "file", str),
                index=_require(raw, "index", int),
                offset=_require(raw, "offset", int),
                length=_require(raw, "length", int),
                sha256=_require(raw, "sha256", str),
                output=_require(raw, "output", str),
                comp_size=_require(raw, "comp_size", int),
                copy=_require(raw, "copy", int),
            )
        )
    raw_failed = data.get("failed", [])
    if not isinstance(raw_failed, list):
        raise ManifestError("field 'failed' wajib berupa list")
    failed: list[FailedEntry] = []
    for raw in raw_failed:
        if not isinstance(raw, dict):
            raise ManifestError("setiap entri 'failed' wajib berupa objek")
        failed.append(
            FailedEntry(
                task_id=_require(raw, "task_id", int),
                file=_require(raw, "file", str),
                index=_require(raw, "index", int),
                offset=_require(raw, "offset", int),
                length=_require(raw, "length", int),
                attempts=_require(raw, "attempts", int),
                reason=_require(raw, "reason", str),
            )
        )
    return Manifest(
        version=_require(data, "version", int),
        algo=_require(data, "algo", str),
        level=_require(data, "level", int),
        chunk_mb=_require(data, "chunk_mb", int),
        repeat=_require(data, "repeat", int),
        total_orig_bytes=_require(data, "total_orig_bytes", int),
        total_comp_bytes=_require(data, "total_comp_bytes", int),
        entries=tuple(entries),
        failed=tuple(failed),
    )


def write_manifest(path: Path, manifest: Manifest) -> None:
    """Tulis manifest.json."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(to_dict(manifest), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def read_manifest(path: Path) -> Manifest:
    """Baca manifest.json; FileNotFoundError bila tidak ada, ManifestError bila rusak."""
    if not path.is_file():
        raise FileNotFoundError(f"manifest tidak ditemukan: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ManifestError(f"manifest bukan JSON valid: {exc}") from exc
    if not isinstance(data, dict):
        raise ManifestError("manifest wajib berupa objek JSON")
    return from_dict(data)


def reconstruct_file(manifest: Manifest, out_dir: Path, file: str, copy: int = 0) -> bytes:
    """Gabungkan kembali seluruh chunk satu file menjadi data asli."""
    selected = sorted(
        (entry for entry in manifest.entries if entry.file == file and entry.copy == copy),
        key=lambda entry: entry.index,
    )
    if not selected:
        raise ManifestError(f"tidak ada chunk untuk file '{file}' salinan {copy}")
    parts = [
        decompress(manifest.algo, manifest.level, (out_dir / entry.output).read_bytes())
        for entry in selected
    ]
    return b"".join(parts)


def verify_entries(manifest: Manifest, out_dir: Path) -> list[EntryVerification]:
    """Dekompresi setiap chunk dan bandingkan ukuran serta sha256 dengan manifest."""
    results: list[EntryVerification] = []
    for entry in manifest.entries:
        path = out_dir / entry.output
        if not path.is_file():
            results.append(EntryVerification(entry, False, "file chunk tidak ada"))
            continue
        try:
            raw = decompress(manifest.algo, manifest.level, path.read_bytes())
        except Exception as exc:  # noqa: BLE001 - penyebab apa pun dianggap chunk rusak
            results.append(EntryVerification(entry, False, f"gagal dekompresi: {exc}"))
            continue
        if len(raw) != entry.length:
            results.append(EntryVerification(entry, False, f"ukuran {len(raw)} != {entry.length}"))
            continue
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry.sha256:
            results.append(EntryVerification(entry, False, "sha256 tidak cocok"))
            continue
        results.append(EntryVerification(entry, True))
    return results
