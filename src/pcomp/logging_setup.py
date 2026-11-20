"""Konfigurasi logging terpusat (AGENTS.md bagian 4)."""

from __future__ import annotations

import logging
from pathlib import Path

DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
_HANDLER_FLAG = "_pcomp_handler"


def setup_logging(
    level: int | str = logging.INFO,
    log_file: Path | None = None,
    logger_name: str = "pcomp",
) -> logging.Logger:
    """Siapkan logger dengan handler stream dan opsional file; aman dipanggil berulang."""
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    logger.propagate = False

    for handler in list(logger.handlers):
        if getattr(handler, _HANDLER_FLAG, False):
            logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(DEFAULT_FORMAT)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    setattr(stream_handler, _HANDLER_FLAG, True)
    logger.addHandler(stream_handler)

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        setattr(file_handler, _HANDLER_FLAG, True)
        logger.addHandler(file_handler)

    return logger
