"""UT-NODE-01..04: pemeriksaan kesiapan node (PLAN.md P8-T1)."""

from __future__ import annotations

from collections.abc import Callable
from types import ModuleType

import pytest

Loader = Callable[[str], ModuleType]


@pytest.fixture
def node(load_script: Loader) -> ModuleType:
    return load_script("check_node.py")


def test_parse_master_address(node: ModuleType) -> None:
    """UT-NODE-01: alamat Master `host:port` divalidasi."""
    assert node.parse_master("10.0.0.5:5050") == ("10.0.0.5", 5050)
    assert node.parse_master(" master.lab:6000 ") == ("master.lab", 6000)

    for bad in ("10.0.0.5", "10.0.0.5:", ":5050", "10.0.0.5:0", "10.0.0.5:70000", "10.0.0.5:abc"):
        with pytest.raises(ValueError):
            node.parse_master(bad)


def test_check_python_and_cores(node: ModuleType) -> None:
    """UT-NODE-02: versi Python minimal dan jumlah core dilaporkan."""
    assert node.check_python((3, 10, 12)).ok is False
    assert "3.11" in node.check_python((3, 10, 12)).detail
    assert node.check_python((3, 11, 0)).ok is True
    assert node.check_python((3, 14, 4)).ok is True

    cores = node.check_cores(lambda: 8)
    assert cores.ok is True
    assert "8" in cores.detail
    assert node.check_cores(lambda: None).ok is False


def test_check_master_with_injected_connect(node: ModuleType) -> None:
    """UT-NODE-03: cek koneksi Master memakai fungsi connect yang disuntikkan."""
    calls: list[tuple[str, int, float]] = []

    def ok_connect(host: str, port: int, timeout: float) -> None:
        calls.append((host, port, timeout))

    result = node.check_master("10.0.0.5", 5050, connect=ok_connect, timeout=2.5)
    assert result.ok is True
    assert "10.0.0.5:5050" in result.detail
    assert calls == [("10.0.0.5", 5050, 2.5)]

    def refused(host: str, port: int, timeout: float) -> None:
        raise OSError("connection refused")

    failed = node.check_master("10.0.0.5", 5050, connect=refused)
    assert failed.ok is False
    assert "connection refused" in failed.detail


def test_report_and_main_exit_codes(node: ModuleType, free_port: int) -> None:
    """UT-NODE-04: laporan ringkas dan exit code `main`."""
    ok_result = node.CheckResult(name="python", ok=True, detail="3.14.4")
    bad_result = node.CheckResult(name="psutil", ok=False, detail="tidak terpasang")
    assert "CHECK NODE OK" in node.format_report([ok_result])
    assert "CHECK NODE GAGAL" in node.format_report([ok_result, bad_result])
    assert node.format_report([ok_result]).splitlines()[0].startswith("OK")

    assert node.main([]) == 0
    assert node.main(["--master", f"127.0.0.1:{free_port}", "--timeout", "1"]) == 1
    assert node.main(["--master", "tanpa-port"]) == 2


def test_run_checks_has_local_rows(node: ModuleType) -> None:
    """UT-NODE-04b: pemeriksaan lokal memuat python, psutil, core, RAM, protokol."""
    results = node.run_checks()
    names = {item.name for item in results}
    assert {"python", "psutil", "core", "ram", "protokol", "paket"} <= names
    assert all(isinstance(item.ok, bool) for item in results)
