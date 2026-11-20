"""Konstanta global paket pcomp (AGENTS.md bagian 4)."""

from __future__ import annotations

from pathlib import Path

PROJECT_NAME = "ZipHive"
PACKAGE_NAME = "pcomp"
__version__ = "0.00.0"

# Versi format pesan; naikkan bila format berubah (PROTOCOL.md).
PROTOCOL_VERSION = 1

# Lokasi default konfigurasi; dapat ditimpa lewat argumen CLI.
DEFAULT_GROUP_CONFIG = Path("config") / "group.toml"

EXIT_OK = 0
EXIT_ERROR = 1
