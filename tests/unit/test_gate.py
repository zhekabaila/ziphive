"""UT-BOOT-05: fungsi parsing dan pemeriksaan di scripts/gate.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType

import pytest

PLAN_SAMPLE = """\
# PLAN.md

CURRENT PHASE: 3

## Status fase
| Fase | Nama | Ukuran | Pelaku | Status |
|---|---|---|---|---|
| 0 | Bootstrap repo dan tooling | S | Agent | DONE |
| 1 | Protokol dan infrastruktur inti | M | Agent | DONE |
| 2 | Mesin kompresi | M | Agent | DONE |
| 3 | Local parallel | S | Agent | IN PROGRESS |
"""


def load_gate_module(repo_root: Path) -> ModuleType:
    gate_path = repo_root / "scripts" / "gate.py"
    spec = importlib.util.spec_from_file_location("gate_module", gate_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # dataclass butuh modul terdaftar di sys.modules saat dieksekusi.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def gate(repo_root: Path) -> ModuleType:
    return load_gate_module(repo_root)


def test_parse_current_phase(gate: ModuleType) -> None:
    assert gate.parse_current_phase(PLAN_SAMPLE) == 3


def test_parse_current_phase_missing(gate: ModuleType) -> None:
    with pytest.raises(ValueError):
        gate.parse_current_phase("# tidak ada penanda fase")


def test_parse_phase_status(gate: ModuleType) -> None:
    assert gate.parse_phase_status(PLAN_SAMPLE, 3) == "IN PROGRESS"
    assert gate.parse_phase_status(PLAN_SAMPLE, 0) == "DONE"


def test_parse_phase_status_missing(gate: ModuleType) -> None:
    with pytest.raises(ValueError):
        gate.parse_phase_status(PLAN_SAMPLE, 9)


def test_resolve_gate_phase_active(gate: ModuleType) -> None:
    assert gate.resolve_gate_phase(PLAN_SAMPLE) == 3


def test_resolve_gate_phase_after_shift(gate: ModuleType) -> None:
    shifted = PLAN_SAMPLE.replace("CURRENT PHASE: 3", "CURRENT PHASE: 4")
    shifted = shifted.replace(
        "| 3 | Local parallel | S | Agent | IN PROGRESS |",
        "| 3 | Local parallel | S | Agent | DONE |\n| 4 | Master-Worker inti | L | Agent | TODO |",
    )
    assert gate.resolve_gate_phase(shifted) == 3


def test_is_forbidden_repo_path(gate: ModuleType) -> None:
    assert gate.is_forbidden_repo_path("data/silesia/dickens") is True
    assert gate.is_forbidden_repo_path("output/run1/manifest.json") is True
    assert gate.is_forbidden_repo_path("src/pcomp/constants.py") is False


def test_find_oversized_files(gate: ModuleType, tmp_path: Path) -> None:
    small = tmp_path / "kecil.bin"
    small.write_bytes(b"x" * 10)
    big = tmp_path / "besar.bin"
    big.write_bytes(b"x" * 64)
    found = gate.find_oversized_files([small, big], limit_bytes=32)
    assert found == [big]
