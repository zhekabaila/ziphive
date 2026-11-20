"""Penulisan hasil kompresi oleh Master (PLAN.md P4-T2)."""

from __future__ import annotations

import json
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pcomp.chunker import copy_index
from pcomp.manifest import (
    Manifest,
    ManifestEntry,
    build_manifest,
    chunk_output_name,
    make_entry,
    write_manifest,
)
from pcomp.tasks import Task


class Collector:
    """Kumpulkan entri manifest dan tulis chunk, manifest, serta metrics."""

    def __init__(
        self,
        out_dir: Path,
        *,
        algo: str,
        level: int,
        chunk_mb: int,
        repeat: int,
        total_tasks: int,
    ) -> None:
        self.out_dir = out_dir
        self.algo = algo
        self.level = level
        self.chunk_mb = chunk_mb
        self.repeat = repeat
        self.total_tasks = total_tasks
        self._entries: list[ManifestEntry] = []
        self._lock = threading.Lock()
        out_dir.mkdir(parents=True, exist_ok=True)

    def _copy_of(self, task_id: int) -> int:
        """Nomor salinan `--repeat` untuk task_id ini."""
        if self.repeat <= 1:
            return 0
        per_copy = self.total_tasks // self.repeat
        return copy_index(task_id, per_copy) if per_copy > 0 else 0

    def write_chunk(self, task: Task, data: bytes, *, sha256: str, comp_size: int) -> ManifestEntry:
        """Tulis satu chunk hasil dan catat entrinya pada manifest."""
        copy = self._copy_of(task.task_id)
        relative = chunk_output_name(
            task.file, task.index, self.algo, copy=copy, repeat=self.repeat
        )
        target = self.out_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        entry = make_entry(
            task,
            sha256=sha256,
            length=task.length,
            comp_size=comp_size,
            output=relative,
            copy=copy,
        )
        with self._lock:
            self._entries.append(entry)
        return entry

    def manifest(self) -> Manifest:
        """Manifest dari seluruh entri yang sudah ditulis, urut task_id."""
        with self._lock:
            entries = sorted(self._entries, key=lambda item: item.task_id)
        return build_manifest(
            algo=self.algo,
            level=self.level,
            chunk_mb=self.chunk_mb,
            repeat=self.repeat,
            entries=entries,
        )

    def write_manifest(self) -> Manifest:
        """Tulis `manifest.json` dan kembalikan isinya."""
        manifest = self.manifest()
        write_manifest(self.out_dir / "manifest.json", manifest)
        return manifest

    def write_metrics(self, metrics: Mapping[str, Any]) -> None:
        """Tulis `metrics.json`."""
        (self.out_dir / "metrics.json").write_text(
            json.dumps(dict(metrics), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
