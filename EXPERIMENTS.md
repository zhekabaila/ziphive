# EXPERIMENTS.md — Rancangan Eksperimen dan Metrik

## 1. Kondisi tetap (semua eksperimen)
Dataset, algoritma, level, chunk size, dan `--repeat` sama untuk semua eksperimen yang dibandingkan. Direkomendasikan: Silesia, `lzma` preset 6, chunk 4 MiB, `--repeat` dipilih agar T sequential 2 sampai 10 menit. Nilai final dikunci di `PHASE-09.md`. Tiap konfigurasi diulang 3 kali, laporkan rata-rata dan simpangan baku. Jeda 30 detik antar run. Tidak ada aplikasi berat lain di node. Catat metadata lingkungan (CPU, core, RAM, OS, Python, jaringan).

## 2. Daftar eksperimen (memetakan butir 3a sampai 3f soal)
| ID | Soal | Konfigurasi | Yang dibandingkan |
|---|---|---|---|
| E1 | a. Sequential | 1 proses, 1 mesin | T baseline |
| E2 | b. Local parallel | p = 1, 2, 4, ..., jumlah core (1 mesin) | T, speedup, efficiency terhadap p |
| E3 | c. Distributed | 1 Master + 9 Worker, scheduler dynamic | T, throughput, CPU/memori, vs E1 dan E2 |
| E4 | d. Dynamic LB | 9 Worker, satu atau dua Worker dilambatkan (`--throttle` atau `--procs` lebih kecil); static vs dynamic | makespan, waktu sibuk per Worker, imbalance factor |
| E5 | e. Fault tolerance | 9 Worker; (i) matikan 1 Worker di sekitar 50% progres; (ii) matikan 3 Worker | waktu total, detection latency, Recovery Time, jumlah task diulang, `VERIFY OK` |
| E6 | f. Scalability | 1, 2, 4, 6, 9 Worker | T, speedup, efficiency, throughput |
| E7 (opsional) | tambahan | chunk size 1, 4, 16 MiB | T, rasio kompresi, overhead jaringan |

## 3. Rumus metrik
- Execution Time T: detik, dari task pertama dikirim sampai hasil terakhir tertulis (distributed) atau seluruh proses selesai (sequential dan local).
- Speedup terhadap sequential: S_seq(n) = T_seq / T_n.
- Speedup relatif 1 Worker: S_rel(n) = T_1worker / T_n.
- Efficiency: E(n) = S(n) / n, n = jumlah Worker (distributed) atau jumlah proses p (local). Untuk distributed, laporkan juga E terhadap total core Worker.
- Throughput: total ukuran data asli (MB) / T, satuan MB/s. Tambahan: rasio kompresi = ukuran asli / ukuran hasil.
- CPU/Memory Utilization: psutil 1 Hz. Laporkan rata-rata dan puncak per node.
- Imbalance factor: max(busy_i) / mean(busy_i), busy_i = jumlah `compute_sec` Worker i. Nilai 1 berarti seimbang.
- Detection latency: t_dead_detected - t_kill. Recovery Time: t_all_requeued_done - t_kill, dengan t_all_requeued_done = waktu task terakhir yang tadinya milik Worker mati selesai DONE. t_kill dicatat oleh `inject_failure.py` atau event `worker_exit_injected`.

## 4. Skema CSV (`results/summary.csv`)
`exp, run_id, rep, mode, workers, procs, scheduler, algo, level, chunk_mb, repeat, total_mb, tasks, time_s, throughput_mbs, ratio, speedup_seq, speedup_rel, efficiency, imbalance, cpu_avg_master, cpu_avg_workers, mem_avg_master, mem_avg_workers, detect_s, recovery_s, retried_tasks, verify_ok, started_at`

## 5. Prosedur satu run (LAN)
1. Master: `python -m pcomp.master --input data/silesia --expect-workers N --scheduler dynamic --out results/raw/E6/<run_id>`
2. Worker (tiap node): `python -m pcomp.worker --master <IP>:5050 --id wX`
3. Setelah selesai: `python -m pcomp.tools.verify --manifest <run>/manifest.json`
4. Periksa `metrics.json` dan `events.jsonl` ada. Salin ke repo.

## 6. Template analisis tiap eksperimen
Tujuan, konfigurasi, tabel hasil (dari CSV), grafik, pengamatan, penyebab (overhead jaringan, hukum Amdahl, I/O Master, ketimpangan task), kesimpulan. Setiap angka menyebut file sumbernya.

## 7. Catatan kejujuran data
`--repeat` menggandakan beban dari file yang sama, bukan data baru. Kompresi chunk mandiri menurunkan rasio dibanding file utuh. Keduanya dituliskan di laporan. Hasil `sim` tidak dipakai.
