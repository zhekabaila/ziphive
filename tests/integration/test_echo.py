"""IT-ECHO-01: echo server localhost, payload 10 MiB, hash sama."""

from __future__ import annotations

import hashlib
import socket
import threading

import pytest

from pcomp.net import recv_msg, send_msg

PAYLOAD_SIZE = 10 * 1024 * 1024


def _run_echo_server(server: socket.socket, ready: threading.Event) -> None:
    ready.set()
    connection, _ = server.accept()
    try:
        connection.settimeout(60.0)
        while True:
            try:
                frame = recv_msg(connection)
            except ConnectionError:
                break
            if frame.header.get("type") == "SHUTDOWN":
                break
            send_msg(connection, frame.header, frame.payload)
    finally:
        connection.close()
        server.close()


@pytest.mark.integration
def test_echo_ten_mib() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    host, port = server.getsockname()[:2]

    ready = threading.Event()
    thread = threading.Thread(target=_run_echo_server, args=(server, ready), daemon=True)
    thread.start()
    assert ready.wait(5.0)

    payload = bytes(range(256)) * (PAYLOAD_SIZE // 256)
    digest = hashlib.sha256(payload).hexdigest()

    client = socket.create_connection((host, port), timeout=60.0)
    try:
        client.settimeout(60.0)
        send_msg(client, {"type": "TASK", "v": 1, "task_id": 1}, payload)
        frame = recv_msg(client)
        assert frame.header["task_id"] == 1
        assert len(frame.payload) == PAYLOAD_SIZE
        assert hashlib.sha256(frame.payload).hexdigest() == digest

        send_msg(client, {"type": "SHUTDOWN", "v": 1, "reason": "selesai"})
    finally:
        client.close()

    thread.join(timeout=10.0)
    assert not thread.is_alive()
