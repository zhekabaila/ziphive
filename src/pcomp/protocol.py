"""Frame dan pesan protokol Master-Worker (PROTOCOL.md bagian 1 dan 2)."""

from __future__ import annotations

import json
import struct
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any, cast

from pcomp import constants


class ProtocolError(Exception):
    """Kesalahan umum protokol."""


class BadFrameError(ProtocolError):
    """Frame tidak valid: prefix, batas ukuran, atau header JSON."""


class UnknownMessageTypeError(ProtocolError):
    """Tipe pesan tidak ada pada PROTOCOL.md bagian 2."""


class VersionMismatchError(ProtocolError):
    """Versi protokol pengirim berbeda dengan versi lokal."""


class MessageType(StrEnum):
    """Tipe pesan yang diizinkan protokol versi 1."""

    REGISTER = "REGISTER"
    REGISTER_ACK = "REGISTER_ACK"
    REQUEST = "REQUEST"
    TASK = "TASK"
    RESULT = "RESULT"
    HEARTBEAT = "HEARTBEAT"
    HEARTBEAT_ACK = "HEARTBEAT_ACK"
    SHUTDOWN = "SHUTDOWN"
    BYE = "BYE"
    ERROR = "ERROR"


class ErrorCode(StrEnum):
    """Kode error pada pesan ERROR."""

    VERSION_MISMATCH = "VERSION_MISMATCH"
    DUPLICATE_WORKER = "DUPLICATE_WORKER"
    BAD_FRAME = "BAD_FRAME"
    UNKNOWN_TYPE = "UNKNOWN_TYPE"
    INTERNAL = "INTERNAL"


@dataclass(frozen=True)
class Frame:
    """Satu frame protokol: header terurai dan payload biner."""

    header: dict[str, Any]
    payload: bytes


def _is_str(value: object) -> bool:
    return isinstance(value, str)


def _is_str_or_none(value: object) -> bool:
    return value is None or isinstance(value, str)


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_bool(value: object) -> bool:
    return isinstance(value, bool)


def _is_int_or_str(value: object) -> bool:
    return _is_int(value) or _is_str(value)


Validator = Callable[[object], bool]

# Field wajib per tipe pesan sesuai PROTOCOL.md bagian 2.
REQUIRED_FIELDS: dict[MessageType, dict[str, Validator]] = {
    MessageType.REGISTER: {
        "worker_id": _is_str,
        "hostname": _is_str,
        "cores": _is_int,
        "procs": _is_int,
        "version": _is_int_or_str,
    },
    MessageType.REGISTER_ACK: {
        "accepted": _is_bool,
        "reason": _is_str,
        "heartbeat_interval": _is_number,
        "algo": _is_str,
        "level": _is_int,
    },
    MessageType.REQUEST: {"credits": _is_int},
    MessageType.TASK: {
        "task_id": _is_int_or_str,
        "file": _is_str,
        "index": _is_int,
        "algo": _is_str,
        "level": _is_int,
        "orig_size": _is_int,
        "sha256": _is_str,
    },
    MessageType.RESULT: {
        "task_id": _is_int_or_str,
        "ok": _is_bool,
        "orig_size": _is_int,
        "comp_size": _is_int,
        "sha256_in": _is_str,
        "compute_sec": _is_number,
        "error": _is_str_or_none,
    },
    MessageType.HEARTBEAT: {
        "ts": _is_number,
        "cpu_percent": _is_number,
        "mem_percent": _is_number,
        "inflight": _is_int,
    },
    MessageType.HEARTBEAT_ACK: {"ts": _is_number},
    MessageType.SHUTDOWN: {"reason": _is_str},
    MessageType.BYE: {"worker_id": _is_str},
    MessageType.ERROR: {"code": _is_str, "message": _is_str},
}


def make_header(msg_type: MessageType | str, **fields: Any) -> dict[str, Any]:
    """Bangun header dengan `type` dan `v` sesuai PROTOCOL.md."""
    type_value = msg_type.value if isinstance(msg_type, MessageType) else msg_type
    header: dict[str, Any] = {"type": type_value, "v": constants.PROTOCOL_VERSION}
    header.update(fields)
    return header


def encode_header(header: Mapping[str, Any]) -> bytes:
    """Serialisasi header ke UTF-8 JSON dan periksa batas 64 KiB."""
    try:
        raw = json.dumps(dict(header), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BadFrameError(f"header tidak dapat diserialisasi: {exc}") from exc
    if len(raw) > constants.MAX_HEADER_BYTES:
        raise BadFrameError(
            f"header {len(raw)} byte melebihi batas {constants.MAX_HEADER_BYTES} byte"
        )
    return raw


def decode_header(raw: bytes) -> dict[str, Any]:
    """Urai header JSON dan pastikan berbentuk objek."""
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BadFrameError(f"header bukan JSON valid: {exc}") from exc
    if not isinstance(parsed, dict):
        raise BadFrameError("header JSON wajib berupa objek")
    return cast("dict[str, Any]", parsed)


def decode_frame_prefix(prefix: bytes) -> tuple[int, int]:
    """Baca 4 byte panjang header dan 8 byte panjang payload, lalu periksa batas."""
    if len(prefix) < constants.FRAME_PREFIX_SIZE:
        raise BadFrameError(
            f"prefix frame {len(prefix)} byte, minimal {constants.FRAME_PREFIX_SIZE} byte"
        )
    header_len = struct.unpack(constants.HEADER_LENGTH_STRUCT, prefix[:4])[0]
    payload_len = struct.unpack(constants.PAYLOAD_LENGTH_STRUCT, prefix[4:12])[0]
    if header_len > constants.MAX_HEADER_BYTES:
        raise BadFrameError(f"header {header_len} byte melebihi batas {constants.MAX_HEADER_BYTES}")
    if payload_len > constants.MAX_PAYLOAD_BYTES:
        raise BadFrameError(
            f"payload {payload_len} byte melebihi batas {constants.MAX_PAYLOAD_BYTES}"
        )
    return header_len, payload_len


def encode_frame(header: Mapping[str, Any], payload: bytes = b"") -> bytes:
    """Susun frame: !I panjang header, !Q panjang payload, header JSON, payload."""
    header_raw = encode_header(header)
    if len(payload) > constants.MAX_PAYLOAD_BYTES:
        raise BadFrameError(
            f"payload {len(payload)} byte melebihi batas {constants.MAX_PAYLOAD_BYTES}"
        )
    prefix = struct.pack(constants.HEADER_LENGTH_STRUCT, len(header_raw))
    prefix += struct.pack(constants.PAYLOAD_LENGTH_STRUCT, len(payload))
    return prefix + header_raw + bytes(payload)


def validate_message(
    header: Mapping[str, Any], *, expected_version: int = constants.PROTOCOL_VERSION
) -> MessageType:
    """Validasi `type`, `v`, dan field wajib. Field tak dikenal diabaikan (aturan 9)."""
    type_value = header.get("type")
    if not isinstance(type_value, str):
        raise BadFrameError("header wajib memuat 'type' berupa string")
    try:
        msg_type = MessageType(type_value)
    except ValueError as exc:
        raise UnknownMessageTypeError(f"tipe pesan tidak dikenal: {type_value}") from exc

    version = header.get("v")
    if not _is_int(version):
        raise BadFrameError("header wajib memuat 'v' berupa int")
    if version != expected_version:
        raise VersionMismatchError(f"versi protokol {version} berbeda dari {expected_version}")

    for field, validator in REQUIRED_FIELDS[msg_type].items():
        if field not in header:
            raise BadFrameError(f"field '{field}' wajib ada pada {msg_type.value}")
        if not validator(header[field]):
            raise BadFrameError(f"field '{field}' tidak valid pada {msg_type.value}")

    if msg_type is MessageType.REQUEST and header["credits"] <= 0:
        raise BadFrameError("field 'credits' harus lebih besar dari 0")
    if msg_type is MessageType.ERROR:
        known_codes = {code.value for code in ErrorCode}
        if header["code"] not in known_codes:
            raise BadFrameError(f"kode error tidak dikenal: {header['code']}")
    return msg_type


def build_frame(msg_type: MessageType | str, payload: bytes = b"", **fields: Any) -> bytes:
    """Bangun dan validasi frame siap kirim."""
    header = make_header(msg_type, **fields)
    validate_message(header)
    return encode_frame(header, payload)
