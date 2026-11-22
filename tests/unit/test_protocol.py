"""UT-PRO-01..06: frame protokol sesuai PROTOCOL.md bagian 1."""

from __future__ import annotations

import json
import struct

import pytest

from pcomp import constants
from pcomp.protocol import (
    BadFrameError,
    ErrorCode,
    MessageType,
    UnknownMessageTypeError,
    VersionMismatchError,
    build_frame,
    decode_frame_prefix,
    decode_header,
    encode_frame,
    encode_header,
    make_header,
    validate_message,
)


def test_roundtrip_with_payload() -> None:
    """UT-PRO-01: frame dengan payload kembali utuh dan formatnya persis 4+8+N+M."""
    header = make_header(MessageType.REQUEST, credits=2)
    data = encode_frame(header, b"isi-chunk")

    header_len = struct.unpack("!I", data[0:4])[0]
    payload_len = struct.unpack("!Q", data[4:12])[0]
    assert header_len == len(data) - 12 - payload_len
    assert payload_len == len(b"isi-chunk")
    assert json.loads(data[12 : 12 + header_len].decode("utf-8")) == {
        "type": "REQUEST",
        "v": constants.PROTOCOL_VERSION,
        "credits": 2,
    }
    assert data[12 + header_len :] == b"isi-chunk"


def test_roundtrip_without_payload() -> None:
    """UT-PRO-02: payload kosong ditulis sebagai M = 0."""
    data = encode_frame(make_header(MessageType.SHUTDOWN, reason="selesai"))
    assert struct.unpack("!Q", data[4:12])[0] == 0


def test_truncated_prefix_rejected() -> None:
    """UT-PRO-03: prefix kurang dari 12 byte ditolak."""
    with pytest.raises(BadFrameError):
        decode_frame_prefix(b"\x00\x00\x00")


def test_header_limit_enforced() -> None:
    """UT-PRO-04: header melebihi 64 KiB ditolak saat decode maupun encode."""
    too_big = constants.MAX_HEADER_BYTES + 1
    prefix = struct.pack("!I", too_big) + struct.pack("!Q", 0)
    with pytest.raises(BadFrameError):
        decode_frame_prefix(prefix)

    huge_header = {"type": "ERROR", "v": 1, "message": "x" * constants.MAX_HEADER_BYTES}
    with pytest.raises(BadFrameError):
        encode_header(huge_header)


def test_payload_limit_enforced() -> None:
    """UT-PRO-04b: payload melebihi 64 MiB ditolak."""
    prefix = struct.pack("!I", 2) + struct.pack("!Q", constants.MAX_PAYLOAD_BYTES + 1)
    with pytest.raises(BadFrameError):
        decode_frame_prefix(prefix)

    class OversizedPayload(bytes):
        def __len__(self) -> int:
            return constants.MAX_PAYLOAD_BYTES + 1

    with pytest.raises(BadFrameError):
        encode_frame({"type": "TASK", "v": 1}, OversizedPayload(b""))


def test_broken_json_rejected() -> None:
    """UT-PRO-05: header bukan JSON valid ditolak."""
    with pytest.raises(BadFrameError):
        decode_header(b"{bukan json")


def test_header_must_be_object() -> None:
    """UT-PRO-05b: header JSON harus objek, bukan array."""
    with pytest.raises(BadFrameError):
        decode_header(b"[1, 2, 3]")


def test_unknown_type_rejected() -> None:
    """UT-PRO-06: tipe pesan di luar tabel ditolak."""
    with pytest.raises(UnknownMessageTypeError):
        validate_message({"type": "TIDAK_ADA", "v": constants.PROTOCOL_VERSION})


def test_missing_required_field_rejected() -> None:
    """UT-PRO-06b: field wajib yang hilang ditolak."""
    with pytest.raises(BadFrameError):
        validate_message({"type": "REQUEST", "v": constants.PROTOCOL_VERSION})


def test_credits_must_be_positive() -> None:
    """UT-PRO-06c: REQUEST dengan credits 0 ditolak."""
    with pytest.raises(BadFrameError):
        validate_message({"type": "REQUEST", "v": constants.PROTOCOL_VERSION, "credits": 0})


def test_version_mismatch_detected() -> None:
    """UT-PRO-06d: versi protokol berbeda menghasilkan VersionMismatchError."""
    with pytest.raises(VersionMismatchError):
        validate_message({"type": "REGISTER", "v": 99, "worker_id": "w1"})


def test_unknown_fields_ignored() -> None:
    """PROTOCOL.md aturan 9: field tidak dikenal diabaikan."""
    header = {
        "type": "HEARTBEAT",
        "v": constants.PROTOCOL_VERSION,
        "ts": 1.0,
        "cpu_percent": 1.0,
        "mem_percent": 2.0,
        "inflight": 0,
        "field_baru": "abaikan",
    }
    assert validate_message(header) is MessageType.HEARTBEAT


def test_all_message_types_defined() -> None:
    """Seluruh tipe pada PROTOCOL.md bagian 2 tersedia di enum."""
    expected = {
        "REGISTER",
        "REGISTER_ACK",
        "REQUEST",
        "TASK",
        "RESULT",
        "HEARTBEAT",
        "HEARTBEAT_ACK",
        "SHUTDOWN",
        "BYE",
        "ERROR",
        "KILL",
    }
    assert {member.value for member in MessageType} == expected


def test_error_codes_defined() -> None:
    """Seluruh kode error pada PROTOCOL.md bagian 2 tersedia di enum."""
    expected = {
        "VERSION_MISMATCH",
        "DUPLICATE_WORKER",
        "SERVER_FULL",
        "BAD_FRAME",
        "UNKNOWN_TYPE",
        "INTERNAL",
    }
    assert {member.value for member in ErrorCode} == expected


def test_build_frame_validates() -> None:
    """build_frame menolak field wajib yang hilang."""
    with pytest.raises(BadFrameError):
        build_frame(MessageType.TASK, task_id=1)


def test_kill_header_requires_worker_and_reason() -> None:
    """UT-PRO-07: pesan KILL versi 2 wajib memuat worker_id dan reason."""
    header = make_header(MessageType.KILL, worker_id="w3", reason="master-kill")
    assert validate_message(header) is MessageType.KILL

    with pytest.raises(BadFrameError):
        validate_message({"type": "KILL", "v": constants.PROTOCOL_VERSION, "worker_id": "w3"})
    with pytest.raises(BadFrameError):
        validate_message({"type": "KILL", "v": constants.PROTOCOL_VERSION, "reason": "x"})
