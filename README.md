# ZipHive

Kompresi data terdistribusi dengan arsitektur Master-Worker. Proyek UAS mata kuliah Komputasi
Paralel dan Sistem Terdistribusi, Informatika, Universitas Siliwangi (Tema 16).

Status: Fase 0 selesai (bootstrap repo dan tooling). Seluruh aturan kerja ada di `AGENTS.md`,
`PLAN.md`, dan `SDLC.md`.

## Kebutuhan

- Python 3.11 atau lebih baru
- Dependensi runtime: `psutil`
- Dependensi dev: pytest, pytest-cov, pytest-timeout, ruff, mypy, types-psutil

## Setup

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
```

Isi identitas kelompok di `config/group.toml` (placeholder `<ISI ...>`). Nilai tersebut dipakai
banner setiap program CLI.

## Perintah

| Perintah | Fungsi |
|---|---|
| `python -m pcomp --version` | cetak versi |
| `python -m pcomp` | cetak banner identitas kelompok |
| `python scripts/gate.py` | Verification Gate penuh G1-G9 |
| `python scripts/gate.py --quick` | lint + unit test |
| `python -m pytest -m "not integration and not perf and not slow"` | unit test |
| `python -m pytest -m integration` | integration test |

Ringkasan gate terakhir disimpan di `reports/gate-latest.txt`.

## Struktur

```
config/    group.toml master.toml worker.toml nodes.toml
src/pcomp/ constants.py banner.py (modul aplikasi menyusul per fase)
scripts/   gate.py
tests/     unit/ integration/ conftest.py
docs/      phase-logs/
results/   raw/ figures/
data/ output/ reports/   (lokal, tidak masuk repo)
```

## Dokumen

| Dokumen | Isi |
|---|---|
| `AGENTS.md` | instruksi wajib agent |
| `PLAN.md` | rencana dan status per fase |
| `SDLC.md` | siklus kerja, gate, aturan git |
| `ARCHITECTURE.md` | arsitektur sistem |
| `FLOW.md` | alur sistem |
| `PROTOCOL.md` | protokol Master-Worker |
| `TESTING.md` | strategi pengujian |
| `EXPERIMENTS.md` | rancangan eksperimen dan metrik |
| `DEPLOYMENT.md` | deployment 10 node |
| `SUBMISSION.md` | paket pengumpulan |
| `DECISIONS.md` | catatan keputusan desain |
| `CHANGELOG.md` | riwayat perubahan |
| `ASSETS.md` | sumber aset |
| `PROMPTS.md` | urutan prompt kerja agent |
