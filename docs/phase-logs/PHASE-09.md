# PHASE-09 — Eksperimen resmi pada 10 node virtual

- Branch: phase/09-official-results
- Mulai / selesai: 2026-11-22 / 2026-11-22
- Status: IN PROGRESS

## 1. Tujuan
Menjalankan eksperimen resmi E1 sampai E6 pada 10 node virtual (ADR-015), masing-masing tiga
ulangan dengan jeda 30 detik, memakai algoritma nyata, lalu menyimpan seluruh hasil ke
`results/raw/<exp>/<run_id>/` beserta ringkasan `results/summary.csv` dan grafik final.

## 2. Ringkasan hasil
Seluruh 45 run (E1 3, E2 12, E3 3, E4 6, E5 6, E6 15) selesai dengan `VERIFY OK`, dan
`python -m pcomp.tools.validate_results results/raw` mencetak `RESULTS VALID`. Sequential
menghabiskan 143,56 ± 6,79 detik untuk 2048 MiB (14,29 MB/s), local parallel p = 8 memberi speedup
3,71, sedangkan distributed 9 Worker memberi speedup 2,30 terhadap sequential dan 3,49 terhadap
satu Worker. Scheduler dynamic 14,4 % lebih cepat daripada static pada E4 (57,16 berbanding 66,78
detik) dengan imbalance 1,038 berbanding 1,222. Kegagalan Worker terdeteksi di bawah 0,5 detik dan
seluruh run E5 tetap `VERIFY OK`; skenario 3 Worker mati menambah makespan menjadi 108,21 detik.
Penambahan Worker dari 6 ke 9 tidak menambah throughput karena VM Colima hanya 6 vCPU.
Analisis lengkap beserta angka per eksperimen ada di `docs/ANALYSIS.md`.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P9-T0 | Perbaikan harness: jeda antar run dan orkestrasi container per run | DONE | `bench/runner.py` mendapat `--pause`; `scripts/run_experiments.py` menyalakan/mematikan container, membunuh Worker E5, dan menyimpan bukti |
| P9-T1 | `tools/validate_results.py` dan unit test | DONE | Validasi metadata, `VERIFY OK`, larangan `sim`, jumlah ulangan, dan skema `summary.csv` |
| P9-T2 | `results/summary.csv` dan grafik final | DONE | 45 run, `summary_agg.csv` 13 kelompok konfigurasi, 7 grafik di `results/figures/` |
| P9-T3 | `docs/ANALYSIS.md` | DONE | Analisis tiap eksperimen dari `summary.csv` dan `summary_agg.csv`, menyebut file sumber |

### 3.1 Parameter yang dikunci
Nilai berikut dipakai untuk **semua** eksperimen sehingga perbandingan sahih
(EXPERIMENTS.md bagian 1).

| Parameter | Nilai | Alasan |
|---|---|---|
| Dataset | sintetis `data/bench`, 2048 MiB, 8 berkas, seed 20261122 | Silesia tidak tersedia luring; komposisi pola teks/acak/berulang/campuran sama seperti `make_dataset` |
| Algoritma / level | `lzma`, preset 6 | Rekomendasi EXPERIMENTS.md bagian 1 |
| Chunk size | 4 MiB | Rekomendasi EXPERIMENTS.md bagian 1 |
| `--repeat` | 1 | Dataset sudah cukup besar; menghindari catatan kejujuran duplikasi data |
| Jumlah ulangan | 3 per konfigurasi | EXPERIMENTS.md bagian 1 |
| Jeda antar run | 30 detik | EXPERIMENTS.md bagian 1 |
| Mode E1 | sequential, 1 proses | EXPERIMENTS.md bagian 2 |
| Mode E2 | local parallel, `procs = 1, 2, 4, 8` | 8 core logis pada host Master |
| Mode E3/E4/E5/E6 | 1 Master (host) + 9 Worker container, `procs = 1` | ADR-015 |
| E4 lambat | `--throttle 0,25` detik per task pada Worker terakhir | Membuat ketimpangan beban terukur |
| E5 mati | 1 Worker dan 3 Worker dimatikan pada sekitar 50% task selesai | EXPERIMENTS.md bagian 2 butir e |

Kalibrasi T sequential (EXPERIMENTS.md mensyaratkan 2 sampai 10 menit) diukur dengan pipeline
nyata pada dataset 256 MiB. Pada mesin yang sudah dikosongkan hasilnya 21,4 detik (11,94 MB/s),
sehingga dataset dinaikkan ke 2048 MiB agar T sequential sekitar 170 detik, bukan 86 detik
(terlalu pendek) seperti jika dataset tetap 1024 MiB. Nilai terukur untuk dataset final dicatat
pada bagian 2 dan pada `results/summary.csv` baris E1.

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `scripts/run_experiments.py` | add | Orkestrasi container per run, kill E5, bukti log, pembersihan payload |
| `tests/unit/test_run_experiments.py` | add | UT-EXP-01..07 |
| `src/pcomp/tools/validate_results.py` | add | P9-T1 |
| `tests/unit/test_validate_results.py` | add | UT-VAL-01..07 |
| `src/pcomp/bench/runner.py` | mod | Opsi `--pause`, `pause_between_runs`, urutan run (ulangan di luar), pembacaan ulang `summary.csv` untuk grafik, kolom `kill_workers` |
| `tests/unit/test_bench.py` | mod | UT-BEN-09, UT-BEN-10, UT-BEN-11 |
| `src/pcomp/metrics/calc.py` | mod | `retried_tasks` dan Recovery Time menghitung seluruh Worker yang diinjeksi |
| `tests/unit/test_calc.py` | mod | UT-CAL-07 |
| `src/pcomp/bench/report.py` | mod | `kill_workers` masuk kunci agregat; `plot_worker_load` memilih run terdistribusi berbeda konfigurasi |
| `EXPERIMENTS.md` | mod | Skema `summary.csv` memuat `kill_workers` |
| `scripts/gate.py` | mod | Smoke fase 9 = `validate_results` mencetak `RESULTS VALID` |
| `PLAN.md` | mod | Status fase 9 `IN PROGRESS` |
| `docs/ANALYSIS.md` | add | P9-T3 |
| `results/raw/`, `results/summary.csv`, `results/figures/` | add | Data eksperimen resmi |
| `docs/phase-logs/PHASE-09.md` | add | Catatan fase ini |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 18 | 236 | UT-EXP-01..07, UT-VAL-01..07, UT-BEN-09..11, UT-CAL-07 |
| Integration | 0 | 19 | Perilaku jaringan sudah dicakup test fase sebelumnya; jumlahnya tidak berubah |

Coverage: 84,6 % (ambang 80 %).

## 6. Hasil Verification Gate
Gate penuh dijalankan 2026-11-22 pukul 17:46, hasil `PASS (seluruh gate wajib lulus)`.

| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!`; `format=118 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 40 source files` |
| G3 Unit+cov | PASS | `236 passed, 20 deselected`, coverage `84.56 %` |
| G4 Integration | PASS | `19 passed, 237 deselected` |
| G5 Regresi | PASS | seluruh test fase lama dijalankan pada G3 dan G4 |
| G6 Smoke | PASS | `validate_results results/raw` -> `RESULTS VALID` |
| G7 Flaky x3 | PASS | 3 kali lulus |
| G8 Dokumen | PASS | CHANGELOG, phase log, dan status PLAN sinkron |
| G9 Repo | PASS | 749 file terlacak, tidak ada pelanggaran |

## 7. Deviasi dari rencana
1. Langkah eksperimen pada `PROMPTS.md` ditandai khusus user. Bagian ini dijalankan agent atas
   instruksi eksplisit user pada 2026-11-22; keputusan dan alasan dicatat di sini agar tidak
   dianggap agent melanggar batas peran.
2. Dataset resmi memakai korpus sintetis, bukan Silesia, karena Silesia tidak tersedia luring dan
   ruang disk terbatas. Komposisi dan seed dicatat sehingga dapat direproduksi.
3. Payload chunk (`chunks/`) dihapus setelah `VERIFY OK` untuk menghemat disk; `manifest.json`
   menyimpan hash setiap chunk dan `verify.log` menyimpan bukti verifikasi. Hal ini juga dicatat
   sebagai keterbatasan pada bagian 10.
4. Node bersifat virtual (1 Master di host + 9 Worker container) sesuai ADR-015, bukan 10
   perangkat fisik.
5. Pengukuran berjalan pada laptop yang juga memakai aplikasi lain, sehingga throughput lebih
   rendah daripada potensi perangkat. Semua run berada pada kondisi yang sama.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| Harness tidak punya jeda antar run | `bench/runner.py` hanya mengulang run berurutan | Tambah `--pause` dan `pause_between_runs` (UT-BEN-09) |
| Baris port Master tidak terbaca orkestrator | stdout runner ter-buffer saat diarahkan ke berkas | Runner dijalankan dengan `-u` dan `PYTHONUNBUFFERED=1` |
| Port Master dipakai ulang antar run | Satu port dipilih per eksperimen | Port dibaca dari `master.log` setiap run; runner memilih port bebas sendiri |
| Run lama diproses ulang pada invocation E5 kedua | Pencarian folder run tidak melewati run yang sudah selesai | `metrics.json` dipakai sebagai penanda run selesai |
| Kalibrasi T meleset (perkiraan 16 menit) | Proses sisa dan `mediaanalysisd` memakai CPU; dataset 1536 MiB terlalu besar | Proses sisa dimatikan, pengukuran diulang setelah mesin tenang |
| Baseline E1 tidak konsisten (199,5 s lalu 94,4 s dan 100,3 s) | Chrome, Discord, dan `mediaanalysisd` memakai CPU bergantian sehingga throughput berubah dua kali | User menutup aplikasi berat; kalibrasi ulang 21,4 detik untuk 256 MiB lalu seluruh eksperimen diulang dari nol dengan dataset 2048 MiB |
| `caffeinate` menolak perintah (exit 127) | `PYTHONPATH=src` dianggap nama perintah oleh `caffeinate` | Dipanggil sebagai `caffeinate -im env PYTHONPATH=src ...` |
| Run E1 pertama gagal saat finalisasi | Mode sequential tidak menulis `events.jsonl`, tetapi orkestrator mewajibkannya | `check_artifacts` dan `validate_results` memakai daftar berkas sadar-mode (`UT-EXP-07`, `UT-VAL-07`) |
| Speedup E2 dan E4 berpotensi bias | Seluruh ulangan satu konfigurasi berjalan berurutan sehingga pergeseran beban mesin masuk ke satu konfigurasi saja | Urutan run diubah: ulangan di luar, konfigurasi di dalam (`UT-BEN-10`) |
| `retried_tasks` E5 skenario tiga Worker terlalu kecil | `recovery_stats` hanya menghitung requeue milik satu Worker | `killed_workers` dan cakupan `recovery_time` mencakup semua Worker yang diinjeksi (`UT-CAL-07`) |

## 9. Back-fix (bug fase lama)
1. `metrics/calc.py` (`recovery_stats`, `recovery_time`): jumlah `retried_tasks` dan Recovery
   Time pada skenario yang menghentikan beberapa Worker sebelumnya hanya menghitung Worker
   pertama. Sekarang seluruh Worker yang diinjeksi ikut dihitung agar metrik E5 benar. Perilaku
   untuk satu Worker tidak berubah (UT-CAL-03, UT-CAL-04 tetap lulus).

## 10. Keterbatasan dan utang teknis
1. Payload chunk dihapus setelah verifikasi; verifikasi ulang membutuhkan menjalankan eksperimen
   kembali. `verify.log`, `manifest.json`, dan `summary.csv` tetap tersimpan sebagai bukti.
2. Sembilan Worker berbagi 6 vCPU dan 4 GiB RAM pada satu VM Colima, sehingga CPU per Worker
   lebih lambat daripada proses native. Speedup E3/E6 karena itu di bawah jumlah Worker.
3. Seluruh node berada pada satu host dan jaringan Docker bridge; angka tidak mewakili LAN lab.
4. Beban latar laptop tidak dikendalikan penuh (beberapa proses sistem macOS tetap berjalan).
5. Kolom `cpu_avg_workers` pada `results/summary.csv` tidak dapat dipakai. Sampler membaca
   `cpu_percent` proses utama Worker, sedangkan kompresi berjalan pada proses anak
   `multiprocessing.Pool`, sehingga nilainya hampir selalu 0 % dengan lonjakan tidak wajar.
   Analisis beban memakai `busy_sec` per Worker (`worker_stats`). Perbaikan sampler dicatat
   sebagai utang teknis untuk fase 10.
6. `retried_tasks` pada E5 dihitung dari seluruh Worker yang diinjeksi (perbaikan
   `metrics/calc.py` pada fase ini), sehingga skenario tiga Worker menghitung task dari ketiga
   Worker. Jumlah kejadian `task_requeued` pada `events.jsonl` tetap menjadi rujukan silang.
7. Sebaran waktu E6 besar (simpangan baku sampai 30 detik) karena beban mesin menurun selama sesi
   pengukuran. Ulangan dijalankan dengan konfigurasi di dalam satu ulangan, sehingga perbandingan
   antar jumlah Worker tetap sahih, tetapi angka absolut perlu dibaca bersama simpangan bakunya.

## 11. Catatan serah-terima ke fase berikutnya
1. Data resmi ada di `results/raw/`, ringkasan di `results/summary.csv`, grafik di
   `results/figures/`. Semua angka laporan harus diambil dari berkas ini.
2. `python -m pcomp.tools.validate_results results/raw` harus mencetak `RESULTS VALID`; ini juga
   smoke test gate fase 9.
3. Fase 10 memakai `results/figures/*.png` untuk laporan. Tangkapan layar 10 node diambil manual
   oleh user; perintahnya ada di `docs/evidence/README.md`.
4. Jangan menambah run ke `results/raw/` tanpa mengulang tiga ulangan dan memperbarui
   `results/summary.csv` lewat harness. Bila eksperimen baru ditambahkan, jalankan harness sekali
   lagi agar grafik dan `summary_agg.csv` dibuat ulang dari SELURUH baris `summary.csv`.
5. `summary.csv` memuat kolom `kill_workers`; nilai `0` berarti tanpa injeksi kegagalan. Agregat
   `summary_agg.csv` memakai kolom ini sebagai kunci pengelompokan.
6. Utang teknis fase 10: perbaiki `metrics/system.ProcessSampler` agar menjumlahkan CPU proses
   anak (`multiprocessing.Pool`) sehingga `cpu_avg_workers` terisi benar.

## 12. Commit
Commit bagian agent: `docs(phase-09): add official experiment results and analysis`
(hash `81343f3`), berisi 639 berkas termasuk 45 folder run pada `results/raw/`.
Commit lanjutan `docs(phase-09): record commit hash` mencatat hash ini.
Keduanya digabung ke `main` dengan `git merge --no-ff`, lalu diberi tag `phase-09-done`.
Tag tidak dipush: `git push` hanya dilakukan bila user meminta.
