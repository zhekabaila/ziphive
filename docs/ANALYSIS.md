# ANALYSIS.md — Analisis Hasil Eksperimen E1 sampai E6

Seluruh angka pada dokumen ini diambil dari `results/summary_agg.csv` (rata-rata dan simpangan
baku tiga ulangan) dan `results/summary.csv` (nilai per run). Kolom `run_id` menunjuk folder
`results/raw/<exp>/<run_id>/` yang memuat `metrics.json`, `events.jsonl`, `manifest.json`, dan
`verify.log`. Nilai `verify_ok` pada seluruh 45 run adalah `True`, dan
`python -m pcomp.tools.validate_results results/raw` mencetak `RESULTS VALID`.

Lingkungan pengukuran (dari `results/raw/E3/<run_id>/env.json`): macOS 26.6.2, Apple arm, 8 core
logis, RAM 8 GiB, Python 3.14.4. Satu Master berjalan di host dan sembilan Worker berjalan sebagai
container pada satu VM Colima dengan 6 vCPU (ADR-015). Uji TCP container ke host mencapai
353 MB/s, sehingga jaringan bukan penghambat; yang membatasi adalah CPU VM dan pemrosesan di
Master.

## 0. Parameter bersama

| Parameter | Nilai |
|---|---|
| Dataset | sintetis `data/bench`, 2048 MiB, 8 berkas (`text`, `random`, `repeat`, `mixed`), seed 20261122 |
| Algoritma / level | `lzma`, preset 6 |
| Chunk | 4 MiB |
| `--repeat` | 1 |
| Jumlah task | 513 per run |
| Ulangan | 3 per konfigurasi, jeda 30 detik, urutan ulangan di luar konfigurasi |
| Worker terdistribusi | 9 (1 Master + 9 Worker), `procs = 1` per Worker |
| Heartbeat | interval 2,0 detik, timeout 6,0 detik, `max_attempts` 3 |

Rasio kompresi 2,632 pada semua run, sehingga hasil kompresi sekitar 0,38 kali ukuran asli.
Angka yang ditulis sebagai `a ± b` adalah rata-rata ± simpangan baku dari tiga ulangan.

## 1. E1 — Sequential (T baseline)

Sumber: baris `exp=E1` pada `results/summary.csv`.

| Metrik | Nilai |
|---|---|
| Waktu T | 143,56 ± 6,79 detik |
| Throughput | 14,29 ± 0,66 MB/s |
| Jumlah task | 513 |
| Rasio kompresi | 2,632 |
| CPU Master | 99,69 ± 0,06 % (satu core penuh) |

Tiga ulangan E1 menghasilkan 138,26 detik, 141,20 detik, dan 151,21 detik. Sebaran 6,79 detik
(4,7 % dari rata-rata) menjadi acuan: selisih antar konfigurasi yang lebih kecil dari nilai ini
tidak ditafsirkan sebagai perbedaan nyata.

CPU Master yang mencapai 99,69 % menunjukkan E1 memang terikat satu core, sesuai sifat sequential.
Nilai ini menjadi pembanding utama speedup seluruh eksperimen lain.

## 2. E2 — Local parallel (p = 1, 2, 4, 8)

Sumber: baris `exp=E2` pada `results/summary_agg.csv`, dikelompokkan menurut `procs`.

| p | T (detik) | Speedup S(p) | Efficiency E(p) | Throughput (MB/s) |
|---|---|---|---|---|
| 1 | 152,46 ± 3,80 | 1,010 ± 0,025 | 1,010 ± 0,025 | 13,44 ± 0,34 |
| 2 | 88,42 ± 2,09 | 1,742 ± 0,041 | 0,871 ± 0,021 | 23,17 ± 0,55 |
| 4 | 51,48 ± 2,39 | 2,995 ± 0,138 | 0,749 ± 0,034 | 39,84 ± 1,83 |
| 8 | 42,31 ± 6,71 | 3,708 ± 0,646 | 0,463 ± 0,081 | 49,31 ± 8,59 |

Penambahan proses masih menurunkan waktu sampai p = 8, tetapi efisiensinya turun dari 0,871 pada
p = 2 menjadi 0,463 pada p = 8. Penyebab utamanya bukan komunikasi (semua proses ada di satu
mesin) melainkan sumber daya bersama: delapan proses `lzma` preset 6 memakai memori besar dan
bersaing pada bandwidth memori serta cache, sementara harness juga mencatat `system.csv` pada
satu core.

Sebaran p = 8 paling besar (simpangan baku 6,71 detik, 16 % dari rata-rata) karena tiga ulangannya
42,31 detik, 46,69 detik, dan 34,59 detik. Run 34,59 detik terjadi saat mesin paling lengang.
Karena itu p = 8 ditafsirkan sebagai batas praktis, bukan angka yang presisi.

Nilai p = 1 (152,46 detik) sedikit di atas E1 (143,56 detik) karena harness menyiapkan dataset,
mencatat `system.csv` 1 Hz, dan memakai Worker proses terpisah. Selisih 6 % ini adalah overhead
kerangka pengukuran, bukan overhead algoritma.

## 3. E3 — Distributed 1 Master + 9 Worker

Sumber: baris `exp=E3` pada `results/summary.csv` dan `results/summary_agg.csv`.

| Metrik | Nilai |
|---|---|
| Waktu T | 62,31 ± 5,84 detik |
| Speedup terhadap sequential (E1) | 2,301 ± 0,205 |
| Speedup terhadap 1 Worker container (E6 w = 1, 247,15 detik) | 3,97 |
| Efficiency terhadap 9 Worker | 0,256 ± 0,023 |
| Imbalance factor | 1,026 ± 0,020 |
| CPU Master | 8,10 ± 0,26 % |
| Throughput | 33,05 ± 2,94 MB/s |

Tiga ulangan E3 menghasilkan 58,53 detik, 69,03 detik, dan 59,37 detik. Nilai 69,03 detik adalah
outlier karena beban mesin naik sesaat; imbalance factor run tersebut juga naik ke 1,048.

Dibanding E1, E3 sekitar 2,3 kali lebih cepat. Dibanding satu Worker container, E3 sekitar 3,97
kali lebih cepat. Dua angka ini berbeda karena satu Worker container lebih lambat daripada
sequential (lihat bagian 6), sehingga memakai E1 sebagai pembanding membuat distributed terlihat
kurang menguntungkan.

Imbalance factor mendekati 1 (1,026), artinya scheduler dynamic membagi task hampir merata:
selisih waktu sibuk antar Worker hanya sekitar 2,6 %. Rincian beban per Worker ada pada
`results/figures/worker_load.png`.

CPU Master hanya 8,10 %, sehingga Master tidak terikat CPU. Yang membatasi adalah penulisan hasil
dan hashing di Master yang berjalan berurutan untuk setiap chunk masuk, ditambah sembilan Worker
yang berbagi 6 vCPU.

## 4. E4 — Dynamic load balancing (static vs dynamic)

Sumber: baris `exp=E4` pada `results/summary_agg.csv`; beban per Worker dari `worker_stats` pada
`results/raw/E4/<run_id>/metrics.json`. Worker ke-9 diberi `--throttle 0,25` detik per task
sehingga menjadi Worker lambat.

| Scheduler | Makespan (detik) | Imbalance factor | Throughput (MB/s) |
|---|---|---|---|
| static | 66,78 ± 1,30 | 1,222 ± 0,014 | 30,67 ± 0,60 |
| dynamic | 57,16 ± 0,88 | 1,038 ± 0,007 | 35,83 ± 0,55 |

Beban per Worker (rata-rata tiga ulangan, detik sibuk):

| Worker | static | dynamic |
|---|---|---|
| w1 | 48,2 | 48,3 |
| w2 | 49,2 | 48,3 |
| w3 | 48,5 | 48,7 |
| w4 | 47,9 | 48,4 |
| w5 | 47,8 | 48,6 |
| w6 | 46,7 | 48,9 |
| w7 | 48,4 | 48,9 |
| w8 | 49,7 | 48,6 |
| w9 (diperlambat) | 60,7 | 50,7 |

Pada scheduler static setiap Worker menerima tepat 57 task tanpa melihat kecepatan, sehingga
Worker lambat (w9) menjadi penentu akhir: 60,7 detik sibuk dibanding 46,7 sampai 49,7 detik pada
Worker lain. Pada scheduler dynamic Worker lambat otomatis menerima lebih sedikit task
(rata-rata 40,3 task berbanding sekitar 57 sampai 62 task pada Worker lain), sehingga w9 hanya
sibuk 50,7 detik.

Makespan dynamic 14,4 % lebih pendek daripada static (57,16 berbanding 66,78 detik) dan imbalance
factor turun dari 1,222 ke 1,038. Simpangan baku kedua konfigurasi kecil (1,30 dan 0,88 detik),
jauh di bawah selisih 9,62 detik, sehingga perbedaan ini nyata dan bukan kebetulan pengukuran.

## 5. E5 — Fault tolerance (1 dan 3 Worker dimatikan pada 50 % progres)

Sumber: baris `exp=E5` pada `results/summary_agg.csv` (kolom `kill_workers` membedakan kedua
skenario) dan `results/raw/E5/<run_id>/events.jsonl`.

| Skenario | Makespan (detik) | Detection latency (detik) | Recovery time (detik) | Task diulang |
|---|---|---|---|---|
| 1 Worker mati | 66,27 ± 8,27 | 0,26 ± 0,09 | 1,37 ± 0,70 | 1,00 ± 0,00 |
| 3 Worker mati | 108,21 ± 3,82 | 0,38 ± 0,11 | 5,60 ± 5,84 | 2,67 ± 0,58 |

Setiap run E5 berakhir dengan `VERIFY OK`, artinya hasil dekompresi tetap identik dengan aslinya
meskipun Worker dimatikan di tengah run. Event `worker_exit_injected`, `worker_dead`, dan
`task_requeued` pada `events.jsonl` menjadi bukti urutan kejadiannya.

Detection latency di bawah 0,5 detik karena Master memeriksa heartbeat setiap 0,2 detik dan
Worker yang mati langsung terlihat dari koneksi yang tertutup, tanpa menunggu batas timeout
6 detik. Recovery time adalah waktu sampai task yang diulang selesai dikerjakan Worker lain.

Skenario satu Worker mati hampir tidak menambah waktu dibanding E3 (66,27 berbanding 62,31
detik), karena delapan Worker tersisa menyerap task yang dilepas. Skenario tiga Worker mati
menambah waktu menjadi 108,21 detik karena kapasitas turun dari 9 menjadi 6 Worker, tepat pada
batas 6 vCPU yang tersedia.

Recovery time skenario tiga Worker memiliki simpangan baku besar (5,60 ± 5,84 detik) karena satu
ulangan memerlukan 12,34 detik: task yang diulang kebetulan adalah chunk data acak yang paling
lama dikompresi (sekitar 2,3 detik per chunk) dan harus diulang dari awal.

## 6. E6 — Skalabilitas jumlah Worker (1, 2, 4, 6, 9)

Sumber: baris `exp=E6` pada `results/summary_agg.csv`, dikelompokkan menurut `workers`.

| Worker | T (detik) | Speedup terhadap 1 Worker | Efficiency | Throughput (MB/s) |
|---|---|---|---|---|
| 1 | 247,15 ± 27,82 | 1,000 | 0,805 | 8,36 ± 0,99 |
| 2 | 140,50 ± 30,26 | 1,978 ± 0,392 | 0,722 ± 0,143 | 15,00 ± 2,97 |
| 4 | 98,67 ± 22,00 | 2,835 ± 0,663 | 0,517 ± 0,121 | 21,50 ± 5,03 |
| 6 | 79,28 ± 12,81 | 3,473 ± 0,619 | 0,423 ± 0,075 | 26,34 ± 4,69 |
| 9 | 79,32 ± 14,09 | 3,487 ± 0,690 | 0,283 ± 0,056 | 26,44 ± 5,23 |

Dua hal menonjol. Pertama, satu Worker container (247,15 detik) lebih lambat daripada sequential
(143,56 detik), sehingga speedup terhadap E1 untuk w = 1 hanya 0,805. Kedua, waktu w = 6 dan
w = 9 praktis sama (79,28 dan 79,32 detik): penambahan Worker dari 6 ke 9 tidak menambah
throughput karena VM Colima hanya diberi 6 vCPU.

Karena itu kurva speedup mendatar setelah 6 Worker. Efisiensi turun dari 0,722 pada w = 2 menjadi
0,283 pada w = 9, sesuai pembagian 6 vCPU untuk 9 proses kompresi.

Sebaran waktu pada E6 paling besar (simpangan baku sampai 30 detik pada w = 2). Penyebabnya
terlihat dari urutan run: ulangan pertama selalu paling lambat (w = 1: 270,07 detik) dan ulangan
ketiga paling cepat (216,19 detik), karena mesin masih menyelesaikan pekerjaan latar pada awal
pengukuran. Karena setiap ulangan memuat kelima konfigurasi secara berurutan, perbandingan antar
jumlah Worker di dalam satu ulangan tetap sahih, sedangkan angka absolutnya perlu dibaca dengan
simpangan baku tersebut.

## 7. Penyebab speedup di bawah jumlah proses atau Worker

1. **Worker container lebih lambat daripada proses native.** Kompresi dijalankan pada
   `multiprocessing.Pool` di dalam container, sehingga ada salinan data melalui lapisan Docker
   dan VM. Satu Worker container memerlukan 247,15 detik untuk 513 task, sedangkan sequential
   pada mesin yang sama hanya 143,56 detik (1,72 kali lebih lambat per task).
2. **Jumlah vCPU VM lebih kecil daripada jumlah Worker.** VM Colima diberi 6 vCPU untuk 9 Worker.
   Buktinya, w = 6 dan w = 9 menghasilkan waktu yang sama (79,28 dan 79,32 detik).
3. **Pemrosesan di Master bersifat berurutan.** Master menerima, memverifikasi hash, dan menulis
   setiap chunk satu per satu. Throughput tertinggi yang tercatat sekitar 36 MB/s pada E4
   dynamic, sementara jaringan container ke host sanggup 353 MB/s, sehingga batasnya ada pada
   pemrosesan dan penulisan hasil, bukan pada jaringan.
4. **Overhead kerangka pengukuran.** Harness mencatat `system.csv` 1 Hz dan menghitung hash pada
   setiap task. Perbandingan E1 (143,56 detik) dengan E2 p = 1 (152,46 detik) menunjukkan
   tambahan sekitar 6 %.
5. **Batas sumber daya bersama pada local parallel.** Efisiensi E2 turun ke 0,463 pada p = 8
   karena delapan proses `lzma` bersaing pada bandwidth memori dan cache, bukan karena
   komunikasi jaringan.

## 8. Keterbatasan pengukuran

1. Seluruh node berada pada satu mesin (ADR-015), sehingga angka tidak mewakili LAN lab dengan
   perangkat terpisah. Yang diukur adalah overhead virtualisasi dan pembagian CPU, bukan latensi
   jaringan fisik.
2. Kolom `cpu_avg_workers` pada `results/summary.csv` tidak dapat dipakai. Sampler membaca
   `cpu_percent` proses utama Worker, sedangkan kompresi berjalan pada proses anak di
   `multiprocessing.Pool`; akibatnya nilai terbaca hampir selalu 0 % dengan lonjakan tidak wajar.
   Analisis beban karena itu memakai `busy_sec` per Worker pada `metrics.json`
   (`results/figures/worker_load.png`). Kolom `cpu_avg_master` tetap sahih karena Master
   mengerjakan sendiri seluruh pemrosesan chunk.
3. Beban latar macOS tidak dapat dikendalikan penuh. Aplikasi berat sudah ditutup sebelum
   pengukuran, tetapi layanan sistem seperti `mediaanalysisd` sempat aktif pada awal sesi dan
   menurunkan throughput. Dampaknya terlihat pada urutan ulangan E6 (bagian 6).
4. Payload chunk dihapus setelah `VERIFY OK` untuk menghemat disk, sehingga verifikasi ulang
   membutuhkan menjalankan eksperimen kembali. Bukti verifikasi tetap tersimpan pada
   `verify.log` dan `manifest.json`.
5. Dataset bersifat sintetis karena Silesia tidak tersedia luring. Komposisi dan seed dicatat
   sehingga hasil dapat direproduksi, tetapi rasio kompresi dan waktu per chunk tidak identik
   dengan korpus Silesia.
