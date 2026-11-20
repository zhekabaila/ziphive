"""UT-CFG-01..02: pemuatan TOML dan override dari argumen CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from pcomp.config import ConfigError, load_master_config, load_toml, load_worker_config


def test_load_toml(tmp_path: Path) -> None:
    """UT-CFG-01: file TOML terbaca menjadi dict."""
    path = tmp_path / "contoh.toml"
    path.write_text('host = "127.0.0.1"\nport = 6000\n', encoding="utf-8")
    assert load_toml(path) == {"host": "127.0.0.1", "port": 6000}


def test_load_toml_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_toml(tmp_path / "tidak-ada.toml")


def test_load_toml_invalid(tmp_path: Path) -> None:
    path = tmp_path / "rusak.toml"
    path.write_text("ini bukan = = toml", encoding="utf-8")
    with pytest.raises(ConfigError):
        load_toml(path)


def test_master_defaults_from_repo(repo_root: Path) -> None:
    """UT-CFG-01b: config/master.toml bawaan repo dapat dimuat."""
    config = load_master_config(repo_root / "config" / "master.toml")
    assert config.port == 5050
    assert config.algo == "lzma"
    assert config.level == 6
    assert config.chunk_mb == 4
    assert config.scheduler == "dynamic"
    assert config.expect_workers == 9
    assert config.heartbeat_interval == 2.0
    assert config.heartbeat_timeout == 6.0
    assert config.max_attempts == 3


def test_worker_defaults_from_repo(repo_root: Path) -> None:
    config = load_worker_config(repo_root / "config" / "worker.toml")
    assert config.worker_id == "w1"
    assert config.procs == 4
    assert config.throttle == 1.0
    assert config.seed == 0


def test_cli_override_master(repo_root: Path) -> None:
    """UT-CFG-02: nilai CLI menimpa TOML, nilai None diabaikan."""
    config = load_master_config(
        repo_root / "config" / "master.toml",
        overrides={"port": 6000, "scheduler": "static", "level": None},
    )
    assert config.port == 6000
    assert config.scheduler == "static"
    assert config.level == 6


def test_cli_override_worker(repo_root: Path) -> None:
    config = load_worker_config(
        repo_root / "config" / "worker.toml",
        overrides={"procs": 8, "worker_id": "w9"},
    )
    assert config.procs == 8
    assert config.worker_id == "w9"


def test_invalid_port_rejected(repo_root: Path) -> None:
    with pytest.raises(ConfigError):
        load_master_config(repo_root / "config" / "master.toml", overrides={"port": 0})


def test_invalid_scheduler_rejected(repo_root: Path) -> None:
    with pytest.raises(ConfigError):
        load_master_config(repo_root / "config" / "master.toml", overrides={"scheduler": "acak"})


def test_invalid_procs_rejected(repo_root: Path) -> None:
    with pytest.raises(ConfigError):
        load_worker_config(repo_root / "config" / "worker.toml", overrides={"procs": 0})


def test_missing_field_rejected(tmp_path: Path) -> None:
    path = tmp_path / "kurang.toml"
    path.write_text('host = "0.0.0.0"\n', encoding="utf-8")
    with pytest.raises(ConfigError):
        load_master_config(path)


def test_wrong_type_rejected(repo_root: Path) -> None:
    with pytest.raises(ConfigError):
        load_master_config(repo_root / "config" / "master.toml", overrides={"port": "5050"})
