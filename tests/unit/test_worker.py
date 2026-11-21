"""UT-WRK-01..09: helper Worker, executor, heartbeat, dan klien (PLAN.md P4-T3, P4-T4)."""

from __future__ import annotations

import queue
import socket
import threading
import time

import pytest

from pcomp import constants
from pcomp.compressor import TaskResult, compress_task
from pcomp.config import WorkerConfig
from pcomp.net import recv_msg, send_msg
from pcomp.protocol import MessageType, make_header, validate_message
from pcomp.tasks import Task
from pcomp.worker import client as client_module
from pcomp.worker.client import (
    WorkerClient,
    build_register_header,
    build_result_header,
    parse_master_address,
)
from pcomp.worker.executor import Executor
from pcomp.worker.heartbeat import HeartbeatSender


def make_worker_config(**overrides: object) -> WorkerConfig:
    values: dict[str, object] = {
        "master": "127.0.0.1:5050",
        "worker_id": "w1",
        "procs": 1,
        "throttle": 0.0,
        "fail_after_tasks": 0,
        "fail_after_sec": 0.0,
        "task_fail_rate": 0.0,
        "seed": 1,
    }
    values.update(overrides)
    return WorkerConfig(**values)  # type: ignore[arg-type]


class FakeExecutor:
    """Pengganti Executor yang hanya mencatat task yang dikirim."""

    def __init__(self) -> None:
        self.submitted: list[tuple[Task, bytes, str, int]] = []

    def submit(self, task: Task, data: bytes, algo: str, level: int) -> None:
        self.submitted.append((task, data, algo, level))


def test_parse_master_address() -> None:
    """UT-WRK-01: alamat host:port diurai dan divalidasi."""
    assert parse_master_address("127.0.0.1:5050") == ("127.0.0.1", 5050)
    assert parse_master_address("localhost:1") == ("localhost", 1)
    with pytest.raises(ValueError):
        parse_master_address("127.0.0.1")
    with pytest.raises(ValueError):
        parse_master_address("127.0.0.1:70000")
    with pytest.raises(ValueError):
        parse_master_address(":5050")


def test_build_register_header_is_valid() -> None:
    """UT-WRK-02: header REGISTER lolos validasi protokol."""
    header = build_register_header("w1", hostname="uji", cores=4, procs=2)

    assert validate_message(header) is MessageType.REGISTER
    assert header["worker_id"] == "w1"
    assert header["procs"] == 2
    assert header["version"] == constants.PROTOCOL_VERSION
    assert header["v"] == constants.PROTOCOL_VERSION


def test_build_result_header_for_ok_and_error() -> None:
    task = Task(task_id=3, file="a.bin", index=0, offset=0, length=4)
    ok_result = compress_task(task, b"data", "gzip", 1)
    ok_header = build_result_header(task, ok_result)

    assert validate_message(ok_header) is MessageType.RESULT
    assert ok_header["ok"] is True
    assert ok_header["sha256_in"] == ok_result.sha256
    assert ok_header["comp_size"] == ok_result.comp_size
    assert ok_header["orig_size"] == 4

    failed = TaskResult(
        task_id=3, ok=False, sha256="", comp_size=0, data=None, error="boom", compute_sec=0.0
    )
    failed_header = build_result_header(task, failed)
    assert validate_message(failed_header) is MessageType.RESULT
    assert failed_header["ok"] is False
    assert failed_header["error"] == "boom"


def test_executor_runs_task_in_pool() -> None:
    """UT-WRK-03: executor menjalankan compress_task di proses pool."""
    results: queue.Queue[TaskResult] = queue.Queue()
    executor = Executor(2, results.put_nowait)
    task = Task(task_id=0, file="a.bin", index=0, offset=0, length=10)

    try:
        executor.submit(task, b"x" * 1000, "sim", 1)
        result = results.get(timeout=30)
    finally:
        executor.close()

    assert result.ok is True
    assert result.task_id == 0
    assert result.data == b"x" * 1000


def test_heartbeat_sends_valid_frames() -> None:
    """UT-WRK-04: heartbeat mengirim HEARTBEAT valid secara berkala."""
    headers: list[dict] = []
    sender = HeartbeatSender(headers.append, interval=0.02, inflight=lambda: 3)

    sender.start()
    deadline = time.monotonic() + 5.0
    while len(headers) < 3 and time.monotonic() < deadline:
        time.sleep(0.02)
    sender.stop()

    assert len(headers) >= 3
    assert all(validate_message(header) is MessageType.HEARTBEAT for header in headers)
    assert headers[0]["inflight"] == 3
    assert sender.is_running is False


def test_send_frame_without_connection_raises() -> None:
    """UT-WRK-05: mengirim sebelum terhubung ditolak jelas."""
    worker = WorkerClient(make_worker_config())

    with pytest.raises(ConnectionError):
        worker.send_frame(make_header(MessageType.REQUEST, credits=1))


def test_run_returns_error_when_master_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UT-WRK-06: Master tidak dapat dihubungi menghasilkan kode galat."""

    def refuse(host: str, port: int) -> socket.socket:
        raise ConnectionError("master menolak")

    monkeypatch.setattr(client_module, "connect_with_retry", refuse)

    assert WorkerClient(make_worker_config()).run() == constants.EXIT_ERROR


def test_report_rejection_reads_error_frame() -> None:
    """UT-WRK-07: penolakan REGISTER membaca kode ERROR dari Master."""
    worker = WorkerClient(make_worker_config())
    local, remote = socket.socketpair()
    try:
        send_msg(remote, make_header(MessageType.ERROR, code="VERSION_MISMATCH", message="beda"))
        assert worker._report_rejection(local, "ditolak") == constants.EXIT_ERROR
    finally:
        local.close()
        remote.close()


def test_receive_loop_submits_task_then_shutdown() -> None:
    """UT-WRK-08: TASK dikirim ke executor, HEARTBEAT_ACK diabaikan, SHUTDOWN mengakhiri loop."""
    worker = WorkerClient(make_worker_config())
    executor = FakeExecutor()
    local, remote = socket.socketpair()
    try:
        send_msg(
            remote,
            make_header(
                MessageType.TASK,
                task_id=1,
                file="a.bin",
                index=0,
                algo="sim",
                level=1,
                orig_size=4,
                sha256="0" * 64,
            ),
            b"data",
        )
        send_msg(remote, make_header(MessageType.HEARTBEAT_ACK, ts=0.0))
        send_msg(remote, make_header(MessageType.SHUTDOWN, reason="selesai"))

        code = worker._receive_loop(local, executor)  # type: ignore[arg-type]
    finally:
        local.close()
        remote.close()

    assert code == constants.EXIT_OK
    assert len(executor.submitted) == 1
    task, payload, algo, level = executor.submitted[0]
    assert (task.task_id, task.length, payload, algo, level) == (1, 4, b"data", "sim", 1)
    assert worker.inflight_count() == 1


def test_receive_loop_returns_error_on_error_message() -> None:
    """UT-WRK-09: pesan ERROR dari Master mengakhiri Worker dengan kode galat."""
    worker = WorkerClient(make_worker_config())
    local, remote = socket.socketpair()
    try:
        send_msg(remote, make_header(MessageType.ERROR, code="INTERNAL", message="gagal"))
        code = worker._receive_loop(local, FakeExecutor())  # type: ignore[arg-type]
    finally:
        local.close()
        remote.close()

    assert code == constants.EXIT_ERROR


def test_sender_loop_sends_result_and_new_credit() -> None:
    """UT-WRK-10: hasil dikirim sebagai RESULT diikuti REQUEST satu credit."""
    worker = WorkerClient(make_worker_config())
    local, remote = socket.socketpair()
    task = Task(task_id=7, file="a.bin", index=0, offset=0, length=10)
    results: queue.Queue[TaskResult] = queue.Queue()
    results.put(
        TaskResult(
            task_id=7,
            ok=True,
            sha256="a" * 64,
            comp_size=2,
            data=b"zz",
            error=None,
            compute_sec=0.01,
        )
    )
    try:
        worker._sock = local
        worker._inflight[7] = task
        thread = threading.Thread(target=worker._sender_loop, args=(results,))
        thread.start()
        result_frame = recv_msg(remote)
        request_frame = recv_msg(remote)
        worker._stop.set()
        thread.join(timeout=10)
    finally:
        local.close()
        remote.close()

    assert result_frame.header["type"] == "RESULT"
    assert result_frame.header["task_id"] == 7
    assert result_frame.payload == b"zz"
    assert request_frame.header["type"] == "REQUEST"
    assert request_frame.header["credits"] == 1
    assert worker.inflight_count() == 0
    assert thread.is_alive() is False


def test_executor_throttle_delays_task_and_counts_busy() -> None:
    """UT-WRK-11: throttle memperlambat task dan ikut terhitung pada compute_sec."""
    results: queue.Queue[TaskResult] = queue.Queue()
    executor = Executor(1, results.put_nowait, throttle=0.2)
    task = Task(task_id=0, file="a.bin", index=0, offset=0, length=1000)

    try:
        started = time.perf_counter()
        executor.submit(task, b"x" * 1000, "sim", 1)
        result = results.get(timeout=30)
        elapsed = time.perf_counter() - started
    finally:
        executor.close()

    assert result.ok is True
    assert elapsed >= 0.2
    assert result.compute_sec >= 0.2
