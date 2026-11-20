"""Klien Worker: REGISTER, terima TASK, kirim RESULT (PLAN.md P4-T3)."""

from __future__ import annotations

import contextlib
import logging
import queue
import socket
import sys
import threading
import time
from collections.abc import Callable
from typing import Any

from pcomp import constants
from pcomp.compressor import TaskResult
from pcomp.config import WorkerConfig
from pcomp.net import close_quietly, connect_with_retry, recv_msg, send_msg
from pcomp.protocol import MessageType, ProtocolError, make_header, validate_message
from pcomp.tasks import Task
from pcomp.worker.executor import Executor
from pcomp.worker.heartbeat import HeartbeatSender

logger = logging.getLogger(__name__)


def parse_master_address(value: str) -> tuple[str, int]:
    """Urai `host:port` dan validasi rentang port."""
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


def build_register_header(
    worker_id: str,
    *,
    hostname: str,
    cores: int,
    procs: int,
    version: int = constants.PROTOCOL_VERSION,
) -> dict[str, Any]:
    """Header REGISTER sesuai PROTOCOL.md bagian 2; `v` dan `version` bernilai sama."""
    header = make_header(
        MessageType.REGISTER,
        worker_id=worker_id,
        hostname=hostname,
        cores=cores,
        procs=procs,
        version=version,
    )
    header["v"] = version
    return header


def build_result_header(task: Task, result: TaskResult) -> dict[str, Any]:
    """Header RESULT; payload terkompresi dikirim terpisah."""
    return make_header(
        MessageType.RESULT,
        task_id=task.task_id,
        ok=result.ok,
        orig_size=task.length,
        comp_size=result.comp_size,
        sha256_in=result.sha256,
        compute_sec=round(result.compute_sec, 6),
        error=result.error,
    )


class WorkerClient:
    """Satu Worker: koneksi ke Master, pool kompresi, dan pengiriman hasil."""

    def __init__(
        self,
        config: WorkerConfig,
        *,
        protocol_version: int = constants.PROTOCOL_VERSION,
        hostname: str | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.config = config
        self.protocol_version = protocol_version
        self.hostname = hostname or socket.gethostname()
        self.clock = clock
        self._sock: socket.socket | None = None
        self._send_lock = threading.Lock()
        self._inflight: dict[int, Task] = {}
        self._inflight_lock = threading.Lock()
        self._stop = threading.Event()

    # -- bantu -----------------------------------------------------------
    def send_frame(self, header: dict[str, Any], payload: bytes = b"") -> None:
        """Kirim satu frame; semua thread memakai satu lock kirim."""
        sock = self._sock
        if sock is None:
            raise ConnectionError("socket Worker belum terhubung")
        with self._send_lock:
            send_msg(sock, header, payload)

    def inflight_count(self) -> int:
        with self._inflight_lock:
            return len(self._inflight)

    # -- utama -----------------------------------------------------------
    def run(self) -> int:
        """Jalankan Worker sampai SHUTDOWN, ERROR, atau koneksi putus."""
        host, port = parse_master_address(self.config.master)
        try:
            self._sock = connect_with_retry(host, port)
        except ConnectionError as exc:
            print(f"WORKER GAGAL: {exc}", file=sys.stderr)
            return constants.EXIT_ERROR
        sock = self._sock
        sock.settimeout(constants.DEFAULT_SOCKET_TIMEOUT)

        results: queue.Queue[TaskResult] = queue.Queue()
        executor: Executor | None = None
        heartbeat: HeartbeatSender | None = None
        sender: threading.Thread | None = None
        code = constants.EXIT_OK
        try:
            self.send_frame(
                build_register_header(
                    self.config.worker_id,
                    hostname=self.hostname,
                    cores=1,
                    procs=self.config.procs,
                    version=self.protocol_version,
                )
            )
            ack = recv_msg(sock)
            msg_type = validate_message(ack.header)
            if msg_type is not MessageType.REGISTER_ACK:
                print(f"WORKER: balasan tak terduga {msg_type.value}", file=sys.stderr)
                return constants.EXIT_ERROR
            if not ack.header["accepted"]:
                return self._report_rejection(sock, str(ack.header["reason"]))

            interval = float(ack.header["heartbeat_interval"])
            executor = Executor(self.config.procs, results.put)
            heartbeat = HeartbeatSender(
                self.send_frame,
                interval=interval,
                inflight=self.inflight_count,
                clock=self.clock,
            )
            heartbeat.start()
            sender = threading.Thread(
                target=self._sender_loop, args=(results,), name="sender", daemon=True
            )
            sender.start()
            self.send_frame(make_header(MessageType.REQUEST, credits=self.config.procs))
            code = self._receive_loop(sock, executor)
        except ProtocolError as exc:
            print(f"WORKER: protokol tidak valid: {exc}", file=sys.stderr)
            code = constants.EXIT_ERROR
        except (ConnectionError, OSError) as exc:
            print(f"WORKER: koneksi terputus: {exc}", file=sys.stderr)
            code = constants.EXIT_ERROR
        finally:
            self._stop.set()
            if heartbeat is not None:
                heartbeat.stop()
            with contextlib.suppress(ConnectionError, OSError):
                self.send_frame(make_header(MessageType.BYE, worker_id=self.config.worker_id))
            if executor is not None:
                executor.close()
            if sender is not None:
                sender.join(timeout=5.0)
            close_quietly(sock)
            self._sock = None
        return code

    def _report_rejection(self, sock: socket.socket, reason: str) -> int:
        """Cetak alasan penolakan REGISTER beserta kode ERROR bila ada."""
        code_text = "DITOLAK"
        try:
            frame = recv_msg(sock)
            if frame.header.get("type") == "ERROR":
                code_text = str(frame.header.get("code"))
                print(
                    f"WORKER DITOLAK {code_text}: {frame.header.get('message')}",
                    file=sys.stderr,
                )
        except (ConnectionError, OSError, ProtocolError):
            pass
        if code_text == "DITOLAK":
            print(f"WORKER DITOLAK: {reason}", file=sys.stderr)
        return constants.EXIT_ERROR

    def _receive_loop(self, sock: socket.socket, executor: Executor) -> int:
        while True:
            frame = recv_msg(sock)
            msg_type = validate_message(frame.header)
            if msg_type is MessageType.TASK:
                task = Task(
                    task_id=int(frame.header["task_id"]),
                    file=str(frame.header["file"]),
                    index=int(frame.header["index"]),
                    offset=0,
                    length=int(frame.header["orig_size"]),
                )
                with self._inflight_lock:
                    self._inflight[task.task_id] = task
                executor.submit(
                    task,
                    frame.payload,
                    str(frame.header["algo"]),
                    int(frame.header["level"]),
                )
            elif msg_type is MessageType.HEARTBEAT_ACK:
                continue
            elif msg_type is MessageType.SHUTDOWN:
                logger.info("SHUTDOWN diterima: %s", frame.header.get("reason"))
                return constants.EXIT_OK
            elif msg_type is MessageType.ERROR:
                print(
                    f"WORKER ERROR {frame.header['code']}: {frame.header['message']}",
                    file=sys.stderr,
                )
                return constants.EXIT_ERROR
            else:
                print(f"WORKER: pesan tidak diharapkan {msg_type.value}", file=sys.stderr)
                return constants.EXIT_ERROR

    def _sender_loop(self, results: queue.Queue[TaskResult]) -> None:
        """Kirim RESULT dan minta satu credit baru untuk setiap task selesai."""
        while not self._stop.is_set() or not results.empty():
            try:
                result = results.get(timeout=0.05)
            except queue.Empty:
                continue
            with self._inflight_lock:
                task = self._inflight.pop(result.task_id, None)
            if task is None:
                continue
            try:
                self.send_frame(build_result_header(task, result), result.data or b"")
                self.send_frame(make_header(MessageType.REQUEST, credits=1))
            except (ConnectionError, OSError):
                self._stop.set()
                return
