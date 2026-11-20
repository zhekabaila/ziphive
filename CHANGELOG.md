# Changelog

Format mengikuti Keep a Changelog. Versi `0.<NN>.0` = akhir fase NN. Aturan pencatatan: SDLC.md bagian 6.

## [Unreleased]
### Added
- (kosong)

## [0.01.0] - 2026-11-20
### Added
- `src/pcomp/protocol.py`: frame `!I` (4 byte) + `!Q` (8 byte) + header JSON + payload, batas 64 KiB dan 64 MiB, enum `MessageType` dan `ErrorCode`, validasi field per PROTOCOL.md bagian 2.
- `src/pcomp/net.py`: `recv_exact`, `send_msg`, `recv_msg`, `connect_with_retry` (backoff 0.5 sampai 5 detik), `close_quietly`.
- `src/pcomp/config.py`: `MasterConfig`, `WorkerConfig`, `load_toml`, override nilai CLI, validasi tipe dan rentang.
- `src/pcomp/logging_setup.py`: `setup_logging` idempoten dengan handler stream dan opsional file.
- `src/pcomp/metrics/events.py`: `EventLog` JSONL thread-safe (`ts`, `event`, field bebas) dan `read_events`.
- `src/pcomp/constants.py`: batas frame, tipe struct, dan nilai default timeout protokol.
- Unit test UT-PRO-01..06, UT-NET-01..03, UT-CFG-01..02, UT-EVT-01, UT-LOG-01 dan integration test IT-ECHO-01 (payload 10 MiB).

### Changed
- `__version__` dan versi `pyproject.toml` menjadi `0.01.0`; ditambah test kesesuaian keduanya.
- `scripts/gate.py`: smoke Fase 1 (`pytest -m integration -k echo`) dan penanda phase log tambahan.
- `TESTING.md` bagian 4: tambah baris UT-LOG-01.

## [0.00.0] - 2026-11-20
### Added
- Bootstrap repo: `pyproject.toml`, `requirements.txt`, `requirements-worker.txt`, `requirements-dev.txt`, `Makefile`, `.gitignore`.
- Struktur paket `src/pcomp` beserta subpaket `master`, `worker`, `metrics`, `bench`, dan `tools` (masih kosong, diisi fase berikutnya).
- `src/pcomp/constants.py` (PROJECT_NAME, `__version__`, `PROTOCOL_VERSION = 1`) dan `src/pcomp/banner.py` yang membaca identitas dari `config/group.toml`.
- CLI `python -m pcomp` (banner) dan `python -m pcomp --version`.
- `scripts/gate.py`: Verification Gate G1 sampai G9, mode `--quick`, ringkasan ditulis ke `reports/gate-latest.txt`.
- Konfigurasi default `config/group.toml` (placeholder), `config/master.toml`, `config/worker.toml`, `config/nodes.toml`.
- Unit test UT-BOOT-01 sampai UT-BOOT-05, integration test IT-BOOT-01, dan fixture `tests/conftest.py`.
- `README.md`: kebutuhan, setup, perintah standar, struktur repo, daftar dokumen.

### Changed
- `_TEMPLATE.md` dipindah ke `docs/phase-logs/_TEMPLATE.md` agar sesuai path pada SDLC.md bagian 1 dan 6.
- `TESTING.md` bagian 4: ditambah baris UT-BOOT dan IT-BOOT untuk fase bootstrap.

## [0.0.0] - perencanaan
### Docs
- Dokumen perencanaan dibuat: AGENTS, PLAN, ARCHITECTURE, FLOW, PROTOCOL, SDLC, TESTING, EXPERIMENTS, DEPLOYMENT, ASSETS, SUBMISSION, DECISIONS, PROMPTS (urutan prompt agent). Nama proyek: ZipHive.
