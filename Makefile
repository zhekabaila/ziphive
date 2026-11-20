# Makefile pembungkus perintah standar (AGENTS.md bagian 6).
# Windows tanpa make: jalankan perintah python di kolom kanan secara langsung.

PYTHON ?= python

.PHONY: help install install-dev lint fmt type test test-integration test-slow gate gate-quick clean

help:
	@echo "make install       : pasang paket + dependensi runtime"
	@echo "make install-dev   : pasang paket + dependensi dev"
	@echo "make lint          : ruff check dan ruff format --check"
	@echo "make fmt           : rapikan format dengan ruff"
	@echo "make type          : mypy src"
	@echo "make test          : unit test"
	@echo "make test-integration : integration test"
	@echo "make test-slow     : test bertanda slow"
	@echo "make gate          : Verification Gate penuh G1-G9"
	@echo "make gate-quick    : gate cepat (lint + unit test)"

install:
	$(PYTHON) -m pip install -e .

install-dev:
	$(PYTHON) -m pip install -e ".[dev]"

lint:
	$(PYTHON) -m ruff check .
	$(PYTHON) -m ruff format --check .

fmt:
	$(PYTHON) -m ruff format .
	$(PYTHON) -m ruff check --fix .

type:
	$(PYTHON) -m mypy src

test:
	$(PYTHON) -m pytest -m "not integration and not perf and not slow"

test-integration:
	$(PYTHON) -m pytest -m integration

test-slow:
	$(PYTHON) -m pytest -m slow

gate:
	$(PYTHON) scripts/gate.py

gate-quick:
	$(PYTHON) scripts/gate.py --quick

clean:
	$(PYTHON) -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in ('.pytest_cache', '.ruff_cache', '.mypy_cache', 'htmlcov')]"
