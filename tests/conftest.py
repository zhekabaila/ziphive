"""Fixture bersama untuk seluruh test ZipHive."""

from __future__ import annotations

import os
import socket
import subprocess
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

VALID_GROUP_TOML = """\
project_name = "ZipHive"
tema = "16 - Distributed Data Compression"
mata_kuliah = "Komputasi Paralel dan Sistem Terdistribusi"
institusi = "Informatika, Universitas Siliwangi"

[kelompok]
nama = "Kelompok Uji"

[[anggota]]
nama = "Ani Uji"
npm = "123456"
"""

PLACEHOLDER_GROUP_TOML = """\
project_name = "ZipHive"
tema = "16 - Distributed Data Compression"
mata_kuliah = "Komputasi Paralel dan Sistem Terdistribusi"
institusi = "Informatika, Universitas Siliwangi"

[kelompok]
nama = "<ISI NAMA KELOMPOK>"

[[anggota]]
nama = "<ISI NAMA ANGGOTA 1>"
npm = "<ISI NPM 1>"
"""


@pytest.fixture
def repo_root() -> Path:
    """Folder akar repo (berisi pyproject.toml)."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture
def valid_group_file(tmp_path: Path) -> Path:
    """File group.toml yang sudah terisi lengkap."""
    path = tmp_path / "group-valid.toml"
    path.write_text(VALID_GROUP_TOML, encoding="utf-8")
    return path


@pytest.fixture
def placeholder_group_file(tmp_path: Path) -> Path:
    """File group.toml yang masih berisi placeholder."""
    path = tmp_path / "group-placeholder.toml"
    path.write_text(PLACEHOLDER_GROUP_TOML, encoding="utf-8")
    return path


@pytest.fixture
def free_port() -> int:
    """Port TCP bebas di localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


@pytest.fixture
def synth_dataset(tmp_path: Path) -> Path:
    """Dataset sintetis 2 MiB untuk test jaringan."""
    from pcomp.tools.make_dataset import build_dataset

    target = tmp_path / "dataset"
    build_dataset(target, size_mb=2, seed=1)
    return target


class ModuleRunner:
    """Menjalankan modul `python -m ...` sebagai subprocess dan membersihkannya."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root
        self.processes: list[subprocess.Popen[str]] = []

    def start(self, module: str, *args: str) -> subprocess.Popen[str]:
        env = dict(os.environ)
        env["PYTHONPATH"] = str(self.repo_root / "src")
        proc: subprocess.Popen[str] = subprocess.Popen(
            [sys.executable, "-m", module, *args],
            cwd=self.repo_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        self.processes.append(proc)
        return proc

    def stop_all(self) -> None:
        for proc in self.processes:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)


@pytest.fixture
def module_runner(repo_root: Path) -> Iterator[ModuleRunner]:
    runner = ModuleRunner(repo_root)
    yield runner
    runner.stop_all()


@pytest.fixture
def start_master(module_runner: ModuleRunner) -> Callable[..., subprocess.Popen[str]]:
    """Factory `python -m pcomp.master ...`."""

    def _start(*args: str) -> subprocess.Popen[str]:
        return module_runner.start("pcomp.master", *args)

    return _start


@pytest.fixture
def start_worker(module_runner: ModuleRunner) -> Callable[..., subprocess.Popen[str]]:
    """Factory `python -m pcomp.worker ...`."""

    def _start(*args: str) -> subprocess.Popen[str]:
        return module_runner.start("pcomp.worker", *args)

    return _start


@pytest.fixture
def events_of() -> Callable[[Path], list[dict]]:
    """Baca events.jsonl dari folder run."""
    from pcomp.metrics.events import read_events

    def _read(run_dir: Path) -> list[dict]:
        return read_events(run_dir / "events.jsonl")

    return _read
