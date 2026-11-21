"""Konstanta global paket pcomp (AGENTS.md bagian 4)."""

from __future__ import annotations

from pathlib import Path

PROJECT_NAME = "ZipHive"
PACKAGE_NAME = "pcomp"
__version__ = "0.05.0"

# Versi format pesan; naikkan bila format berubah (PROTOCOL.md).
PROTOCOL_VERSION = 1

# Lokasi default konfigurasi; dapat ditimpa lewat argumen CLI.
DEFAULT_GROUP_CONFIG = Path("config") / "group.toml"
DEFAULT_MASTER_CONFIG = Path("config") / "master.toml"
DEFAULT_WORKER_CONFIG = Path("config") / "worker.toml"
DEFAULT_NODES_CONFIG = Path("config") / "nodes.toml"

# Batas frame protokol (PROTOCOL.md bagian 1).
FRAME_PREFIX_SIZE = 12
HEADER_LENGTH_STRUCT = "!I"
PAYLOAD_LENGTH_STRUCT = "!Q"
MAX_HEADER_BYTES = 64 * 1024
MAX_PAYLOAD_BYTES = 64 * 1024 * 1024

# Nilai default protokol dan jaringan (PROTOCOL.md bagian 4).
DEFAULT_PORT = 5050
DEFAULT_SOCKET_TIMEOUT = 30.0
DEFAULT_CONNECT_TIMEOUT = 5.0
DEFAULT_CONNECT_ATTEMPTS = 10
DEFAULT_CONNECT_BACKOFF_MIN = 0.5
DEFAULT_CONNECT_BACKOFF_MAX = 5.0
DEFAULT_HEARTBEAT_INTERVAL = 2.0
DEFAULT_HEARTBEAT_TIMEOUT = 6.0
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BARRIER_TIMEOUT = 120.0

# Default kompresi dan task decomposition (PLAN.md bagian Default dan asumsi).
MIB = 1024 * 1024
DEFAULT_CHUNK_MB = 4
DEFAULT_REPEAT = 1
DEFAULT_ALGO = "lzma"
DEFAULT_LEVEL = 6
SIM_SECONDS_PER_MB = 0.02

# Default jumlah proses untuk baseline local parallel; sama dengan config/worker.toml.
DEFAULT_PROCS = 4

EXIT_OK = 0
EXIT_ERROR = 1
