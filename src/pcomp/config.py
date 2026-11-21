"""Pemuatan konfigurasi TOML dengan override dari argumen CLI (PLAN.md P1-T3)."""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pcomp import constants

VALID_SCHEDULERS = ("static", "dynamic")


class ConfigError(ValueError):
    """Nilai konfigurasi tidak valid."""


@dataclass(frozen=True)
class MasterConfig:
    """Konfigurasi Master (ARCHITECTURE.md bagian 10)."""

    host: str
    port: int
    input: str
    out: str
    algo: str
    level: int
    chunk_mb: int
    repeat: int
    scheduler: str
    expect_workers: int
    heartbeat_interval: float
    heartbeat_timeout: float
    max_attempts: int


@dataclass(frozen=True)
class WorkerConfig:
    """Konfigurasi Worker (ARCHITECTURE.md bagian 10)."""

    master: str
    worker_id: str
    procs: int
    throttle: float
    fail_after_tasks: int
    fail_after_sec: float
    task_fail_rate: float
    seed: int


def load_toml(path: Path) -> dict[str, Any]:
    """Muat file TOML; FileNotFoundError bila tidak ada, ConfigError bila rusak."""
    if not path.is_file():
        raise FileNotFoundError(f"file konfigurasi tidak ditemukan: {path}")
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"TOML tidak valid di {path}: {exc}") from exc


def _merged(
    path: Path | None,
    default_path: Path,
    overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Gabungkan isi TOML dengan override CLI; nilai None diabaikan."""
    data = dict(load_toml(path if path is not None else default_path))
    if overrides is not None:
        for key, value in overrides.items():
            if value is not None:
                data[key] = value
    return data


def _get_str(data: Mapping[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str):
        raise ConfigError(f"field '{key}' wajib berupa string")
    return value


def _get_int(data: Mapping[str, Any], key: str) -> int:
    value = data.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ConfigError(f"field '{key}' wajib berupa int")
    return value


def _get_float(data: Mapping[str, Any], key: str) -> float:
    value = data.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"field '{key}' wajib berupa angka")
    return float(value)


def _validate_master(config: MasterConfig) -> None:
    if not config.host:
        raise ConfigError("field 'host' tidak boleh kosong")
    if not 1 <= config.port <= 65535:
        raise ConfigError(f"port {config.port} di luar rentang 1-65535")
    if not config.algo:
        raise ConfigError("field 'algo' tidak boleh kosong")
    if not 0 <= config.level <= 9:
        raise ConfigError(f"level {config.level} di luar rentang 0-9")
    if config.chunk_mb < 1:
        raise ConfigError("chunk_mb minimal 1")
    if config.repeat < 1:
        raise ConfigError("repeat minimal 1")
    if config.scheduler not in VALID_SCHEDULERS:
        raise ConfigError(f"scheduler '{config.scheduler}' harus salah satu {VALID_SCHEDULERS}")
    if config.expect_workers < 1:
        raise ConfigError("expect_workers minimal 1")
    if config.heartbeat_interval <= 0:
        raise ConfigError("heartbeat_interval harus lebih besar dari 0")
    if config.heartbeat_timeout <= 0:
        raise ConfigError("heartbeat_timeout harus lebih besar dari 0")
    if config.max_attempts < 1:
        raise ConfigError("max_attempts minimal 1")


def _validate_worker(config: WorkerConfig) -> None:
    if not config.master:
        raise ConfigError("field 'master' tidak boleh kosong")
    if not config.worker_id:
        raise ConfigError("field 'worker_id' tidak boleh kosong")
    if config.procs < 1:
        raise ConfigError("procs minimal 1")
    if config.throttle < 0:
        raise ConfigError("throttle tidak boleh negatif")
    if config.fail_after_tasks < 0:
        raise ConfigError("fail_after_tasks tidak boleh negatif")
    if config.fail_after_sec < 0:
        raise ConfigError("fail_after_sec tidak boleh negatif")
    if not 0.0 <= config.task_fail_rate <= 1.0:
        raise ConfigError("task_fail_rate harus di antara 0 dan 1")


def load_master_config(
    path: Path | None = None, overrides: Mapping[str, Any] | None = None
) -> MasterConfig:
    """Muat konfigurasi Master lalu timpa dengan nilai CLI."""
    data = _merged(path, constants.DEFAULT_MASTER_CONFIG, overrides)
    config = MasterConfig(
        host=_get_str(data, "host"),
        port=_get_int(data, "port"),
        input=_get_str(data, "input"),
        out=_get_str(data, "out"),
        algo=_get_str(data, "algo"),
        level=_get_int(data, "level"),
        chunk_mb=_get_int(data, "chunk_mb"),
        repeat=_get_int(data, "repeat"),
        scheduler=_get_str(data, "scheduler"),
        expect_workers=_get_int(data, "expect_workers"),
        heartbeat_interval=_get_float(data, "heartbeat_interval"),
        heartbeat_timeout=_get_float(data, "heartbeat_timeout"),
        max_attempts=_get_int(data, "max_attempts"),
    )
    _validate_master(config)
    return config


def load_worker_config(
    path: Path | None = None, overrides: Mapping[str, Any] | None = None
) -> WorkerConfig:
    """Muat konfigurasi Worker lalu timpa dengan nilai CLI."""
    data = _merged(path, constants.DEFAULT_WORKER_CONFIG, overrides)
    config = WorkerConfig(
        master=_get_str(data, "master"),
        worker_id=_get_str(data, "worker_id"),
        procs=_get_int(data, "procs"),
        throttle=_get_float(data, "throttle"),
        fail_after_tasks=_get_int(data, "fail_after_tasks"),
        fail_after_sec=_get_float(data, "fail_after_sec"),
        task_fail_rate=_get_float(data, "task_fail_rate"),
        seed=_get_int(data, "seed"),
    )
    _validate_worker(config)
    return config
