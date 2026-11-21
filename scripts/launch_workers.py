"""Pembangkit perintah Worker dari `config/nodes.toml` (PLAN.md P8-T2).

Dua mode: `--print` mencetak perintah ssh per node tanpa mengeksekusi apa pun, dan
`--ssh` menjalankan perintah tersebut (tambahkan `--dry-run` untuk mencetak saja).
Skrip tidak menyimpan kredensial; ssh diasumsikan memakai kunci yang sudah dipasang.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NODES = REPO_ROOT / "config" / "nodes.toml"
DEFAULT_PORT = 5050
DEFAULT_PROCS = 1
DEFAULT_WORKDIR = "~/ziphive"
ROLES = ("master", "worker")
REQUIRED_FIELDS = ("nama", "host", "role", "user")
PLACEHOLDER_FIELDS = ("host", "user", "python")
EXIT_OK = 0
EXIT_FAIL = 1
EXIT_USAGE = 2


@dataclass(frozen=True)
class Node:
    """Satu baris inventaris `config/nodes.toml`."""

    name: str
    host: str
    role: str
    user: str
    python: str = "python3"
    procs: int | None = None


@dataclass(frozen=True)
class LaunchItem:
    """Perintah satu Worker beserta argv ssh-nya."""

    node: Node
    worker_id: str
    command: str
    ssh: list[str]


def _text(entry: Mapping[str, object], key: str, default: str = "") -> str:
    value = entry.get(key, default)
    return "" if value is None else str(value).strip()


def parse_node(entry: Mapping[str, object]) -> Node:
    """Ubah satu entri TOML menjadi `Node` dan tolak isian yang tidak lengkap."""
    missing = [key for key in REQUIRED_FIELDS if not _text(entry, key)]
    if missing:
        raise ValueError(f"node kehilangan field: {', '.join(missing)}")
    role = _text(entry, "role").lower()
    if role not in ROLES:
        raise ValueError(f"role tidak dikenal: {role!r} (pilihan: {', '.join(ROLES)})")
    raw_procs = entry.get("procs")
    procs = int(raw_procs) if raw_procs is not None else None
    if procs is not None and procs < 1:
        raise ValueError(f"procs minimal 1 pada node {_text(entry, 'nama')}")
    return Node(
        name=_text(entry, "nama"),
        host=_text(entry, "host"),
        role=role,
        user=_text(entry, "user"),
        python=_text(entry, "python", "python3") or "python3",
        procs=procs,
    )


def load_nodes(path: Path) -> list[Node]:
    """Baca daftar node dari file TOML inventaris."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"inventaris node tidak ditemukan: {path}")
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    entries = data.get("node") or []
    if not entries:
        raise ValueError(f"tidak ada entri [[node]] pada {path}")
    return [parse_node(entry) for entry in entries]


def split_roles(nodes: Sequence[Node]) -> tuple[Node, list[Node]]:
    """Pisahkan node Master dan Worker, dengan tepat satu Master."""
    masters = [node for node in nodes if node.role == "master"]
    workers = [node for node in nodes if node.role == "worker"]
    if len(masters) != 1:
        raise ValueError(f"butuh tepat satu node master, ditemukan {len(masters)}")
    if not workers:
        raise ValueError("tidak ada node worker pada inventaris")
    return masters[0], workers


def is_placeholder(value: str) -> bool:
    """True bila nilai masih berupa placeholder `<...>`."""
    return value.startswith("<") and value.endswith(">")


def placeholder_fields(node: Node) -> list[str]:
    """Daftar field node yang masih berisi placeholder."""
    return [key for key in PLACEHOLDER_FIELDS if is_placeholder(getattr(node, key))]


def worker_address(master: Node, port: int) -> str:
    """Alamat `host:port` yang dipakai Worker untuk menghubungi Master."""
    if not 1 <= port <= 65535:
        raise ValueError(f"port di luar rentang 1-65535: {port}")
    return f"{master.host}:{port}"


def build_plan(
    nodes: Sequence[Node],
    *,
    port: int = DEFAULT_PORT,
    procs: int = DEFAULT_PROCS,
    workdir: str = DEFAULT_WORKDIR,
) -> list[LaunchItem]:
    """Bangkitkan perintah tiap Worker sesuai DEPLOYMENT.md bagian 4."""
    if procs < 1:
        raise ValueError("procs minimal 1")
    master, workers = split_roles(list(nodes))
    address = worker_address(master, port)
    plan: list[LaunchItem] = []
    for index, node in enumerate(workers, start=1):
        worker_id = f"w{index}"
        count = node.procs if node.procs is not None else procs
        command = (
            f"cd {workdir} && {node.python} -m pcomp.worker"
            f" --master {address} --id {worker_id} --procs {count}"
        )
        plan.append(
            LaunchItem(
                node=node,
                worker_id=worker_id,
                command=command,
                ssh=["ssh", f"{node.user}@{node.host}", command],
            )
        )
    return plan


def report_placeholders(nodes: Sequence[Node]) -> list[tuple[str, str]]:
    """Kumpulkan pasangan (nama node, field) yang masih placeholder."""
    problems: list[tuple[str, str]] = []
    for node in nodes:
        problems.extend((node.name, field) for field in placeholder_fields(node))
    return problems


def build_parser() -> argparse.ArgumentParser:
    """Parser argumen `launch_workers.py`."""
    parser = argparse.ArgumentParser(
        prog="launch_workers.py", description="Jalankan Worker di banyak node dari satu tempat"
    )
    parser.add_argument("--nodes", default=str(DEFAULT_NODES), help="file inventaris TOML")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port Master")
    parser.add_argument(
        "--procs", type=int, default=DEFAULT_PROCS, help="proses per Worker bila TOML tidak mengisi"
    )
    parser.add_argument("--dir", default=DEFAULT_WORKDIR, help="folder kerja di node jarak jauh")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--print", action="store_true", help="cetak perintah ssh tanpa menjalankan")
    mode.add_argument("--ssh", action="store_true", help="jalankan perintah ssh")
    parser.add_argument("--dry-run", action="store_true", help="dengan --ssh: cetak saja")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Cetak atau jalankan perintah Worker, lalu kembalikan exit code."""
    args = build_parser().parse_args(argv)
    try:
        nodes = load_nodes(Path(args.nodes))
        plan = build_plan(nodes, port=args.port, procs=args.procs, workdir=args.dir)
    except (OSError, ValueError) as exc:
        print(f"LAUNCH GAGAL: {exc}", file=sys.stderr)
        return EXIT_USAGE

    problems = report_placeholders(nodes)
    if problems:
        for name, field in problems:
            print(f"placeholder: node {name} field {field}", file=sys.stderr)
        print(
            "LAUNCH GAGAL: lengkapi config/nodes.toml dari inventaris DEPLOYMENT.md bagian 1",
            file=sys.stderr,
        )
        return EXIT_FAIL

    for item in plan:
        printed = " ".join(item.ssh)
        print(printed)
        if not args.ssh or args.dry_run:
            continue
        code = subprocess.run(item.ssh, check=False).returncode
        if code != 0:
            print(f"LAUNCH GAGAL: {item.node.name} keluar dengan kode {code}", file=sys.stderr)
            return EXIT_FAIL

    print("LAUNCH OK" if args.ssh else "LAUNCH PLAN OK")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
