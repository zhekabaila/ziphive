"""UT-NET-01..03: helper jaringan."""

from __future__ import annotations

import socket
import threading

import pytest

from pcomp import constants
from pcomp.net import connect_with_retry, recv_exact, recv_msg, send_msg


def test_recv_exact_reads_all_bytes() -> None:
    """UT-NET-01: data yang datang terpotong-potong tetap terbaca tepat N byte."""
    left, right = socket.socketpair()
    try:
        left.settimeout(5.0)
        right.sendall(b"abc")
        right.sendall(b"defgh")
        right.sendall(b"ij")
        assert recv_exact(left, 10) == b"abcdefghij"
        assert recv_exact(left, 0) == b""
    finally:
        left.close()
        right.close()


def test_recv_exact_eof() -> None:
    """UT-NET-01b: koneksi tertutup sebelum N byte terbaca dianggap ConnectionError."""
    left, right = socket.socketpair()
    try:
        left.settimeout(5.0)
        right.sendall(b"abc")
        right.close()
        with pytest.raises(ConnectionError):
            recv_exact(left, 10)
    finally:
        left.close()


def test_recv_exact_timeout() -> None:
    """UT-NET-02: tidak ada data sampai batas waktu -> TimeoutError."""
    left, right = socket.socketpair()
    try:
        left.settimeout(0.05)
        with pytest.raises(TimeoutError):
            recv_exact(left, 4)
    finally:
        left.close()
        right.close()


def test_send_recv_roundtrip() -> None:
    """Frame yang dikirim lewat socket terbaca utuh di sisi lain."""
    left, right = socket.socketpair()
    try:
        left.settimeout(5.0)
        right.settimeout(5.0)
        payload = b"x" * 1000
        thread = threading.Thread(
            target=send_msg, args=(right, {"type": "TASK", "v": 1, "task_id": 7}, payload)
        )
        thread.start()
        frame = recv_msg(left)
        thread.join(5.0)
        assert frame.header["task_id"] == 7
        assert frame.payload == payload
    finally:
        left.close()
        right.close()


def test_recv_msg_eof() -> None:
    """recv_msg pada socket tertutup -> ConnectionError."""
    left, right = socket.socketpair()
    try:
        left.settimeout(5.0)
        right.close()
        with pytest.raises(ConnectionError):
            recv_msg(left)
    finally:
        left.close()


def test_connect_retry_succeeds_after_failures() -> None:
    """UT-NET-03: connect dicoba ulang dengan backoff sampai berhasil."""
    attempts: list[int] = []
    sleeps: list[float] = []

    class FakeSocket:
        pass

    def fake_connect(address: tuple[str, int], timeout: float) -> FakeSocket:
        attempts.append(1)
        if len(attempts) < 3:
            raise OSError("belum siap")
        return FakeSocket()

    def fake_sleep(seconds: float) -> None:
        sleeps.append(seconds)

    result = connect_with_retry(
        "127.0.0.1",
        1234,
        attempts=5,
        connect_fn=fake_connect,  # type: ignore[arg-type]
        sleep_fn=fake_sleep,
    )
    assert isinstance(result, FakeSocket)
    assert len(attempts) == 3
    assert sleeps == [constants.DEFAULT_CONNECT_BACKOFF_MIN, 1.0]


def test_connect_retry_exhausted() -> None:
    """UT-NET-03b: seluruh percobaan gagal -> ConnectionError dengan jumlah percobaan."""
    sleeps: list[float] = []

    def always_fail(address: tuple[str, int], timeout: float) -> socket.socket:
        raise OSError("mati")

    with pytest.raises(ConnectionError) as excinfo:
        connect_with_retry(
            "127.0.0.1",
            1234,
            attempts=3,
            connect_fn=always_fail,
            sleep_fn=sleeps.append,
        )
    assert "3" in str(excinfo.value)
    assert len(sleeps) == 2
