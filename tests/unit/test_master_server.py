"""UT-MST-01..06: logika Master dan penanganan koneksi (PLAN.md P4-T1, P4-T2, P4-T5)."""

from __future__ import annotations

import hashlib
import json
import socket
import threading
from pathlib import Path

import pytest

from pcomp import constants
from pcomp.compressor import compress
from pcomp.config import MasterConfig
from pcomp.manifest import read_manifest
from pcomp.master.server import MasterServer, is_valid_result
from pcomp.net import recv_msg, send_msg
from pcomp.protocol import make_header
from pcomp.tasks import Task


def make_config(tmp_path: Path, **overrides: object) -> MasterConfig:
    values: dict[str, object] = {
        "host": "127.0.0.1",
        "port": 5050,
        "input": str(tmp_path / "input"),
        "out": str(tmp_path / "out"),
        "algo": "gzip",
        "level": 1,
        "chunk_mb": 1,
        "repeat": 1,
        "scheduler": "dynamic",
        "expect_workers": 1,
        "heartbeat_interval": 0.05,
        "heartbeat_timeout": 6.0,
        "max_attempts": 3,
    }
    values.update(overrides)
    return MasterConfig(**values)  # type: ignore[arg-type]


def make_dataset(tmp_path: Path, count: int = 2) -> Path:
    source = tmp_path / "input"
    source.mkdir(exist_ok=True)
    for index in range(count):
        (source / f"f{index}.txt").write_bytes(f"payload-{index} ".encode() * 50)
    return source


class ServerThread:
    """Jalankan `serve_connection` pada satu sisi socketpair."""

    def __init__(self, server: MasterServer, sock: socket.socket) -> None:
        self.sock = sock
        self.thread = threading.Thread(target=server.serve_connection, args=(sock,), daemon=True)
        self.thread.start()

    def join(self, timeout: float = 10.0) -> None:
        self.thread.join(timeout)


def register_header(worker_id: str = "w1", version: int = constants.PROTOCOL_VERSION) -> dict:
    header = make_header(
        "REGISTER", worker_id=worker_id, hostname="uji", cores=2, procs=2, version=version
    )
    header["v"] = version
    return header


def test_first_message_must_be_register(tmp_path: Path) -> None:
    """UT-MST-01: pesan pertama selain REGISTER ditolak dengan ERROR BAD_FRAME."""
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()
    local, remote = socket.socketpair()
    runner = ServerThread(server, local)

    send_msg(remote, make_header("REQUEST", credits=1))
    frame = recv_msg(remote)

    assert frame.header["type"] == "ERROR"
    assert frame.header["code"] == "BAD_FRAME"
    runner.join()
    remote.close()


def test_version_mismatch_rejected(tmp_path: Path) -> None:
    """UT-MST-02: versi protokol berbeda ditolak (PROTOCOL.md aturan 2)."""
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()
    local, remote = socket.socketpair()
    runner = ServerThread(server, local)

    send_msg(remote, register_header(version=99))
    ack = recv_msg(remote)
    error = recv_msg(remote)

    assert ack.header["type"] == "REGISTER_ACK"
    assert ack.header["accepted"] is False
    assert error.header["code"] == "VERSION_MISMATCH"
    runner.join()
    remote.close()
    assert server.state.sessions() == []


def test_duplicate_worker_rejected(tmp_path: Path) -> None:
    """UT-MST-03: worker_id aktif yang sama ditolak (PROTOCOL.md aturan 3)."""
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()

    first_local, first_remote = socket.socketpair()
    first = ServerThread(server, first_local)
    send_msg(first_remote, register_header())
    assert recv_msg(first_remote).header["accepted"] is True

    second_local, second_remote = socket.socketpair()
    second = ServerThread(server, second_local)
    send_msg(second_remote, register_header())
    frame = recv_msg(second_remote)

    assert frame.header["type"] == "ERROR"
    assert frame.header["code"] == "DUPLICATE_WORKER"

    first.join()
    second.join()
    first_remote.close()
    second_remote.close()


def test_full_task_cycle(tmp_path: Path) -> None:
    """UT-MST-04: TASK dikirim sesuai credit, RESULT valid menulis chunk dan SHUTDOWN."""
    make_dataset(tmp_path)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()
    local, remote = socket.socketpair()
    runner = ServerThread(server, local)

    send_msg(remote, register_header())
    assert recv_msg(remote).header["accepted"] is True
    send_msg(remote, make_header("REQUEST", credits=2))

    dispatched = [recv_msg(remote), recv_msg(remote)]
    assert [frame.header["task_id"] for frame in dispatched] == [0, 1]
    assert all(frame.header["algo"] == "gzip" for frame in dispatched)

    results = []
    for frame in dispatched:
        raw = frame.payload
        assert hashlib.sha256(raw).hexdigest() == frame.header["sha256"]
        assert frame.header["orig_size"] == len(raw)
        packed = compress("gzip", 1, raw)
        send_msg(
            remote,
            make_header(
                "RESULT",
                task_id=frame.header["task_id"],
                ok=True,
                orig_size=len(raw),
                comp_size=len(packed),
                sha256_in=frame.header["sha256"],
                compute_sec=0.01,
                error=None,
            ),
            packed,
        )
        results.append(frame.header["task_id"])

    shutdown = recv_msg(remote)
    assert shutdown.header["type"] == "SHUTDOWN"
    runner.join()
    server.finalize()

    manifest = read_manifest(server.out_dir / "manifest.json")
    assert [entry.task_id for entry in manifest.entries] == results
    metrics = json.loads((server.out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["tasks_ok"] == 2
    assert metrics["tasks_failed"] == 0
    assert metrics["mode"] == "distributed"
    events = [
        json.loads(line)
        for line in (server.out_dir / "events.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert {"worker_registered", "task_done", "run_finished"} <= {item["event"] for item in events}
    remote.close()


def test_invalid_result_marks_failed(tmp_path: Path) -> None:
    """UT-MST-05: hasil dengan sha256 salah dihitung gagal."""
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()
    local, remote = socket.socketpair()
    runner = ServerThread(server, local)

    send_msg(remote, register_header())
    recv_msg(remote)
    send_msg(remote, make_header("REQUEST", credits=1))
    task_frame = recv_msg(remote)
    packed = compress("gzip", 1, b"salah")
    send_msg(
        remote,
        make_header(
            "RESULT",
            task_id=task_frame.header["task_id"],
            ok=True,
            orig_size=task_frame.header["orig_size"],
            comp_size=len(packed),
            sha256_in="0" * 64,
            compute_sec=0.0,
            error=None,
        ),
        packed,
    )

    assert recv_msg(remote).header["type"] == "SHUTDOWN"
    runner.join()
    server.finalize()

    metrics = json.loads((server.out_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["tasks_failed"] == 1
    assert metrics["tasks_ok"] == 0
    manifest = read_manifest(server.out_dir / "manifest.json")
    assert manifest.entries == ()
    remote.close()


def test_is_valid_result_checks_fields() -> None:
    task = Task(task_id=0, file="a", index=0, offset=0, length=4)
    task.sha256 = "a" * 64
    good = {
        "ok": True,
        "sha256_in": "a" * 64,
        "orig_size": 4,
        "comp_size": 3,
    }
    assert is_valid_result(task, good, b"abc") is True
    assert is_valid_result(task, dict(good, sha256_in="b" * 64), b"abc") is False
    assert is_valid_result(task, dict(good, orig_size=5), b"abc") is False
    assert is_valid_result(task, dict(good, comp_size=2), b"abc") is False
    assert is_valid_result(task, dict(good, ok=False), b"abc") is False


def test_run_without_workers_times_out(tmp_path: Path, free_port: int) -> None:
    """UT-MST-06: tanpa Worker, barrier berakhir dan Master keluar dengan kode error."""
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path, port=free_port), barrier_timeout=0.3)

    assert server.run() == constants.EXIT_ERROR
    assert "tidak ada Worker" in (server.last_error or "")


@pytest.mark.parametrize("credits", [0, -1])
def test_invalid_credit_rejected(tmp_path: Path, credits: int) -> None:
    make_dataset(tmp_path, count=1)
    server = MasterServer(make_config(tmp_path), barrier_timeout=1.0)
    server.begin()
    local, remote = socket.socketpair()
    runner = ServerThread(server, local)

    send_msg(remote, register_header())
    recv_msg(remote)
    send_msg(remote, make_header("REQUEST", credits=credits))
    frame = recv_msg(remote)

    assert frame.header["type"] == "ERROR"
    runner.join()
    remote.close()
