# PHASE-07 — Metrik dan harness benchmark

- Branch: phase/07-metrics-bench
- Mulai / selesai: 2026-11-21 / 2026-11-21
- Status: DONE

## 1. Tujuan
Pengukuran 6 metrik dan otomatisasi eksperimen E1 sampai E6 (PLAN.md Fase 7). Lingkup hanya
P7-T1 sampai P7-T5: sampler psutil 1 Hz (`metrics/system.py`) yang ikut heartbeat Worker dan
Master serta menulis `system.csv`, rumus metrik di `metrics/calc.py` sesuai EXPERIMENTS.md
bagian 3, harness `bench/runner.py` untuk matriks E1-E6 (localhost dan LAN), laporan
`bench/report.py` berisi tabel rata-rata/simpangan baku dan grafik PNG dengan backend Agg, serta
metadata lingkungan otomatis per run. Menjalankan eksperimen resmi, menulis analisis hasil, dan
skrip deployment node tidak termasuk fase ini.

## 2. Ringkasan hasil
Seluruh lima task fase ini selesai dan seluruh test hijau. Sampler psutil 1 Hz kini berjalan di
Master dan Worker sehingga `system.csv` pada setiap run memuat pemakaian CPU dan memori per
peran. Rumus speedup, efficiency, throughput, imbalance, detection latency, dan Recovery Time
mengikuti EXPERIMENTS.md bagian 3 dan diuji dengan nilai hitung tangan serta events sintetis.
Harness `bench/runner.py` menyusun matriks E1 sampai E6, menjalankan N ulangan pada mode
localhost atau LAN, dan menulis `summary.csv` dengan kolom persis EXPERIMENTS.md bagian 4
beserta `env.json`, `spec.json`, `system.csv`, `metrics.json`, dan log proses per run. Hasil
algoritma `sim` dipisahkan ke `results/dev/` dan tidak pernah masuk `results/raw/`.
`bench/report.py` menulis tabel agregat dan tujuh grafik PNG dengan backend `Agg`.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P7-T1 | `metrics/system.py`: sampler psutil 1 Hz, heartbeat, `system.csv` | DONE | `SystemSampler` memakai sampler dan jam yang dapat disuntikkan; Master mencatat `role=master`, Worker mencatat `role=worker`, mode local mencatat `role=local` |
| P7-T2 | `metrics/calc.py`: rumus speedup, efficiency, throughput, imbalance, detection latency, Recovery Time | DONE | Rumus sama dengan EXPERIMENTS.md bagian 3; `recovery_stats` menurunkan detection dan Recovery Time dari `events.jsonl` |
| P7-T3 | `bench/runner.py`: matriks E1-E6, N ulangan, localhost dan LAN, `results/raw`, `results/summary.csv` | DONE | `--local` menjalankan Master dan Worker sebagai subprocess; `--lan` menjalankan Master saja dan menunggu Worker manual; E5 memakai `pcomp.tools.inject_failure` |
| P7-T4 | `bench/report.py`: tabel rata-rata/simpangan baku dan grafik PNG (Agg) | DONE | Tujuh grafik: waktu vs Worker, speedup, efficiency, throughput, CPU/memori, beban per Worker, timeline recovery; backend `Agg` diset sebelum `pyplot` |
| P7-T5 | Metadata lingkungan otomatis per run | DONE | `env.json`: hostname, platform, OS, versi Python, CPU, core fisik dan logis, RAM, tanggal |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/metrics/system.py` | add | Sampler psutil 1 Hz, `SystemLog` penulis `system.csv`, pembaca, dan agregasi per peran |
| `src/pcomp/metrics/calc.py` | add | Rumus enam metrik dan `recovery_stats` dari events |
| `src/pcomp/bench/runner.py` | add | Matriks E1-E6, eksekusi localhost/LAN, metadata lingkungan, `summary.csv` |
| `src/pcomp/bench/report.py` | add | Agregasi rata-rata/simpangan baku dan tujuh grafik PNG |
| `src/pcomp/master/server.py` | mod | `SystemLog`/`SystemSampler` peran master dan pencatatan HEARTBEAT Worker |
| `src/pcomp/worker/heartbeat.py` | mod | `sampler` opsional sehingga `cpu_percent` dan `mem_percent` berasal dari psutil |
| `src/pcomp/worker/client.py` | mod | Heartbeat memakai `ProcessSampler().usage` |
| `src/pcomp/constants.py` | mod | `SYSTEM_SAMPLE_INTERVAL`, `SYSTEM_CSV_NAME`, `BENCH_ENV_NAME`, versi `0.07.0` |
| `tests/unit/test_calc.py` | add | UT-CAL-01..04 |
| `tests/unit/test_system.py` | add | UT-SYS-01..03 |
| `tests/unit/test_bench.py` | add | UT-BEN-01..07 |
| `tests/unit/test_report.py` | add | UT-RPT-01..02 |
| `tests/integration/test_bench_cli.py` | add | IT-BENCH-01 |
| `scripts/gate.py` | mod | Smoke Fase 7 dengan penanda `BENCH OK` |
| `.gitignore` | mod | `results/dev/` tidak dilacak |
| `pyproject.toml` | mod | Versi `0.07.0` dan dependensi opsional `analysis` (matplotlib) |
| `requirements-dev.txt` | mod | Baris `matplotlib>=3.7` untuk grafik laporan |
| `DECISIONS.md` | mod | ADR-012 matplotlib sebagai dependensi analisis |
| `ARCHITECTURE.md` | mod | Bagian 9 memuat `system.csv`, `env.json`, dan pemisahan `results/dev` |
| `TESTING.md` | mod | Baris UT-SYS, UT-BEN, dan UT-RPT pada matriks test |
| `CHANGELOG.md` | mod | Entri `0.07.0` |
| `PLAN.md` | mod | Status Fase 7 DONE dan `CURRENT PHASE: 8` |
| `docs/phase-logs/PHASE-07.md` | add | Catatan fase ini |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 20 | 206 | UT-CAL-01..04, UT-SYS-01..03, UT-BEN-01..07, UT-RPT-01..02 |
| Integration | 1 | 19 | IT-BENCH-01: runner localhost `sim`, 1 dan 2 Worker, 2 ulangan |

Coverage: 83.20% pada run gate final (83.13% pada run gate sebelumnya; selisih kecil karena
beberapa cabang bergantung waktu).

## 6. Hasil Verification Gate
Dijalankan dengan `python scripts/gate.py` pada 2026-11-21.

| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=103 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 39 source files` |
| G3 Unit+cov | PASS | `Required test coverage of 80% reached. Total coverage: 83.20% \| 206 passed, 19 deselected` |
| G4 Integration | PASS | `19 passed, 206 deselected in 71.11s` |
| G5 Regresi | PASS | `seluruh test fase lama ikut dijalankan oleh G3 dan G4` |
| G6 Smoke | PASS | `python.exe -m pcomp.bench.runner --exp E6 --local --workers 1,2 --reps 2 --algo sim -> rc=0: BENCH OK` |
| G7 Flaky x3 | PASS | `3 kali lulus` |
| G8 Dokumen | PASS | `CHANGELOG, phase log, dan status PLAN sinkron` |
| G9 Repo | PASS | `103 file terlacak, tidak ada pelanggaran` |

Keluaran smoke apa adanya (dijalankan langsung dari root repo):

```
E6-w1-p1-dynamic-r1-20261121T023940619851: workers=1 procs=1 time_s=0.608727 tasks=5 verify=True
E6-w1-p1-dynamic-r2-20261121T023942667717: workers=1 procs=1 time_s=0.620117 tasks=5 verify=True
E6-w2-p1-dynamic-r1-20261121T023944665767: workers=2 procs=1 time_s=0.827623 tasks=5 verify=True
E6-w2-p1-dynamic-r2-20261121T023946904176: workers=2 procs=1 time_s=0.809709 tasks=5 verify=True
exp          : E6
mode         : local
runs         : 4
baseline_s   : 0.291796
summary      : results\dev\summary.csv
figures      : 6 berkas di results\dev\figures
BENCH OK
```

Angka di atas berasal dari algoritma `sim` pada dataset sintetis 8 MiB, sehingga hanya menjadi
bukti harness berjalan dan tidak dipakai untuk analisis performa.

## 7. Deviasi dari rencana
1. PLAN.md P7-T3 menyebut keluaran ke `results/raw/<exp>/<run_id>/` dan `results/summary.csv`.
   Instruksi fase ini mewajibkan hasil `sim` disimpan di `results/dev/`, sehingga harness memilih
   folder induk berdasarkan algoritma: `results/raw` dan `results/summary.csv` untuk algoritma
   nyata, `results/dev` untuk `sim`. `--out-root` menimpa keduanya. Metadata `algo` tetap dicatat
   pada `spec.json` dan `metrics.json` agar validator Fase 9 dapat menolak data simulasi.
2. matplotlib dicatat sebagai dependensi opsional `analysis`, bukan `dependencies` inti, karena
   PLAN.md P0-T2 membatasi dependensi runtime Worker pada psutil (ADR-012).
3. Harness memakai `python -m pcomp.master` dan `python -m pcomp.worker` sebagai subprocess dan
   memilih port kosong otomatis; tidak ada perubahan PROTOCOL.md karena tidak ada pesan baru.
4. Smoke Fase 7 pada PLAN.md hanya memberi perintah tanpa penanda keluaran; penanda `BENCH OK`
   ditetapkan pada `scripts/gate.py`, sama seperti pola fase sebelumnya.
5. UT-BEN-07 menjalankan `main` mode sequential dengan `sim` di dalam unit test agar jalur CLI
   harness tercakup tanpa jaringan dan tetap di bawah batas 60 detik per test.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| G3 gagal pertama: coverage 78.01% | `bench/runner.py` menambah 349 baris dan unit test baru hanya menyentuh fungsi murni | Menambah UT-BEN-05..07 (penyusunan argumen, helper metrics/events/dataset, dan jalur `main` sequential) sehingga coverage 83.13% |
| `TypeError: build_row() got an unexpected keyword argument 'imbalance'` | Nilai imbalance hanya dibaca dari `metrics.json`, padahal E2 lokal menghitungnya di pemanggil | Menambah parameter `imbalance` pada `build_row` dengan fallback ke `metrics` dan `busy_per_process` |
| G1 gagal karena E501 pada beberapa baris | Baris `argparse` dan ekspresi panjang | Memecah baris dan menjalankan `ruff format` |
| mypy menolak `float(event["ts"])` | `Event` didefinisikan `Mapping[str, object]` | Tipe diubah menjadi `Mapping[str, Any]` |

## 9. Back-fix (bug fase lama)
Tidak ada. Perubahan `worker/heartbeat.py` dan `worker/client.py` hanya mengaktifkan field
`cpu_percent`/`mem_percent` yang sudah ada pada PROTOCOL.md; perilaku lama (nilai 0.0) tetap
tersedia bila `sampler` tidak diberikan.

## 10. Keterbatasan dan utang teknis
1. Jalur E3 (9 Worker), E4 dengan throttle di banyak node, dan mode `--lan` baru diuji secara
   logika dan pada localhost; pengujian pada node fisik dijadwalkan Fase 8.
2. `bench/runner.py` belum diuji untuk skenario Master gagal di tengah run atau Worker yang mati
   lebih dari satu pada satu waktu (di luar `--kill-workers`).
3. Tanpa ekstra `analysis`, `python -m pcomp.bench.runner` gagal saat mengimpor
   `pcomp.bench.report`. Perilaku ini dicatat pada ADR-012.
4. Smoke gate menambahkan baris ke `results/dev/summary.csv` setiap kali dijalankan; folder
   tersebut gitignored sehingga tidak mencemari data resmi, tetapi isinya perlu dibersihkan
   manual sebelum analisis Fase 9.
5. Grafik `recovery_timeline.png` hanya terbentuk pada run yang memiliki event
   `worker_exit_injected`, sehingga smoke E6 menghasilkan enam dari tujuh grafik.
6. Simpangan baku memakai `statistics.stdev` (sampel); untuk satu ulangan nilainya 0.0.

## 11. Catatan serah-terima ke fase berikutnya
1. Fase 8 tinggal menjalankan harness yang sama pada node fisik (`--lan`) dan mencatat hasil di
   `results/raw/`; skrip deployment node belum ada dan menjadi bagian fase itu.
2. Semua hasil baru wajib memakai algoritma nyata (`lzma`/`bz2`/`gzip`); data `sim` di
   `results/dev/` tidak boleh disalin ke `results/raw/` atau dipakai pada laporan.
3. Validator Fase 9 dapat menolak run dengan `algo=sim` dari `spec.json`, `metrics.json`, atau
   kolom `algo` pada `summary.csv`.
4. `scripts/gate.py` sudah memuat smoke Fase 7 (`BENCH OK`); smoke Fase 8 perlu ditambahkan saat
   fase itu dimulai.

## 12. Commit
Commit fase: `feat(phase-07): add metrics collection, calculations, benchmark harness`.
Hash dan tag: lihat `git log --oneline` serta tag `phase-07-done`.
