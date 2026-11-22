"""Helper lintas platform untuk launcher ZipHive di laptop fisik (PLAN.md P11-T5).

Modul ini tidak menjalankan proses apa pun: seluruh fungsi murni atau hanya membaca dan
menulis berkas kecil, sehingga mudah diuji unit. Dipakai oleh `bootstrap_node.py`,
`start_worker.py`, dan `start_master.py` pada macOS, Windows, dan Linux.
"""

from __future__ import annotations

import os
import socket
import sys
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

MIN_PYTHON = (3, 11)
DEFAULT_MASTER_PORT = 5050
DEFAULT_WORKER_ID = "w1"
DEFAULT_PROCS = 1
DEFAULT_THROTTLE = 0.0
LOCAL_CONFIG_NAME = "worker.local.toml"

VERSION_HINT = (
    "Pasang Python 3.11 atau lebih baru (python.org). "
    "macOS: jangan pakai python3 bawaan Xcode Command Line Tools (3.9). "
    "Windows: centang 'Add python.exe to PATH' saat memasang."
)


def is_windows(os_name: str | None = None) -> bool:
    """True bila sistem yang diperiksa adalah Windows."""
    name = os_name if os_name is not None else sys.platform
    return name.startswith("win")


def venv_dir(root: Path) -> Path:
    """Folder virtual environment di dalam folder proyek."""
    return root / ".venv"


def venv_python(root: Path, os_name: str | None = None) -> Path:
    """Path interpreter Python di dalam `.venv` sesuai sistem operasi."""
    if is_windows(os_name):
        return venv_dir(root) / "Scripts" / "python.exe"
    return venv_dir(root) / "bin" / "python"


def venv_ready(root: Path, os_name: str | None = None) -> bool:
    """True bila interpreter `.venv` sudah ada."""
    return venv_python(root, os_name).is_file()


def version_tuple(info: Sequence[int]) -> tuple[int, int]:
    """Ambil (major, minor) dari `sys.version_info` atau tuple versi apa pun."""
    if len(info) < 2:
        raise ValueError("versi Python minimal memuat major dan minor")
    return int(info[0]), int(info[1])


def version_ok(info: Sequence[int], minimum: tuple[int, int] = MIN_PYTHON) -> bool:
    """True bila versi Python memenuhi batas minimum proyek."""
    return version_tuple(info) >= minimum


def describe_version(info: Sequence[int]) -> str:
    """Teks `major.minor.patch` untuk laporan konsol."""
    parts = [str(int(part)) for part in info[:3]]
    return ".".join(parts)


def package_env(root: Path, base: Mapping[str, str] | None = None) -> dict[str, str]:
    """Environment dengan `PYTHONPATH` menunjuk `src/` agar paket dipakai dari repo."""
    env = dict(base if base is not None else os.environ)
    src = str(root / "src")
    existing = env.get("PYTHONPATH", "")
    separator = ";" if is_windows() else ":"
    env["PYTHONPATH"] = src + (separator + existing if existing else "")
    env["PYTHONUNBUFFERED"] = "1"
    return env


def local_ip() -> str:
    """Perkiraan IP LAN laptop ini; 127.0.0.1 bila tidak ada jaringan."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.settimeout(0.5)
        # Alamat tujuan tidak dikirimi paket; hanya dipakai untuk memilih rute keluar.
        probe.connect(("8.8.8.8", 80))
        address = probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()
    return str(address)


def master_address(host: str, port: int = DEFAULT_MASTER_PORT) -> str:
    """Gabungkan host dan port menjadi `host:port`."""
    return f"{host}:{port}"


def parse_master_address(value: str) -> tuple[str, int]:
    """Urai `host:port`; ValueError bila bentuknya salah."""
    host, separator, raw_port = value.rpartition(":")
    if not separator or not host or not raw_port:
        raise ValueError(f"alamat Master harus host:port, diterima '{value}'")
    try:
        port = int(raw_port)
    except ValueError as exc:
        raise ValueError(f"port tidak valid pada '{value}'") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"port {port} di luar rentang 1-65535")
    return host, port


def worker_command(
    python: Path | str,
    master: str,
    worker_id: str,
    procs: int = DEFAULT_PROCS,
    throttle: float = DEFAULT_THROTTLE,
    config: Path | None = None,
) -> list[str]:
    """Perintah `python -m pcomp.worker` untuk satu laptop Worker."""
    command = [
        str(python),
        "-m",
        "pcomp.worker",
        "--master",
        master,
        "--id",
        worker_id,
        "--procs",
        str(procs),
    ]
    if throttle > 0:
        command += ["--throttle", str(throttle)]
    if config is not None:
        command += ["--config", str(config)]
    return command


def master_command(
    python: Path | str,
    input_dir: str | Path,
    out_dir: str | Path,
    expect_workers: int,
    *,
    host: str = "0.0.0.0",
    port: int = DEFAULT_MASTER_PORT,
    scheduler: str = "dynamic",
    algo: str = "lzma",
    level: int = 6,
    chunk_mb: int = 4,
    repeat: int = 1,
    inject_kills: int = 0,
    inject_kill_fraction: float = 0.5,
) -> list[str]:
    """Perintah `python -m pcomp.master` untuk laptop Master."""
    command = [
        str(python),
        "-m",
        "pcomp.master",
        "--host",
        host,
        "--port",
        str(port),
        "--input",
        str(input_dir),
        "--out",
        str(out_dir),
        "--expect-workers",
        str(expect_workers),
        "--scheduler",
        scheduler,
        "--algo",
        algo,
        "--level",
        str(level),
        "--chunk-mb",
        str(chunk_mb),
        "--repeat",
        str(repeat),
    ]
    if inject_kills > 0:
        command += [
            "--inject-kills",
            str(inject_kills),
            "--inject-kill-fraction",
            str(inject_kill_fraction),
        ]
    return command


def bootstrap_commands(root: Path, python: str, os_name: str | None = None) -> list[list[str]]:
    """Perintah pembuatan venv dan pemasangan paket (tanpa menyentuh Python sistem)."""
    return [
        [python, "-m", "venv", str(venv_dir(root))],
        [str(venv_python(root, os_name)), "-m", "pip", "install", "-e", str(root)],
    ]


def format_command(command: Sequence[str]) -> str:
    """Teks perintah yang dapat disalin, dengan tanda kutip bila ada spasi."""
    parts: list[str] = []
    for item in command:
        text = str(item)
        parts.append(f'"{text}"' if " " in text else text)
    return " ".join(parts)


def local_config_path(root: Path) -> Path:
    """Lokasi berkas ingatan launcher Worker."""
    return root / "config" / LOCAL_CONFIG_NAME


def write_worker_local_config(
    path: Path,
    master: str,
    worker_id: str,
    procs: int = DEFAULT_PROCS,
    throttle: float = DEFAULT_THROTTLE,
) -> Path:
    """Simpan pilihan operator agar tidak perlu mengetik ulang setiap run."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "# Dibuat otomatis oleh scripts/start_worker.py.\n"
        "# Ubah di sini atau jalankan ulang launcher dengan --master/--id.\n"
        f'master = "{master}"\n'
        f'worker_id = "{worker_id}"\n'
        f"procs = {int(procs)}\n"
        f"throttle = {float(throttle)}\n"
    )
    path.write_text(text, encoding="utf-8")
    return path


def read_worker_local_config(path: Path) -> dict[str, Any]:
    """Baca berkas ingatan launcher; dict kosong bila belum ada."""
    if not path.is_file():
        return {}
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    return dict(data)
