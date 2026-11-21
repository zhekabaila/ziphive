"""Monitor heartbeat Master: deteksi Worker DEAD dan requeue task (PLAN.md P6-T1)."""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pcomp.master.server import MasterState

logger = logging.getLogger(__name__)


class Monitor:
    """Pemantau heartbeat; `clock` dapat diganti jam palsu pada unit test."""

    def __init__(
        self,
        state: MasterState,
        *,
        timeout: float,
        interval: float,
        clock: Callable[[], float] = time.time,
        on_dead: Callable[[str], None] | None = None,
    ) -> None:
        if timeout <= 0:
            raise ValueError("timeout harus lebih besar dari 0")
        if interval <= 0:
            raise ValueError("interval harus lebih besar dari 0")
        self._state = state
        self._timeout = timeout
        self._interval = interval
        self._clock = clock
        self._on_dead = on_dead
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def sweep(self) -> list[str]:
        """Tandai Worker yang tidak mengirim pesan melebihi timeout; kembalikan id-nya."""
        now = self._clock()
        dead: list[str] = []
        for session in self._state.sessions():
            if now - session.last_seen <= self._timeout:
                continue
            self._state.drop_worker(session.worker_id, "heartbeat timeout", now)
            dead.append(session.worker_id)
            if self._on_dead is not None:
                self._on_dead(session.worker_id)
        return dead

    def start(self) -> None:
        """Jalankan thread pemantau sampai `stop` dipanggil."""
        if self._thread is not None:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="monitor", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Hentikan thread pemantau dan tunggu selesai."""
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.wait(self._interval):
            try:
                self.sweep()
            except Exception:  # noqa: BLE001 - monitor tidak boleh mematikan Master
                logger.exception("sweep monitor gagal")
