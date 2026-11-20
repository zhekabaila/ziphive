# Changelog

Format mengikuti Keep a Changelog. Versi `0.<NN>.0` = akhir fase NN. Aturan pencatatan: SDLC.md bagian 6.

## [Unreleased]
### Added
- (kosong)

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
