"""Master: accept loop, registry Worker, dispatch FIFO berbasis credit (PLAN.md P4-T1..T5).

Fase 4 sengaja belum memuat monitor heartbeat, requeue, retry, dan scheduler static;
semuanya dijadwalkan pada Fase 5 dan 6.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import socket
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pcomp import constants
from pcomp.chunker import plan_tasks, read_chunk
from pcomp.compressor import is_simulated
from pcomp.config import MasterConfig
from pcomp.master.collector import Collector
from pcomp.metrics.events import EventLog
from pcomp.net import close_quietly, recv_msg, send_msg
from pcomp.protocol import (
    ErrorCode,
    MessageType,
    ProtocolError,
    VersionMismatchError,
    make_header,
    validate_message,
)
from pcomp.tasks import Task, TaskTable

logger = logging.getLogger(__name__)


class WorkerRejected(Exception):
    """REGISTER ditolak; `code` dipakai pada pesan ERROR."""

    def __init__(self, code: ErrorCode, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class WorkerSession:
    """Satu koneksi Worker beserta saldo credit dan statistiknya."""

    worker_id: str
    hostname: str
    procs: int
    sock: socket.socket
    send_lock: threading.Lock = field(default_factory=threading.Lock)
    credits: int = 0
    inflight: int = 0
    tasks_done: int = 0
    tasks_failed: int = 0
    busy_sec: float = 0.0
    shutdown_sent: bool = False


def is_valid_result(task: Task, header: Mapping[str, Any], payload: bytes) -> bool:
    """Validasi hasil Worker (PLAN.md P4-T5): ok, sha256 masukan, ukuran asli, ukuran hasil."""
    if not header.get("ok"):
        return False
    if task.sha256 is None or header.get("sha256_in") != task.sha256:
        return False
    if header.get("orig_size") != task.length:
        return False
    return header.get("comp_size") == len(payload)


class MasterState:
    """Logika Master tanpa socket: registry, credit, dispatch FIFO, dan koleksi hasil."""

    def __init__(
        self,
        tasks: list[Task],
        collector: Collector,
        events: EventLog,
        *,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.table = TaskTable(tasks)
        self.collector = collector
        self.events = events
        self.started = False
        self.start_time: float | None = None
        self.started_at = datetime.now(UTC).isoformat(timespec="seconds")
        self._clock = clock
        self._lock = threading.Lock()
        self._sessions: dict[str, WorkerSession] = {}
        self._registered: list[WorkerSession] = []

    def register(self, session: WorkerSession) -> None:
        """Daftarkan Worker; WorkerRejected bila worker_id masih aktif."""
        with self._lock:
            if session.worker_id in self._sessions:
                raise WorkerRejected(
                    ErrorCode.DUPLICATE_WORKER,
                    f"worker_id '{session.worker_id}' masih aktif",
                )
            self._sessions[session.worker_id] = session
            self._registered.append(session)

    def remove(self, worker_id: str) -> None:
        """Lepas Worker aktif tanpa memengaruhi statistik yang sudah tercatat."""
        with self._lock:
            self._sessions.pop(worker_id, None)

    def sessions(self) -> list[WorkerSession]:
        """Daftar Worker yang masih terhubung."""
        with self._lock:
            return list(self._sessions.values())

    def all_sessions(self) -> list[WorkerSession]:
        """Daftar seluruh Worker yang pernah terdaftar pada run ini."""
        with self._lock:
            return list(self._registered)

    def add_credits(self, worker_id: str, credits: int) -> None:
        """Tambah saldo credit Worker."""
        with self._lock:
            session = self._sessions.get(worker_id)
            if session is not None:
                session.credits += credits

    def take(self, worker_id: str) -> Task | None:
        """Ambil satu task untuk Worker bila credit tersedia."""
        with self._lock:
            session = self._sessions.get(worker_id)
            if session is None or session.credits <= 0:
                return None
            task = self.table.take_next(worker_id, self._clock())
            if task is None:
                return None
            session.credits -= 1
            session.inflight += 1
            return task

    def handle_result(
        self, session: WorkerSession, header: Mapping[str, Any], payload: bytes
    ) -> str:
        """Proses RESULT: tulis chunk bila valid, selain itu tandai gagal."""
        task = self.table.claim_result(int(header["task_id"]), session.worker_id)
        if task is None:
            self.events.emit(
                "result_ignored", task_id=header["task_id"], worker_id=session.worker_id
            )
            return "ignored"

        session.inflight = max(0, session.inflight - 1)
        if is_valid_result(task, header, payload):
            entry = self.collector.write_chunk(
                task,
                payload,
                sha256=str(header["sha256_in"]),
                comp_size=int(header["comp_size"]),
            )
            self.table.mark_done(
                task.task_id,
                sha256=str(header["sha256_in"]),
                comp_size=int(header["comp_size"]),
                now=self._clock(),
            )
            session.tasks_done += 1
            session.busy_sec += float(header["compute_sec"])
            self.events.emit(
                "task_done",
                task_id=task.task_id,
                worker_id=session.worker_id,
                comp_size=entry.comp_size,
                compute_sec=header["compute_sec"],
            )
            return "done"

        self.table.mark_failed(task.task_id, now=self._clock())
        session.tasks_failed += 1
        self.events.emit(
            "task_failed",
            task_id=task.task_id,
            worker_id=session.worker_id,
            error=header.get("error") or "hasil tidak valid",
        )
        return "failed"

    def all_finished(self) -> bool:
        return self.table.all_finished()

    def begin(self) -> None:
        """Mulai pengukuran waktu setelah barrier terpenuhi."""
        self.started = True
        self.start_time = self._clock()

    def elapsed(self) -> float:
        """Waktu berjalan sejak barrier (0 bila belum mulai)."""
        if self.start_time is None:
            return 0.0
        return self._clock() - self.start_time


class MasterServer:
    """Server TCP Master: satu thread handler per Worker."""

    def __init__(
        self,
        config: MasterConfig,
        *,
        barrier_timeout: float = constants.DEFAULT_BARRIER_TIMEOUT,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.config = config
        self.barrier_timeout = barrier_timeout
        self.clock = clock
        self.input_dir = Path(config.input)
        self.out_dir = Path(config.out)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.tasks = plan_tasks(self.input_dir, chunk_mb=config.chunk_mb, repeat=config.repeat)
        self.events = EventLog(self.out_dir / "events.jsonl", clock=clock)
        self.collector = Collector(
            self.out_dir,
            algo=config.algo,
            level=config.level,
            chunk_mb=config.chunk_mb,
            repeat=config.repeat,
            total_tasks=len(self.tasks),
        )
        self.state = MasterState(self.tasks, self.collector, self.events, clock=clock)
        self.port = config.port
        self.last_error: str | None = None
        self.metrics: dict[str, Any] = {}
        self._listener: socket.socket | None = None
        self._stop = threading.Event()
        self._start_lock = threading.Lock()
        self._finish_lock = threading.Lock()
        self._finalize_lock = threading.Lock()
        self._handlers: list[threading.Thread] = []
        self._finished = False
        self._finalized = False

    # -- siklus hidup ---------------------------------------------------
    def begin(self) -> None:
        """Tandai run mulai; aman dipanggil dari beberapa thread."""
        with self._start_lock:
            if self.state.started:
                return
            self.state.begin()
            self.events.emit(
                "run_started",
                tasks=len(self.tasks),
                expect_workers=self.config.expect_workers,
                workers=len(self.state.sessions()),
            )
            logger.info(
                "Mulai memproses %s task dengan %s Worker",
                len(self.tasks),
                len(self.state.sessions()),
            )
            for session in self.state.sessions():
                self._dispatch(session)
        if self.state.all_finished():
            self._maybe_finish()

    def run(self) -> int:
        """Jalankan Master sampai semua task selesai atau barrier habis."""
        self._open_listener()
        logger.info("Master mendengarkan di %s:%s", self.config.host, self.port)
        deadline = time.monotonic() + self.barrier_timeout
        try:
            while not self._stop.is_set():
                self._accept_once()
                if self.state.started:
                    continue
                if len(self.state.sessions()) >= self.config.expect_workers:
                    self.begin()
                elif time.monotonic() >= deadline:
                    if not self.state.sessions():
                        self.last_error = "tidak ada Worker terdaftar sebelum batas barrier"
                        logger.error(self.last_error)
                        return constants.EXIT_ERROR
                    logger.warning("Barrier habis; mulai dengan Worker yang tersedia")
                    self.begin()
            if self.state.started:
                self.finalize()
            return constants.EXIT_OK if self._exit_ok() else constants.EXIT_ERROR
        finally:
            self._stop.set()
            if self._listener is not None:
                close_quietly(self._listener)
            self._listener = None
            self._join_handlers()
            self.events.close()

    def _exit_ok(self) -> bool:
        counts = self.state.table.counts()
        return counts["FAILED"] == 0

    def _open_listener(self) -> None:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((self.config.host, self.config.port))
        listener.listen(16)
        listener.settimeout(0.2)
        self._listener = listener
        self.port = int(listener.getsockname()[1])

    def _accept_once(self) -> None:
        if self._listener is None:
            return
        try:
            client, address = self._listener.accept()
        except (TimeoutError, OSError):
            return
        thread = threading.Thread(
            target=self.serve_connection,
            args=(client,),
            name=f"worker-{address[0]}:{address[1]}",
            daemon=True,
        )
        self._handlers.append(thread)
        thread.start()

    def _join_handlers(self, timeout: float = 5.0) -> None:
        deadline = time.monotonic() + timeout
        for thread in self._handlers:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            thread.join(remaining)

    # -- satu koneksi Worker --------------------------------------------
    def serve_connection(self, sock: socket.socket) -> None:
        """Layani satu Worker sampai SHUTDOWN, BYE, atau koneksi putus."""
        session: WorkerSession | None = None
        try:
            sock.settimeout(constants.DEFAULT_SOCKET_TIMEOUT)
            frame = recv_msg(sock)
            try:
                msg_type = validate_message(frame.header)
            except VersionMismatchError as exc:
                self._send_ack(sock, accepted=False, reason=str(exc))
                self._send_error(sock, ErrorCode.VERSION_MISMATCH, str(exc))
                return
            except ProtocolError as exc:
                self._send_error(sock, ErrorCode.BAD_FRAME, str(exc))
                return

            if msg_type is not MessageType.REGISTER:
                self._send_error(sock, ErrorCode.BAD_FRAME, "pesan pertama harus REGISTER")
                return

            session = self._register(sock, frame.header)
            self._dispatch(session)

            while True:
                # Setelah SHUTDOWN, handler tetap membaca sampai BYE agar socket
                # tidak ditutup mendadak dan frame SHUTDOWN tidak hilang karena RST.
                if self._stop.is_set() and not session.shutdown_sent:
                    break
                frame = recv_msg(sock)
                try:
                    msg_type = validate_message(frame.header)
                except ProtocolError as exc:
                    self._send_error(sock, ErrorCode.BAD_FRAME, str(exc))
                    break
                if msg_type is MessageType.REQUEST:
                    self.state.add_credits(session.worker_id, int(frame.header["credits"]))
                    self._dispatch(session)
                elif msg_type is MessageType.RESULT:
                    self.state.handle_result(session, frame.header, frame.payload)
                    self._maybe_finish()
                elif msg_type is MessageType.HEARTBEAT:
                    with session.send_lock:
                        send_msg(sock, make_header(MessageType.HEARTBEAT_ACK, ts=self.clock()))
                elif msg_type is MessageType.BYE:
                    break
                else:
                    self._send_error(
                        sock, ErrorCode.BAD_FRAME, f"pesan {msg_type.value} tidak diharapkan"
                    )
                    break
        except WorkerRejected as exc:
            self._send_error(sock, exc.code, exc.message)
        except (ConnectionError, OSError, ProtocolError) as exc:
            logger.warning("koneksi Worker berakhir: %s", exc)
        finally:
            if session is not None:
                self.state.remove(session.worker_id)
                self.events.emit("worker_disconnected", worker_id=session.worker_id)
            close_quietly(sock)

    def _register(self, sock: socket.socket, header: Mapping[str, Any]) -> WorkerSession:
        session = WorkerSession(
            worker_id=str(header["worker_id"]),
            hostname=str(header["hostname"]),
            procs=int(header["procs"]),
            sock=sock,
        )
        self.state.register(session)
        with session.send_lock:
            send_msg(
                sock,
                make_header(
                    MessageType.REGISTER_ACK,
                    accepted=True,
                    reason="",
                    heartbeat_interval=self.config.heartbeat_interval,
                    algo=self.config.algo,
                    level=self.config.level,
                ),
            )
        self.events.emit(
            "worker_registered",
            worker_id=session.worker_id,
            hostname=session.hostname,
            procs=session.procs,
        )
        if len(self.state.sessions()) >= self.config.expect_workers:
            self.begin()
        return session

    def _send_ack(self, sock: socket.socket, *, accepted: bool, reason: str) -> None:
        with contextlib.suppress(OSError):
            send_msg(
                sock,
                make_header(
                    MessageType.REGISTER_ACK,
                    accepted=accepted,
                    reason=reason,
                    heartbeat_interval=self.config.heartbeat_interval,
                    algo=self.config.algo,
                    level=self.config.level,
                ),
            )

    def _send_error(self, sock: socket.socket, code: ErrorCode, message: str) -> None:
        with contextlib.suppress(OSError):
            send_msg(sock, make_header(MessageType.ERROR, code=code.value, message=message))

    # -- dispatch dan penyelesaian --------------------------------------
    def _dispatch(self, session: WorkerSession) -> None:
        if not self.state.started:
            return
        while not self._stop.is_set():
            task = self.state.take(session.worker_id)
            if task is None:
                return
            try:
                data = read_chunk(self.input_dir, task)
            except OSError as exc:
                self.state.table.mark_failed(task.task_id, now=self.clock())
                session.tasks_failed += 1
                self.events.emit(
                    "task_failed",
                    task_id=task.task_id,
                    worker_id=session.worker_id,
                    error=str(exc),
                )
                continue

            digest = hashlib.sha256(data).hexdigest()
            task.sha256 = digest
            header = make_header(
                MessageType.TASK,
                task_id=task.task_id,
                file=task.file,
                index=task.index,
                algo=self.config.algo,
                level=self.config.level,
                orig_size=len(data),
                sha256=digest,
            )
            with session.send_lock:
                send_msg(session.sock, header, data)
            self.events.emit(
                "task_assigned",
                task_id=task.task_id,
                worker_id=session.worker_id,
                size=len(data),
            )

    def _maybe_finish(self) -> None:
        if not self.state.all_finished():
            return
        with self._finish_lock:
            if self._finished:
                return
            self._finished = True
        for session in self.state.sessions():
            with session.send_lock:
                try:
                    send_msg(
                        session.sock,
                        make_header(MessageType.SHUTDOWN, reason="semua task selesai"),
                    )
                    session.shutdown_sent = True
                except OSError:
                    session.shutdown_sent = False
        self._stop.set()

    def finalize(self) -> None:
        """Tulis manifest, metrics, dan event penutup sekali saja (idempoten)."""
        with self._finalize_lock:
            if self._finalized:
                return
            self._finalized = True
        manifest = self.collector.write_manifest()
        counts = self.state.table.counts()
        elapsed = self.state.elapsed()
        total_mb = manifest.total_orig_bytes / constants.MIB
        sessions = self.state.all_sessions()
        metrics: dict[str, Any] = {
            "mode": "distributed",
            "algo": self.config.algo,
            "level": self.config.level,
            "chunk_mb": self.config.chunk_mb,
            "repeat": self.config.repeat,
            "scheduler": "fifo",
            "workers": len(sessions),
            "worker_stats": [
                {
                    "worker_id": session.worker_id,
                    "hostname": session.hostname,
                    "procs": session.procs,
                    "tasks_done": session.tasks_done,
                    "tasks_failed": session.tasks_failed,
                    "busy_sec": round(session.busy_sec, 6),
                }
                for session in sessions
            ],
            "tasks": len(self.tasks),
            "tasks_ok": counts["DONE"],
            "tasks_failed": counts["FAILED"],
            "total_orig_bytes": manifest.total_orig_bytes,
            "total_comp_bytes": manifest.total_comp_bytes,
            "total_mb": round(total_mb, 6),
            "ratio": round(manifest.ratio, 6),
            "time_s": round(elapsed, 6),
            "throughput_mbs": round(total_mb / elapsed, 6) if elapsed > 0 else 0.0,
            "simulated": is_simulated(self.config.algo),
            "started_at": self.state.started_at,
        }
        self.collector.write_metrics(metrics)
        self.metrics = metrics
        self.events.emit(
            "run_finished",
            tasks_ok=counts["DONE"],
            tasks_failed=counts["FAILED"],
            time_s=metrics["time_s"],
        )
