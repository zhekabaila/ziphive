# ZipHive

Kompresi data terdistribusi dengan arsitektur Master-Worker. Dataset dipecah menjadi chunk
(task), Master membagikan task ke Worker lewat TCP, setiap Worker mengompresi task secara paralel
dengan `multiprocessing`, lalu Master mengumpulkan hasil dan memverifikasinya dengan SHA-256.

Proyek UAS mata kuliah Komputasi Paralel dan Sistem Terdistribusi, Informatika, Universitas
Siliwangi (Tema 16). Identitas kelompok dibaca dari `config/group.toml`.

## Status

| Bagian | Kondisi |
|---|---|
| Fase 0-9 | Selesai. Tag terakhir `phase-09-done` |
| Eksperimen resmi | 45 run (E1-E6, 3 ulangan) pada 10 node virtual; seluruh run `VERIFY OK`; `validate_results results/raw` mencetak `RESULTS VALID` |
| Hasil | `results/summary.csv`, `results/summary_agg.csv`, 7 grafik di `results/figures/` |
| Fase 10 | Selesai. Versi `1.0.0`, laporan DOCX, naskah video (`docs/DEMO_SCRIPT.md`), dan ZIP sumber di `dist/` |

Soal meminta minimal 10 node fisik. Pelaksanaan 2026-11-22 memakai 10 node virtual di satu laptop
(1 Master di host + 9 Worker container, ADR-015). Deviasi ini diungkap di laporan dan video.

## Kebutuhan

- Python 3.11 atau lebih baru di semua node
- Dependensi runtime: `psutil`
- Dependensi dev: pytest, pytest-cov, pytest-timeout, ruff, mypy, types-psutil
- Dependensi analisis/grafik: matplotlib

## Setup

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev,analysis]"
```

Untuk node Worker yang hanya menjalankan kompresi, cukup dependensi runtime:

```bash
python -m pip install -r requirements-worker.txt
```

Isi identitas kelompok di `config/group.toml` bila masih berupa placeholder. Banner setiap CLI
membaca berkas itu; program tetap berjalan dengan peringatan bila placeholder belum diisi.

## Mulai cepat

```bash
# 1. Dataset sintetis 20 MiB
python -m pcomp.tools.make_dataset --out data/synth --size-mb 20 --seed 1 --files 4

# 2. Baseline satu proses, lalu verifikasi
python -m pcomp.sequential --input data/synth --out output/seq
python -m pcomp.tools.verify --manifest output/seq/manifest.json

# 3. Baseline paralel satu mesin, lalu verifikasi
python -m pcomp.local_parallel --input data/synth --out output/local --procs 4
python -m pcomp.tools.verify --manifest output/local/manifest.json

# 4. End-to-end 1 Master + 3 Worker di localhost
python scripts/e2e_local.py --workers 3
```

Keluaran yang diharapkan: `SEQUENTIAL OK`, `VERIFY OK`, `LOCAL OK`, `VERIFY OK`, `E2E OK`.

## Perintah

### Program utama

| Perintah | Fungsi |
|---|---|
| `python -m pcomp` | cetak banner identitas kelompok |
| `python -m pcomp --version` | cetak versi paket |
| `python -m pcomp.master --input DIR --out DIR` | jalankan Master |
| `python -m pcomp.worker --master HOST:PORT --id wN` | jalankan Worker |
| `python -m pcomp.sequential --input DIR --out DIR` | baseline satu proses (E1) |
| `python -m pcomp.local_parallel --input DIR --out DIR --procs P` | baseline paralel satu mesin (E2) |
| `python -m pcomp.bench.runner --exp E1..E6 --local` | harness benchmark |
| `python -m pcomp.bench.runner --exp E3 --lan` | Master untuk Worker di node lain |

Opsi Master: `--config`, `--host`, `--port`, `--input`, `--out`, `--algo`, `--level`,
`--chunk-mb`, `--repeat`, `--expect-workers`, `--scheduler static|dynamic`,
`--heartbeat-interval`, `--heartbeat-timeout`, `--max-attempts`, `--barrier-timeout`.
Opsi Worker: `--config`, `--master`, `--id`, `--procs`, `--throttle`, `--fail-after-tasks`,
`--fail-after-sec`, `--task-fail-rate`, `--seed`, `--protocol-version`.
Nilai default ada di `config/master.toml` dan `config/worker.toml`; CLI menimpa nilai TOML.

### Alat bantu

| Perintah | Fungsi |
|---|---|
| `python -m pcomp.tools.make_dataset --out DIR --size-mb N` | buat dataset sintetis deterministik |
| `python -m pcomp.tools.verify --manifest FILE` | verifikasi chunk terhadap manifest |
| `python -m pcomp.tools.validate_results results/raw` | validasi kelengkapan hasil resmi |
| `python -m pcomp.tools.inject_failure --events FILE --pid PID` | matikan Worker dari luar |
| `python -m pcomp.tools.download_corpus --url URL --out DIR` | unduh korpus resmi |
| `python scripts/check_node.py --master HOST:PORT` | periksa kesiapan node |
| `python scripts/launch_workers.py --print` | cetak perintah Worker dari `config/nodes.toml` |
| `python scripts/pack_source.py` | buat ZIP sumber di `dist/` |
| `python scripts/build_report.py` | bangun laporan DOCX di `reports/laporan/` |
| `python scripts/smoke_package.py` | bangun ZIP, periksa isinya, lalu jalankan dari nol (smoke gate Fase 10) |
| `python scripts/run_experiments.py --exps E1,E2,E3,E4,E5,E6` | orkestrasi E1-E6 pada 10 node virtual |

### Test dan gate

| Perintah | Fungsi |
|---|---|
| `python -m pytest -m "not integration and not perf and not slow"` | unit test |
| `python -m pytest -m integration` | integration test |
| `python -m pytest -m slow` | uji 9 Worker lokal |
| `python scripts/gate.py --quick` | lint + unit test |
| `python scripts/gate.py` | Verification Gate penuh G1-G9 (wajib sebelum commit) |

Bila paket belum dipasang (`pip install -e .`), jalankan dengan `PYTHONPATH=src`, misalnya
`PYTHONPATH=src python scripts/gate.py`.

## Struktur repo

```
src/pcomp/            kode utama (Master, Worker, protokol, kompresi, metrik, harness)
tests/unit/           unit test per modul
tests/integration/    test dengan proses dan socket nyata
scripts/              gate, e2e, check_node, launch_workers, pack_source, run_experiments
config/               group.toml, master.toml, worker.toml, nodes.toml
docs/                 CODE_GUIDE.md, ANALYSIS.md, phase-logs/, evidence/
results/              raw/, summary.csv, summary_agg.csv, figures/, dev/ (hasil sim)
data/                 dataset (tidak masuk repo)
output/               keluaran run (tidak masuk repo)
```

Penjelasan setiap modul, class, dan fungsi penting ada di `docs/CODE_GUIDE.md`. Rancangan
komponen ada di `ARCHITECTURE.md`, alur kejadian di `FLOW.md`, dan format pesan di `PROTOCOL.md`.

## Menjalankan di 10 node virtual

1. Siapkan Master di host (Python 3.11+, `psutil`). Contoh:

   ```bash
   python -m pcomp.master --input data/bench --out output/run1 \
     --expect-workers 9 --scheduler dynamic --host 0.0.0.0 --port 5050
   ```

2. Siapkan sembilan Worker sebagai container dari image yang sama, dengan `PYTHONPATH` menunjuk
   ke kode di dalam container. Contoh satu Worker:

   ```bash
   docker run -d --name ziphive-w1 --hostname w1 \
     -v "$PWD":/app:ro -e PYTHONPATH=/app/src -w /app ziphive-node:min \
     python3 -m pcomp.worker --master host.docker.internal:5050 --id w1 --procs 1
   ```

3. Tunggu sampai Master mencetak `MASTER OK` dan setiap Worker mencetak `WORKER OK (wN)`.
   Verifikasi hasil dengan `python -m pcomp.tools.verify --manifest output/run1/manifest.json`.

Prosedur lengkap, termasuk pemeriksaan `docker ps` dan pengambilan tangkapan layar bukti, ada di
`docs/evidence/RUNBOOK.md`. Ringkasan status gambar bukti ada di `docs/evidence/README.md`.
Untuk sepuluh node fisik, lengkapi `config/nodes.toml` lalu pakai `scripts/launch_workers.py`
(lihat `DEPLOYMENT.md`).

## Hasil eksperimen

Hasil resmi hanya berasal dari `results/raw/` dan diringkas ke `results/summary.csv` serta
`results/summary_agg.csv`. Validasi cepat:

```bash
python -m pcomp.tools.validate_results results/raw
```

Keluaran terakhir: 45 run (E1 3, E2 12, E3 3, E4 6, E5 6, E6 15), seluruhnya `VERIFY OK`, dan
`RESULTS VALID`. Analisis beserta angka per eksperimen ada di `docs/ANALYSIS.md`. Hasil algoritma
`sim` hanya untuk test dan disimpan terpisah di `results/dev/`, tidak dipakai di laporan.

## Dokumentasi

| Berkas | Isi |
|---|---|
| `AGENTS.md` | aturan kerja agent |
| `PLAN.md` | rencana dan status per fase |
| `SDLC.md` | siklus pengembangan, gate, aturan commit |
| `ARCHITECTURE.md` | komponen, state machine, pembagian proses |
| `FLOW.md` | urutan kejadian Master-Worker |
| `PROTOCOL.md` | format frame dan pesan |
| `EXPERIMENTS.md` | rancangan E1-E6 dan metrik |
| `DEPLOYMENT.md` | persiapan node dan checklist |
| `TESTING.md` | strategi pengujian |
| `ASSETS.md` | sumber dataset, pustaka, formula, lisensi |
| `docs/CODE_GUIDE.md` | panduan kode per modul dan perintah |
| `docs/ANALYSIS.md` | analisis hasil eksperimen |
| `docs/DEMO_SCRIPT.md` | naskah video demo maksimal 5 menit dan checklist rekaman |
| `SUBMISSION.md` | isi paket pengumpulan |

## Paket pengumpulan

```bash
python scripts/build_report.py      # laporan DOCX di reports/laporan/
python scripts/pack_source.py       # ZIP sumber di dist/
python scripts/smoke_package.py     # periksa isi ZIP lalu jalankan dari nol
```

Laporan memakai angka dari `results/summary.csv` dan `docs/ANALYSIS.md`, sedangkan naskah video
demo ada di `docs/DEMO_SCRIPT.md`. Gambar yang belum tersedia tetap ditandai kotak placeholder di
dalam laporan beserta instruksi pengambilannya.

## Catatan

- Dataset tidak masuk repo. Dataset sintetis dibuat ulang dengan `make_dataset` (seed dan SHA-256
  dicatat di `ASSETS.md`); korpus Silesia/Canterbury diunduh lewat `download_corpus.py` dari URL
  resmi.
- Seluruh proses inti memakai `spawn` dan dapat dihentikan dengan bersih; setiap socket memiliki
  timeout.
- Hasil algoritma `sim` tidak boleh dipakai sebagai data laporan.
