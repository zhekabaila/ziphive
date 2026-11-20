"""UT-LOG-01: konfigurasi logging terpusat dan idempoten."""

from __future__ import annotations

import logging
from pathlib import Path

from pcomp.logging_setup import setup_logging


def test_setup_logging_is_idempotent() -> None:
    first = setup_logging(level=logging.DEBUG, logger_name="pcomp-test-idempotent")
    second = setup_logging(level=logging.INFO, logger_name="pcomp-test-idempotent")
    assert first is second
    assert len(second.handlers) == 1
    assert second.level == logging.INFO


def test_setup_logging_writes_file(tmp_path: Path) -> None:
    log_file = tmp_path / "pcomp.log"
    logger = setup_logging(level=logging.INFO, log_file=log_file, logger_name="pcomp-test-file")
    logger.info("halo dari test")
    for handler in logger.handlers:
        handler.flush()
    assert "halo dari test" in log_file.read_text(encoding="utf-8")


def test_setup_logging_accepts_string_level() -> None:
    logger = setup_logging(level="WARNING", logger_name="pcomp-test-level")
    assert logger.level == logging.WARNING
