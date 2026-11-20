"""Helper socket: kirim/terima frame dan connect dengan retry (PLAN.md P1-T2)."""

from __future__ import annotations

import contextlib
import socket
import time
from collections.abc import Callable, Mapping
from typing import Any

from pcomp import constants
from pcomp.protocol import Frame, decode_frame_prefix, decode_header, encode_frame

ConnectFn = Callable[[tuple[str, int], float], socket.socket]
SleepFn = Callable[[float], None]


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """Baca tepat `size` byte; ConnectionError bila koneksi tertutup lebih awal."""
    if size == 0:
        return b""
    chunks: list[bytes] = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(remaining)
        if not chunk:
            raise ConnectionError(
                f"koneksi tertutup saat menunggu {size} byte (sisa {remaining} byte)"
            )
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def send_msg(sock: socket.socket, header: Mapping[str, Any], payload: bytes = b"") -> None:
    """Kirim satu frame utuh."""
    sock.sendall(encode_frame(header, payload))


def recv_msg(sock: socket.socket) -> Frame:
    """Terima satu frame: prefix, header, lalu payload."""
    prefix = recv_exact(sock, constants.FRAME_PREFIX_SIZE)
    header_len, payload_len = decode_frame_prefix(prefix)
    header = decode_header(recv_exact(sock, header_len))
    payload = recv_exact(sock, payload_len) if payload_len else b""
    return Frame(header=header, payload=payload)


def connect_with_retry(
    host: str,
    port: int,
    *,
    attempts: int = constants.DEFAULT_CONNECT_ATTEMPTS,
    timeout: float = constants.DEFAULT_CONNECT_TIMEOUT,
    backoff_min: float = constants.DEFAULT_CONNECT_BACKOFF_MIN,
    backoff_max: float = constants.DEFAULT_CONNECT_BACKOFF_MAX,
    connect_fn: ConnectFn | None = None,
    sleep_fn: SleepFn | None = None,
) -> socket.socket:
    """Connect dengan retry dan backoff eksponensial (PROTOCOL.md bagian 4)."""
    connector = connect_fn if connect_fn is not None else socket.create_connection
    sleeper = sleep_fn if sleep_fn is not None else time.sleep
    delay = backoff_min
    last_error: OSError | None = None

    for attempt in range(1, attempts + 1):
        try:
            return connector((host, port), timeout)
        except OSError as exc:
            last_error = exc
            if attempt == attempts:
                break
            sleeper(delay)
            delay = min(delay * 2, backoff_max)

    raise ConnectionError(
        f"gagal connect ke {host}:{port} setelah {attempts} percobaan: {last_error}"
    )


def close_quietly(sock: socket.socket) -> None:
    """Tutup socket tanpa melempar error."""
    with contextlib.suppress(OSError):
        sock.close()
