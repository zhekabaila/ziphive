"""Verification Gate G1-G9 proyek ZipHive (SDLC.md bagian 4).

Dijalankan dari akar repo: `python scripts/gate.py` atau `python scripts/gate.py --quick`.
Ringkasan hasil ditulis ke reports/gate-latest.txt.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = REPO_ROOT / "PLAN.md"
CHANGELOG_PATH = REPO_ROOT / "CHANGELOG.md"
PHASE_LOG_DIR = REPO_ROOT / "docs" / "phase-logs"
REPORT_PATH = REPO_ROOT / "reports" / "gate-latest.txt"

MAX_FILE_BYTES = 5 * 1024 * 1024
FORBIDDEN_PREFIXES = ("data/", "output/")
FLAKY_GATE_MIN_PHASE = 4
COMMAND_TIMEOUT_SEC = 1800

# Smoke test per fase, disalin dari bagian "Smoke" PLAN.md fase terkait.
SMOKE_COMMANDS: dict[int, list[list[str]]] = {
    0: [[sys.executable, "-m", "pcomp", "--version"]],
    1: [[sys.executable, "-m", "pytest", "-m", "integration", "-k", "echo", "-q"]],
    2: [
        [
            sys.executable,
            "-m",
            "pcomp.tools.make_dataset",
            "--out",
            "data/synth",
            "--size-mb",
            "20",
        ],
        [sys.executable, "-m", "pcomp.sequential", "--input", "data/synth", "--out", "output/seq"],
        [
            sys.executable,
            "-m",
            "pcomp.tools.verify",
            "--manifest",
            "output/seq/manifest.json",
        ],
    ],
    3: [
        [
            sys.executable,
            "-m",
            "pcomp.tools.make_dataset",
            "--out",
            "data/synth",
            "--size-mb",
            "20",
        ],
        [sys.executable, "-m", "pcomp.sequential", "--input", "data/synth", "--out", "output/seq"],
        [sys.executable, "-m", "pcomp.tools.verify", "--manifest", "output/seq/manifest.json"],
        [
            sys.executable,
            "-m",
            "pcomp.local_parallel",
            "--input",
            "data/synth",
            "--out",
            "output/local",
            "--procs",
            "4",
        ],
        [sys.executable, "-m", "pcomp.tools.verify", "--manifest", "output/local/manifest.json"],
    ],
    4: [[sys.executable, "scripts/e2e_local.py", "--workers", "3"]],
    5: [
        [
            sys.executable,
            "scripts/e2e_local.py",
            "--workers",
            "2",
            "--compare",
            "--algo",
            "gzip",
            "--size-mb",
            "4",
            "--chunk-mb",
            "1",
            "--repeat",
            "2",
            "--worker-procs",
            "1",
            "--slow-throttle",
            "0.4",
        ]
    ],
    6: [
        [
            sys.executable,
            "scripts/e2e_local.py",
            "--workers",
            "2",
            "--algo",
            "gzip",
            "--size-mb",
            "4",
            "--chunk-mb",
            "1",
            "--repeat",
            "2",
            "--worker-procs",
            "1",
            "--fail-after-tasks",
            "3",
            "--heartbeat-interval",
            "0.2",
            "--heartbeat-timeout",
            "1.0",
        ]
    ],
    7: [
        [
            sys.executable,
            "-m",
            "pcomp.bench.runner",
            "--exp",
            "E6",
            "--local",
            "--workers",
            "1,2",
            "--reps",
            "2",
            "--algo",
            "sim",
        ]
    ],
    8: [[sys.executable, "-m", "pytest", "-m", "slow", "-q"]],
    9: [[sys.executable, "-m", "pcomp.tools.validate_results", "results/raw"]],
}

# Keluaran yang wajib muncul pada smoke fase tertentu.
SMOKE_EXPECTED: dict[int, list[str]] = {
    2: ["VERIFY OK"],
    3: ["SEQUENTIAL OK", "LOCAL OK"],
    4: ["E2E OK"],
    5: ["LB COMPARE OK"],
    6: ["E2E OK", "worker_dead"],
    7: ["BENCH OK"],
    8: ["1 passed"],
    9: ["RESULTS VALID"],
}

PHASE_LOG_REQUIRED_HEADINGS = (
    "## 1. Tujuan",
    "## 2. Ringkasan hasil",
    "## 3. Task",
    "## 4. File yang berubah",
    "## 5. Test",
    "## 6. Hasil Verification Gate",
    "## 7. Deviasi dari rencana",
    "## 8. Masalah ditemukan dan solusi",
    "## 9. Back-fix (bug fase lama)",
    "## 10. Keterbatasan dan utang teknis",
    "## 11. Catatan serah-terima ke fase berikutnya",
    "## 12. Commit",
)

PHASE_LOG_UNFINISHED_MARKERS = ("(selesai di akhir fase)", "(diisi pada akhir fase)", "<x>%")


@dataclass(frozen=True)
class GateResult:
    """Hasil satu gate."""

    gate_id: str
    name: str
    passed: bool
    detail: str
    skipped: bool = False

    @property
    def label(self) -> str:
        if self.skipped:
            return "SKIP"
        return "PASS" if self.passed else "FAIL"


# ---------------------------------------------------------------------------
# Fungsi parsing murni (diuji unit test UT-BOOT-05)
# ---------------------------------------------------------------------------


def parse_current_phase(plan_text: str) -> int:
    """Ambil nomor fase aktif dari baris `CURRENT PHASE: <n>`."""
    match = re.search(r"^CURRENT PHASE:\s*(\d+)\s*$", plan_text, re.MULTILINE)
    if match is None:
        raise ValueError("baris 'CURRENT PHASE: <n>' tidak ditemukan di PLAN.md")
    return int(match.group(1))


def parse_phase_status(plan_text: str, phase: int) -> str:
    """Ambil kolom Status pada tabel status fase untuk fase tertentu."""
    pattern = re.compile(
        rf"^\|\s*{phase}\s*\|[^|]*\|[^|]*\|[^|]*\|\s*([^|]+?)\s*\|$",
        re.MULTILINE,
    )
    match = pattern.search(plan_text)
    if match is None:
        raise ValueError(f"status fase {phase} tidak ditemukan di PLAN.md")
    return match.group(1).strip()


def resolve_gate_phase(plan_text: str) -> int:
    """Tentukan fase yang diverifikasi gate.

    Bila fase di CURRENT PHASE masih TODO, berarti CURRENT PHASE sudah bergeser ke fase
    berikutnya tetapi fase itu belum dimulai; gate memverifikasi fase terakhir yang dikerjakan.
    """
    current = parse_current_phase(plan_text)
    if parse_phase_status(plan_text, current).upper() != "TODO":
        return current
    return max(current - 1, 0)


def is_forbidden_repo_path(path: str) -> bool:
    """True bila path berada di data/ atau output/ (tidak boleh masuk repo)."""
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return any(normalized.startswith(prefix) for prefix in FORBIDDEN_PREFIXES)


def find_oversized_files(paths: Iterable[Path], limit_bytes: int) -> list[Path]:
    """Kembalikan file yang ukurannya melebihi batas."""
    return [path for path in paths if path.is_file() and path.stat().st_size > limit_bytes]


# ---------------------------------------------------------------------------
# Helper eksekusi perintah
# ---------------------------------------------------------------------------


def run_command(cmd: Sequence[str], cwd: Path = REPO_ROOT) -> tuple[int, str]:
    """Jalankan perintah dengan PYTHONPATH=src, kembalikan (exit code, keluaran)."""
    env = dict(os.environ)
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(cwd / "src") + (os.pathsep + existing if existing else "")
    completed = subprocess.run(
        list(cmd),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=COMMAND_TIMEOUT_SEC,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return completed.returncode, output


def _tail(text: str, lines: int = 3) -> str:
    rows = [row for row in text.splitlines() if row.strip()]
    if not rows:
        return "(tanpa keluaran)"
    return " | ".join(rows[-lines:])


def _result(gate_id: str, name: str, passed: bool, detail: str) -> GateResult:
    return GateResult(gate_id=gate_id, name=name, passed=passed, detail=detail)


# ---------------------------------------------------------------------------
# G1-G9
# ---------------------------------------------------------------------------


def check_g1_lint() -> GateResult:
    """G1: ruff check dan ruff format --check."""
    check_code, check_out = run_command([sys.executable, "-m", "ruff", "check", "."])
    format_code, format_out = run_command([sys.executable, "-m", "ruff", "format", "--check", "."])
    passed = check_code == 0 and format_code == 0
    detail = f"check={_tail(check_out, 1)}; format={_tail(format_out, 1)}"
    return _result("G1", "Lint dan format", passed, detail)


def check_g2_types() -> GateResult:
    """G2: mypy src."""
    code, output = run_command([sys.executable, "-m", "mypy", "src"])
    return _result("G2", "Type check", code == 0, _tail(output, 2))


def check_g3_unit() -> GateResult:
    """G3: unit test dengan coverage minimal 80%."""
    code, output = run_command(
        [
            sys.executable,
            "-m",
            "pytest",
            "-m",
            "not integration and not perf and not slow",
            "--cov=src/pcomp",
            "--cov-fail-under=80",
            "-q",
        ]
    )
    return _result("G3", "Unit test + coverage", code == 0, _tail(output, 2))


def check_g4_integration() -> GateResult:
    """G4: seluruh integration test lulus."""
    code, output = run_command([sys.executable, "-m", "pytest", "-m", "integration", "-q"])
    return _result("G4", "Integration test", code == 0, _tail(output, 2))


def check_g5_regression(g3: GateResult, g4: GateResult) -> GateResult:
    """G5: regresi; G3 dan G4 menjalankan seluruh test semua fase."""
    passed = g3.passed and g4.passed
    detail = "seluruh test fase lama ikut dijalankan oleh G3 dan G4" if passed else "G3/G4 gagal"
    return _result("G5", "Regresi", passed, detail)


def check_g6_smoke(phase: int) -> GateResult:
    """G6: smoke test fase aktif sesuai PLAN.md."""
    commands = SMOKE_COMMANDS.get(phase)
    if commands is None:
        return GateResult("G6", "Smoke test fase", False, f"smoke fase {phase} belum didefinisikan")

    details: list[str] = []
    passed = True
    outputs: list[str] = []
    for cmd in commands:
        code, output = run_command(cmd)
        outputs.append(output)
        label = " ".join(Path(part).name if i == 0 else part for i, part in enumerate(cmd))
        details.append(f"{label} -> rc={code}: {_tail(output, 1)}")
        passed = passed and code == 0

    combined = "\n".join(outputs)
    for expected in SMOKE_EXPECTED.get(phase, []):
        if expected not in combined:
            details.append(f"keluaran '{expected}' tidak ditemukan")
            passed = False

    return _result("G6", "Smoke test fase", passed, "; ".join(details))


def check_g7_flaky(phase: int) -> GateResult:
    """G7: integration test diulang 3 kali (berlaku fase 4 ke atas)."""
    if phase < FLAKY_GATE_MIN_PHASE:
        return GateResult(
            "G7",
            "Cek flaky x3",
            True,
            f"dilewati: berlaku fase {FLAKY_GATE_MIN_PHASE} ke atas (SDLC.md G7)",
            skipped=True,
        )
    for attempt in range(1, 4):
        code, output = run_command([sys.executable, "-m", "pytest", "-m", "integration", "-q"])
        if code != 0:
            return _result(
                "G7", "Cek flaky x3", False, f"gagal pada percobaan {attempt}: {_tail(output, 1)}"
            )
    return _result("G7", "Cek flaky x3", True, "3 kali lulus")


def _changelog_has_entry(phase: int) -> bool:
    if not CHANGELOG_PATH.is_file():
        return False
    text = CHANGELOG_PATH.read_text(encoding="utf-8")
    version_heading = re.compile(rf"^## \[0\.{phase:02d}\.0\][^\n]*$", re.MULTILINE)
    match = version_heading.search(text)
    if match is not None:
        body = text[match.end() :]
        next_heading = re.search(r"^## ", body, re.MULTILINE)
        block = body[: next_heading.start()] if next_heading else body
        if any(line.strip().startswith("- ") for line in block.splitlines()):
            return True
    unreleased = re.search(r"^## \[Unreleased\](.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    if unreleased is None:
        return False
    for line in unreleased.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith("- ") and stripped != "- (kosong)":
            return True
    return False


def _phase_log_complete(phase: int) -> tuple[bool, str]:
    path = PHASE_LOG_DIR / f"PHASE-{phase:02d}.md"
    if not path.is_file():
        return False, f"{path.relative_to(REPO_ROOT)} belum ada"
    text = path.read_text(encoding="utf-8")
    missing = [head for head in PHASE_LOG_REQUIRED_HEADINGS if head not in text]
    if missing:
        return False, f"bagian belum lengkap: {', '.join(missing)}"
    unfinished = [marker for marker in PHASE_LOG_UNFINISHED_MARKERS if marker in text]
    if unfinished:
        return False, f"masih ada penanda belum selesai: {', '.join(unfinished)}"
    return True, f"{path.relative_to(REPO_ROOT)} terisi"


def check_g8_docs(phase: int) -> GateResult:
    """G8: sinkronisasi CHANGELOG, phase log, dan status PLAN."""
    problems: list[str] = []
    if not _changelog_has_entry(phase):
        problems.append("CHANGELOG.md belum memuat entri fase ini")
    log_ok, log_detail = _phase_log_complete(phase)
    if not log_ok:
        problems.append(log_detail)
    plan_text = PLAN_PATH.read_text(encoding="utf-8")
    status = parse_phase_status(plan_text, phase)
    if status.upper() == "TODO":
        problems.append(f"status PLAN.md fase {phase} masih TODO")

    passed = not problems
    detail = "CHANGELOG, phase log, dan status PLAN sinkron" if passed else "; ".join(problems)
    return _result("G8", "Sinkron dokumen", passed, detail)


def check_g9_repo() -> GateResult:
    """G9: tidak ada file liar, tidak ada file > 5 MB, data/ dan output/ tidak ikut."""
    problems: list[str] = []

    tracked_code, tracked_out = run_command(["git", "ls-files"])
    if tracked_code != 0:
        return _result(
            "G9", "Kebersihan repo", False, f"git ls-files gagal: {_tail(tracked_out, 1)}"
        )
    tracked = [line for line in tracked_out.splitlines() if line.strip()]

    forbidden = [path for path in tracked if is_forbidden_repo_path(path)]
    if forbidden:
        problems.append(f"path terlarang terlacak: {', '.join(forbidden[:5])}")

    status_code, status_out = run_command(["git", "status", "--porcelain", "--untracked-files=all"])
    if status_code != 0:
        return _result("G9", "Kebersihan repo", False, f"git status gagal: {_tail(status_out, 1)}")

    untracked: list[str] = []
    for line in status_out.splitlines():
        if line.startswith("?? "):
            path = line[3:].strip().strip('"')
            untracked.append(path)
            if is_forbidden_repo_path(path):
                problems.append(f"file liar di path terlarang: {path}")

    candidates = [REPO_ROOT / path for path in tracked + untracked]
    oversized = find_oversized_files(candidates, MAX_FILE_BYTES)
    if oversized:
        names = ", ".join(str(path.relative_to(REPO_ROOT)) for path in oversized[:5])
        problems.append(f"file lebih dari 5 MB: {names}")

    passed = not problems
    detail = (
        f"{len(tracked)} file terlacak, tidak ada pelanggaran" if passed else "; ".join(problems)
    )
    return _result("G9", "Kebersihan repo", passed, detail)


# ---------------------------------------------------------------------------
# Pelaporan
# ---------------------------------------------------------------------------


def format_report(results: Sequence[GateResult], phase: int, quick: bool) -> str:
    """Susun teks tabel PASS/FAIL untuk layar dan reports/gate-latest.txt."""
    mode = "quick" if quick else "penuh"
    lines = [
        f"ZipHive Verification Gate - fase {phase} ({mode})",
        f"Waktu: {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"{'Gate':<5} {'Status':<6} {'Pemeriksaan':<22} Bukti",
        f"{'-' * 5} {'-' * 6} {'-' * 22} {'-' * 40}",
    ]
    for item in results:
        lines.append(f"{item.gate_id:<5} {item.label:<6} {item.name:<22} {item.detail}")
    failed = [item.gate_id for item in results if not item.passed and not item.skipped]
    lines.append("")
    if failed:
        lines.append(f"HASIL: FAIL ({', '.join(failed)})")
    else:
        lines.append("HASIL: PASS (seluruh gate wajib lulus)")
    return "\n".join(lines)


def write_report(text: str) -> Path:
    """Tulis ringkasan gate ke reports/gate-latest.txt."""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(text + "\n", encoding="utf-8")
    return REPORT_PATH


def run_gate(phase: int, quick: bool) -> list[GateResult]:
    """Jalankan gate sesuai mode."""
    g1 = check_g1_lint()
    if quick:
        g3 = check_g3_unit()
        return [g1, g3]

    g2 = check_g2_types()
    g3 = check_g3_unit()
    g4 = check_g4_integration()
    g5 = check_g5_regression(g3, g4)
    g6 = check_g6_smoke(phase)
    g7 = check_g7_flaky(phase)
    g8 = check_g8_docs(phase)
    g9 = check_g9_repo()
    return [g1, g2, g3, g4, g5, g6, g7, g8, g9]


def main(argv: list[str] | None = None) -> int:
    """Entry point gate."""
    parser = argparse.ArgumentParser(description="Verification Gate ZipHive (SDLC.md bagian 4)")
    parser.add_argument("--quick", action="store_true", help="hanya G1 (lint) dan G3 (unit test)")
    args = parser.parse_args(argv)

    phase = resolve_gate_phase(PLAN_PATH.read_text(encoding="utf-8"))
    results = run_gate(phase, args.quick)
    report = format_report(results, phase, args.quick)
    print(report)
    path = write_report(report)
    print(f"\nRingkasan disimpan di {path.relative_to(REPO_ROOT)}")

    failed = [item for item in results if not item.passed and not item.skipped]
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
