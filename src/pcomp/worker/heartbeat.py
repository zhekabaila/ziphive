"""Heartbeat Worker: kirim HEARTBEAT berkala (PLAN.md P4-T4, P7-T1).

Nilai `cpu_percent` dan `mem_percent` berasal dari sampler psutil yang disuntikkan;
bila tidak ada sampler, nilai 0.0 dikirim agar test lama tetap deterministik.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from pcomp.protocol import MessageType, make_header

SendFn = Callable[[dict[str, Any]], None]
UsageFn = Callable[[], tuple[float, float]]


class HeartbeatSender:
    """Thread pengirim HEARTBEAT sampai dihentikan."""

    def __init__(
        self,
        send: SendFn,
        *,
        interval: float,
        inflight: Callable[[], int] = lambda: 0,
        sampler: UsageFn | None = None,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if interval <= 0:
            raise ValueError("interval harus lebih besar dari 0")
        self._send = send
        self._interval = interval
        self._inflight = inflight
        self._sampler = sampler
        self._clock = clock
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="heartbeat", daemon=True)
        self._running = False

    @property
    def is_running(self) -> bool:
        """True selama thread heartbeat aktif."""
        return self._running and self._thread.is_alive()

    def start(self) -> None:
        """Mulai thread heartbeat."""
        self._thread.start()

    def stop(self) -> None:
        """Hentikan thread heartbeat dan tunggu sampai keluar."""
        self._stop.set()
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)

    def build_header(self) -> dict[str, Any]:
        """Header HEARTBEAT sesuai PROTOCOL.md bagian 2."""
        cpu, mem = self._sampler() if self._sampler is not None else (0.0, 0.0)
        return make_header(
            MessageType.HEARTBEAT,
            ts=self._clock(),
            cpu_percent=float(cpu),
            mem_percent=float(mem),
            inflight=self._inflight(),
        )

    def _loop(self) -> None:
        self._running = True
        try:
            while not self._stop.is_set():
                self._send(self.build_header())
                if self._stop.wait(self._interval):
                    break
        finally:
            self._running = False
