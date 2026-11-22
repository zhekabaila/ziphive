"""UT-KILL-01..05: batas Worker dan injeksi KILL pada Master (PLAN.md P11-T2)."""

from __future__ import annotations

import socket
import time
from pathlib import Path

import pytest

from pcomp import constants
from pcomp.config import MasterConfig
from pcomp.master.server import MasterServer, WorkerSession, should_inject_kills
from pcomp.metrics.events import read_events
from pcomp.net import recv_msg
from pcomp.protocol import ErrorCode, MessageType


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
        "expect_workers": 2,
        "heartbeat_interval": 0.05,
        "heartbeat_timeout": 6.0,
        "max_attempts": 3,
    }
    values.update(overrides)
    return MasterConfig(**values)  # type: ignore[arg-type]


def make_server(
    tmp_path: Path,
    *,
    expect_workers: int = 2,
    inject_kills: int = 0,
    inject_kill_fraction: float = 0.5,
) -> MasterServer:
    source = tmp_path / "input"
    source.mkdir(exist_ok=True)
    for index in range(2):
        (source / f"f{index}.txt").write_bytes(b"payload " * 300)
    config = make_config(tmp_path, expect_workers=expect_workers)
    return MasterServer(
        config,
        inject_kills=inject_kills,
        inject_kill_fraction=inject_kill_fraction,
    )


def session(worker_id: str, sock: socket.socket) -> WorkerSession:
    return WorkerSession(worker_id=worker_id, hostname=f"host-{worker_id}", procs=1, sock=sock)


def test_should_inject_kills_ambang() -> None:
    """UT-KILL-01: minimal satu task selesai sebelum kill, lalu mengikuti fraksi."""
    assert should_inject_kills(0, 10, 0.5) is False
    assert should_inject_kills(1, 10, 0.0) is True
    assert should_inject_kills(4, 10, 0.5) is False
    assert should_inject_kills(5, 10, 0.5) is True
    assert should_inject_kills(10, 10, 1.0) is True
    assert should_inject_kills(0, 0, 0.5) is False


def test_register_menolak_worker_berlebih(tmp_path: Path) -> None:
    """UT-KILL-02: Worker di luar --expect-workers ditolak dengan SERVER_FULL."""
    from pcomp.master.server import WorkerRejected

    server = make_server(tmp_path, expect_workers=1)
    left1, right1 = socket.socketpair()
    left2, right2 = socket.socketpair()
    try:
        server.state.register(session("w1", left1))
        with pytest.raises(WorkerRejected) as rejected:
            server.state.register(session("w2", left2))
        assert rejected.value.code is ErrorCode.SERVER_FULL
        assert "expect-workers 1" in rejected.value.message
        assert [item.worker_id for item in server.state.sessions()] == ["w1"]
    finally:
        for sock in (left1, right1, left2, right2):
            sock.close()


def test_register_menolak_id_ganda(tmp_path: Path) -> None:
    """UT-KILL-03: id yang masih aktif tetap ditolak sebagai DUPLICATE_WORKER."""
    from pcomp.master.server import WorkerRejected

    server = make_server(tmp_path, expect_workers=2)
    left1, right1 = socket.socketpair()
    left2, right2 = socket.socketpair()
    try:
        server.state.register(session("w1", left1))
        with pytest.raises(WorkerRejected) as rejected:
            server.state.register(session("w1", left2))
        assert rejected.value.code is ErrorCode.DUPLICATE_WORKER
    finally:
        for sock in (left1, right1, left2, right2):
            sock.close()


def test_maybe_inject_kills_mengirim_kill(tmp_path: Path) -> None:
    """UT-KILL-04: KILL terkirim sekali, tercatat di events, dan tidak diulang."""
    server = make_server(tmp_path, expect_workers=1, inject_kills=1, inject_kill_fraction=0.0)
    server.state.begin()
    left, right = socket.socketpair()
    right.settimeout(5.0)
    try:
        server.state.register(session("w1", left))
        task = server.state.table.take_next("w1", time.time())
        assert task is not None
        server.state.table.mark_done(task.task_id, sha256="x", comp_size=1, now=time.time())

        server._maybe_inject_kills()
        frame = recv_msg(right)
        assert frame.header["type"] == MessageType.KILL.value
        assert frame.header["worker_id"] == "w1"
        assert frame.header["v"] == constants.PROTOCOL_VERSION

        server._maybe_inject_kills()
        right.settimeout(0.2)
        with pytest.raises((TimeoutError, ConnectionError)):
            recv_msg(right)

        server.events.close()
        rows = read_events(tmp_path / "out" / "events.jsonl")
        injected = [row for row in rows if row["event"] == "worker_exit_injected"]
        assert len(injected) == 1
        assert injected[0]["worker_id"] == "w1"
    finally:
        left.close()
        right.close()


def test_tanpa_inject_kills_tidak_ada_pesan(tmp_path: Path) -> None:
    """UT-KILL-05: Master tanpa opsi E5 tidak pernah mengirim KILL."""
    server = make_server(tmp_path, expect_workers=1)
    server.state.begin()
    left, right = socket.socketpair()
    right.settimeout(0.2)
    try:
        server.state.register(session("w1", left))
        task = server.state.table.take_next("w1", time.time())
        assert task is not None
        server.state.table.mark_done(task.task_id, sha256="x", comp_size=1, now=time.time())
        server._maybe_inject_kills()
        with pytest.raises((TimeoutError, ConnectionError)):
            recv_msg(right)
    finally:
        left.close()
        right.close()


def test_worker_yang_dimatikan_tidak_boleh_daftar_lagi(tmp_path: Path) -> None:
    """UT-KILL-06: setelah KILL, id yang sama ditolak sampai run berakhir (E5 deterministik)."""
    from pcomp.master.server import WorkerRejected

    server = make_server(tmp_path, expect_workers=2, inject_kills=1, inject_kill_fraction=0.0)
    server.state.begin()
    left1, right1 = socket.socketpair()
    left2, right2 = socket.socketpair()
    try:
        first = session("w1", left1)
        server.state.register(first)
        task = server.state.table.take_next("w1", time.time())
        assert task is not None
        server.state.table.mark_done(task.task_id, sha256="x", comp_size=1, now=time.time())
        server._maybe_inject_kills()
        server.state.drop_worker("w1", "koneksi putus", time.time())

        with pytest.raises(WorkerRejected) as rejected:
            server.state.register(session("w1", left2))
        assert rejected.value.code is ErrorCode.SERVER_FULL
        assert "E5" in rejected.value.message
    finally:
        for sock in (left1, right1, left2, right2):
            sock.close()
