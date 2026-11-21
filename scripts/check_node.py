"""Pemeriksaan kesiapan satu node ZipHive (PLAN.md P8-T1).

Memeriksa versi Python, ketersediaan psutil, jumlah core, RAM, versi protokol yang
dipakai paket `pcomp`, dan (bila diminta) keterjangkauan port Master. Skrip tidak
mengirim pesan REGISTER agar tidak mengganggu state Master: ketidakcocokan versi
terdeteksi saat Worker mendaftar (PROTOCOL.md, risiko R2).
"""

from __future__ import annotations

import argparse
import importlib
import json
import socket
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    # Memungkinkan skrip dipakai langsung dari hasil `git clone` tanpa `pip install -e .`.
    sys.path.insert(0, str(SRC_DIR))

MIN_PYTHON = (3, 11)
DEFAULT_MASTER_PORT = 5050
DEFAULT_TIMEOUT = 5.0
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2

ConnectFn = Callable[[str, int, float], None]


@dataclass(frozen=True)
class CheckResult:
    """Hasil satu pemeriksaan."""

    name: str
    ok: bool
    detail: str

    @property
    def label(self) -> str:
        """Teks status untuk laporan."""
        return "OK" if self.ok else "FAIL"


def parse_master(text: str) -> tuple[str, int]:
    """Ubah `host:port` menjadi pasangan host dan port yang tervalidasi."""
    value = text.strip()
    host, separator, port_text = value.rpartition(":")
    host = host.strip()
    if not separator or not host:
        raise ValueError(f"alamat Master harus berbentuk host:port, diterima: {text!r}")
    try:
        port = int(port_text.strip())
    except ValueError as exc:
        raise ValueError(f"port bukan angka: {port_text!r}") from exc
    if not 1 <= port <= 65535:
        raise ValueError(f"port di luar rentang 1-65535: {port}")
    return host, port


def check_python(version_info: Sequence[int] = sys.version_info) -> CheckResult:
    """Pastikan versi Python memenuhi `requires-python` proyek."""
    version = tuple(int(part) for part in tuple(version_info)[:3])
    text = ".".join(str(part) for part in version)
    need = f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}"
    if version[:2] >= MIN_PYTHON:
        return CheckResult("python", True, f"{text} (>= {need})")
    return CheckResult("python", False, f"{text} (butuh >= {need})")


def check_psutil(module: Any | None) -> CheckResult:
    """Laporkan versi psutil atau kegagalan impor."""
    if module is None:
        return CheckResult("psutil", False, "tidak terpasang (pip install -r requirements.txt)")
    version = getattr(module, "__version__", "tidak diketahui")
    return CheckResult("psutil", True, str(version))


def check_package() -> CheckResult:
    """Laporkan versi paket `pcomp` yang terpasang atau dapat diimpor."""
    try:
        from pcomp import constants
    except ImportError:
        return CheckResult("paket", False, "pcomp tidak dapat diimpor (pip install -e .)")
    return CheckResult("paket", True, f"pcomp {constants.__version__}")


def check_protocol() -> CheckResult:
    """Laporkan PROTOCOL_VERSION agar versi antar node mudah dibandingkan."""
    try:
        from pcomp import constants
    except ImportError:
        return CheckResult("protokol", False, "tidak diketahui (pcomp tidak dapat diimpor)")
    return CheckResult("protokol", True, f"PROTOCOL_VERSION={constants.PROTOCOL_VERSION}")


def check_cores(count: Callable[[], int | None]) -> CheckResult:
    """Laporkan jumlah core logis yang terbaca."""
    value = count()
    if not value or value < 1:
        return CheckResult("core", False, "jumlah core tidak terbaca")
    return CheckResult("core", True, f"{value} core logis")


def check_memory(virtual_memory: Callable[[], Any]) -> CheckResult:
    """Laporkan kapasitas RAM total dalam GiB."""
    info = virtual_memory()
    total = float(getattr(info, "total", 0) or 0)
    if total <= 0:
        return CheckResult("ram", False, "kapasitas RAM tidak terbaca")
    return CheckResult("ram", True, f"{total / (1024**3):.1f} GiB")


def default_connect(host: str, port: int, timeout: float) -> None:
    """Buka koneksi TCP lalu tutup; gagal dengan OSError bila tidak terjangkau."""
    with socket.create_connection((host, port), timeout=timeout):
        return None


def check_master(
    host: str, port: int, *, connect: ConnectFn = default_connect, timeout: float = DEFAULT_TIMEOUT
) -> CheckResult:
    """Uji keterjangkauan port Master tanpa mengirim pesan protokol."""
    address = f"{host}:{port}"
    try:
        connect(host, port, timeout)
    except OSError as exc:
        return CheckResult("master", False, f"{address} tidak terjangkau: {exc}")
    return CheckResult("master", True, f"{address} menerima koneksi TCP")


def _load_psutil() -> Any | None:
    try:
        return importlib.import_module("psutil")
    except ImportError:
        return None


def run_checks(
    master: tuple[str, int] | None = None,
    *,
    connect: ConnectFn = default_connect,
    timeout: float = DEFAULT_TIMEOUT,
    psutil_module: Any | None = None,
) -> list[CheckResult]:
    """Jalankan seluruh pemeriksaan lokal dan, bila diminta, pemeriksaan Master."""
    module = psutil_module if psutil_module is not None else _load_psutil()
    results = [
        check_python(),
        check_psutil(module),
        check_package(),
        check_protocol(),
        check_cores(lambda: int(getattr(module, "cpu_count", lambda: 0)()) if module else 0),
        check_memory(lambda: module.virtual_memory() if module else None),
    ]
    if master is not None:
        results.append(check_master(master[0], master[1], connect=connect, timeout=timeout))
    return results


def format_report(results: Sequence[CheckResult]) -> str:
    """Susun baris laporan dan kesimpulan akhir."""
    lines = [f"{item.label} {item.name}: {item.detail}" for item in results]
    passed = all(item.ok for item in results)
    lines.append("CHECK NODE OK" if passed else "CHECK NODE GAGAL")
    return "\n".join(lines)


def read_default_master() -> str:
    """Ambil alamat Master dari `config/worker.toml` sebagai nilai bawaan."""
    from pcomp.config import load_toml

    data = load_toml(REPO_ROOT / "config" / "worker.toml")
    return str(data.get("master", f"127.0.0.1:{DEFAULT_MASTER_PORT}"))


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen `check_node.py`."""
    parser = argparse.ArgumentParser(
        prog="check_node.py", description="Periksa kesiapan node ZipHive"
    )
    parser.add_argument("--master", default=None, help="alamat Master host:port")
    parser.add_argument(
        "--ping-master",
        action="store_true",
        help="hanya uji koneksi ke Master (alamat dari --master atau config/worker.toml)",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT, help="batas waktu koneksi (detik)"
    )
    parser.add_argument("--json", action="store_true", help="cetak hasil sebagai JSON")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Jalankan pemeriksaan dan kembalikan exit code 0 (lulus) atau 1 (gagal)."""
    args = build_parser().parse_args(argv)
    try:
        if args.master is not None:
            master: tuple[str, int] | None = parse_master(args.master)
        elif args.ping_master:
            master = parse_master(read_default_master())
        else:
            master = None
    except ValueError as exc:
        print(f"CHECK NODE GAGAL: {exc}", file=sys.stderr)
        return EXIT_USAGE

    results = run_checks(master, timeout=args.timeout)
    if args.ping_master:
        results = [item for item in results if item.name == "master"]

    if args.json:
        print(json.dumps([item.__dict__ for item in results], ensure_ascii=False, indent=2))
    else:
        print(format_report(results))
    return EXIT_OK if all(item.ok for item in results) else EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
