# PLAN.md — Rencana Pengerjaan per Fase

CURRENT PHASE: 9

## Ringkasan proyek
Aplikasi kompresi data terdistribusi. Dataset dipecah menjadi chunk (task), Master membagikan task ke 9 Worker lewat TCP, tiap Worker memproses task secara paralel dengan multiprocessing, hasil kompresi dikumpulkan Master dan diverifikasi (SHA-256). Mencakup dynamic load balancing, fault tolerance, dan evaluasi performa sesuai soal UAS.

## Pemetaan kebutuhan soal ke fase
| Kebutuhan soal | Fase |
|---|---|
| a. Task decomposition | 2 |
| b. Parallel processing (multiprocessing) | 3, 4 |
| c. Distributed processing | 4 |
| d. Dynamic load balancing | 5 |
| e. Fault tolerance | 6 |
| f. Performance evaluation (6 jenis pengujian + 6 metrik) | 7, 9 |
| Minimal 10 node fisik | 8, 9 |
| Source code, laporan, video demo | 10 |

Catatan node: soal meminta minimal 10 node fisik. Berdasarkan keputusan user 2026-11-22, pelaksanaan
Fase 8 dan 9 memakai 10 node virtual di satu laptop (1 Master di host + 9 Worker container, ADR-015).
Deviasi ini wajib diungkap di laporan dan video.

## Status fase
| Fase | Nama | Ukuran | Pelaku | Status |
|---|---|---|---|---|
| 0 | Bootstrap repo dan tooling | S | Agent | DONE |
| 1 | Protokol dan infrastruktur inti | M | Agent | DONE |
| 2 | Mesin kompresi, task decomposition, baseline sequential | M | Agent | DONE |
| 3 | Local parallel (multiprocessing satu mesin) | S | Agent | DONE |
| 4 | Master–Worker inti | L | Agent | DONE |
| 5 | Dynamic load balancing | M | Agent | DONE |
| 6 | Fault tolerance | L | Agent | DONE |
| 7 | Metrik dan harness benchmark | M | Agent | DONE |
| 8 | Kesiapan multi-node | M | Agent + User | DONE |
| 9 | Eksperimen resmi 10 node virtual | L | User + Agent | TODO |
| 10 | Dokumentasi, laporan, paket pengumpulan | M | Agent + User | TODO |

Ukuran: S kecil, M sedang, L besar. Agent memperbarui kolom Status (TODO, IN PROGRESS, DONE, BLOCKED) dan `CURRENT PHASE` sebelum commit akhir fase.

## Default dan asumsi (ubah di sini bila salah)
- Python 3.11+ di semua node. Dependensi runtime: `psutil`. Dev: pytest, pytest-cov, pytest-timeout, ruff, mypy, types-psutil. Analisis: pandas, matplotlib.
- Task = satu chunk file, ukuran default 4 MiB (`--chunk-mb`).
- Algoritma default `lzma` preset 6 (berat CPU, cocok untuk menunjukkan speedup). Pilihan lain: `bz2`, `gzip`. Algoritma `sim` hanya untuk test, bukan eksperimen resmi.
- Dataset utama: Silesia Corpus. Dataset tambahan: Canterbury Large Corpus dan dataset sintetis. Beban diperbesar dengan `--repeat` (pengulangan file, diungkap di laporan). Target waktu sequential 2 sampai 10 menit.
- Data dikirim lewat TCP dari Master ke Worker (mode `transfer`). Mode `local` hanya bila jaringan menjadi bottleneck (lihat risiko R1).
- Port default 5050. Heartbeat 2 detik, timeout 6 detik, maksimal 3 percobaan per task.
- Eksperimen diulang 3 kali per konfigurasi, dilaporkan rata-rata dan simpangan baku.
- Item yang perlu diisi user: nama kelompok dan anggota (`config/group.toml`), OS tiap node lab, IP master, ada tidaknya remote git.

## Risiko
| ID | Risiko | Mitigasi |
|---|---|---|
| R1 | Bandwidth keluar Master menjadi bottleneck (data dikirim lewat jaringan) | Algoritma berat CPU (lzma), ukur transfer vs compute terpisah, cadangan `--data-mode local` di fase 8 |
| R2 | Python/OS berbeda antar node lab | `scripts/check_node.py`, cek versi protokol saat REGISTER |
| R3 | Firewall memblokir port Master | Checklist di DEPLOYMENT.md |
| R4 | Test jaringan flaky | Port ephemeral, timeout jelas, gate G7 (3 kali ulang) |
| R5 | Multiprocessing spawn di Windows/macOS | Aturan spawn-safe di AGENTS.md, test dengan `get_context("spawn")` |
| R6 | Waktu lab terbatas | Fase 8 dan 9 disiapkan lengkap agar sesi lab singkat |

---

## FASE 0 — Bootstrap repo dan tooling
Tujuan: repo siap, gate bisa berjalan, kerangka folder ada.
Task:
- P0-T1 `git init`, branch `main`, `.gitignore` (data/, output/, reports/, .venv, __pycache__, cache tools).
- P0-T2 `pyproject.toml` (src layout, paket `pcomp`, Python >= 3.11, konfigurasi ruff, mypy, pytest dengan marker `integration`, `perf`, `slow` dan timeout default 60 detik). `requirements.txt`, `requirements-worker.txt` (hanya psutil), `requirements-dev.txt`.
- P0-T3 Kerangka folder sesuai AGENTS.md bagian 5, semua paket berisi `__init__.py`.
- P0-T4 `config/group.toml` (placeholder), `config/master.toml`, `config/worker.toml`, `config/nodes.toml` berisi nilai default.
- P0-T5 `src/pcomp/constants.py`, `banner.py` (cetak identitas dari group.toml), `python -m pcomp --version`.
- P0-T6 `scripts/gate.py` (G1 sampai G9, mode `--quick`, tulis `reports/gate-latest.txt`), `Makefile` pembungkus.
- P0-T7 `README.md` singkat (setup, perintah), salin seluruh dokumen perencanaan.
Test: import paket, versi, banner dengan group.toml valid dan placeholder, gate.py parsing.
Smoke: `python -m pcomp --version` mencetak versi; `python scripts/gate.py` seluruhnya PASS.
Commit: `chore(phase-00): bootstrap repo, tooling, quality gate`

## FASE 1 — Protokol dan infrastruktur inti
Tujuan: komunikasi Master–Worker yang andal di level pesan.
Task:
- P1-T1 `protocol.py`: encode/decode frame (PROTOCOL.md), definisi tipe pesan, validasi field.
- P1-T2 `net.py`: `send_msg`, `recv_msg` (baca tepat N byte, timeout), helper connect dengan retry dan backoff.
- P1-T3 `config.py`: muat TOML, timpa dengan argumen CLI.
- P1-T4 `logging_setup.py`, `metrics/events.py` (JSONL thread-safe: ts, event, field bebas).
Test unit: round-trip frame dengan dan tanpa payload; frame datang terpotong-potong (socketpair); header terlalu besar ditolak; JSON rusak; tipe tidak dikenal; override config; events ditulis dari banyak thread tanpa rusak.
Test integration: Echo server localhost, kirim payload 10 MiB, hash sama.
Smoke: `pytest -m integration -k echo`.
Commit: `feat(phase-01): add wire protocol, networking helpers, config, event log`

## FASE 2 — Mesin kompresi, task decomposition, baseline sequential
Tujuan: pecah dataset menjadi task, kompresi, verifikasi; baseline pengujian (a).
Task:
- P2-T1 `tasks.py`: dataclass `Task`, enum `TaskState`.
- P2-T2 `chunker.py`: pindai folder (urutan deterministik), pecah file menjadi chunk, `--repeat`, abaikan file kosong.
- P2-T3 `compressor.py`: `compress(algo, level, data)`, `decompress`, registri algoritma `gzip`, `bz2`, `lzma` (+ `sim` khusus test: tidur sebanding ukuran).
- P2-T4 `manifest.py`: tulis dan baca `manifest.json` (file asal, urutan chunk, ukuran, sha256 asli, nama file hasil, ukuran hasil). Fungsi rekonstruksi dan verifikasi.
- P2-T5 `tools/make_dataset.py` (sintetis: teks, acak/tidak terkompres, berulang, ukuran bervariasi), `tools/download_corpus.py` (Silesia, Canterbury; catat SHA-256 dan tanggal unduh ke `ASSETS.md`), `tools/verify.py`.
- P2-T6 `sequential.py` CLI: proses satu proses, keluaran `metrics.json` (waktu, throughput, rasio kompresi).
Test unit: batas chunk (file lebih kecil dari chunk, kelipatan pas, sisa), rekonstruksi identik (sha256), tiap algoritma round-trip, skema manifest, urutan deterministik, `--repeat`.
Test integration: dataset sintetis kecil, sequential lalu verify = OK.
Smoke: `python -m pcomp.tools.make_dataset --out data/synth --size-mb 20` lalu `python -m pcomp.sequential --input data/synth --out output/seq` lalu `python -m pcomp.tools.verify --manifest output/seq/manifest.json` mencetak `VERIFY OK`.
Commit: `feat(phase-02): add chunker, compressor, manifest, sequential baseline`

## FASE 3 — Local parallel
Tujuan: baseline pengujian (b), dasar logika eksekusi Worker.
Task:
- P3-T1 `local_parallel.py` CLI: `multiprocessing.Pool(p)`, `imap_unordered`, fungsi kerja top-level (spawn-safe), keluaran dan manifest identik dengan sequential.
- P3-T2 Metrik: waktu, throughput, waktu sibuk per proses.
- P3-T3 Penanganan error task (dicatat, tidak mematikan pool).
Test unit: hasil sha256 sama dengan sequential; p = 1, 2, 4; start method `spawn` via `get_context("spawn")`; task error tercatat.
Test integration: sequential vs local pada dataset sintetis, manifest ekuivalen.
Smoke: bandingkan waktu sequential dan `--procs 4`, keduanya `VERIFY OK`.
Commit: `feat(phase-03): add local multiprocessing baseline`

## FASE 4 — Master–Worker inti
Tujuan: pemrosesan terdistribusi dasar, pengujian (c).
Task:
- P4-T1 Master `server.py`: accept loop, satu thread handler per Worker, registry Worker, `TaskTable` ber-lock (state machine di ARCHITECTURE.md), dispatch berbasis credit (FIFO dulu), start barrier `--expect-workers`.
- P4-T2 Master `collector.py`: tulis chunk hasil, manifest, `metrics.json`, `events.jsonl`; deteksi selesai; kirim SHUTDOWN.
- P4-T3 Worker `client.py` dan `executor.py`: connect dengan retry, REGISTER, kirim credit = jumlah proses, jalankan Pool, kirim RESULT, ulangi sampai SHUTDOWN, keluar bersih.
- P4-T4 Worker `heartbeat.py`: kirim HEARTBEAT berkala (deteksi di Master baru di fase 6).
- P4-T5 Validasi: Master memeriksa sha256 masukan dari Worker dan ukuran hasil; versi protokol berbeda ditolak.
- P4-T6 `scripts/e2e_local.py`: jalankan 1 Master + N Worker di localhost dengan port bebas.
Test unit: transisi `TaskTable`, perhitungan credit, validasi hasil.
Test integration: 1 Master + 2 dan 3 Worker; semua task DONE tepat sekali; `VERIFY OK`; Worker `--procs 2`; tidak ada Worker (timeout rapi); versi protokol tidak cocok ditolak.
Smoke: `python scripts/e2e_local.py --workers 3` mencetak `E2E OK`.
Commit: `feat(phase-04): add master-worker distributed processing core`

## FASE 5 — Dynamic load balancing
Tujuan: pengujian (d), perbandingan sebelum dan sesudah mekanisme.
Task:
- P5-T1 Antarmuka `Scheduler` di `master/scheduler.py`.
- P5-T2 `StaticScheduler`: bagi task rata per jumlah ke tiap Worker di awal (round-robin), tanpa penyeimbangan.
- P5-T3 `DynamicScheduler`: dispatch saat Worker meminta credit, urutan task terbesar dulu (LPT), kapasitas Worker tercermin dari credit.
- P5-T4 Opsi `--scheduler static|dynamic`; opsi Worker `--throttle` untuk mensimulasikan Worker lambat.
- P5-T5 Metrik: waktu sibuk per Worker, jumlah task per Worker, imbalance factor.
Test unit: urutan LPT, partisi static merata, credit habis dan terisi lagi.
Test integration (algoritma `sim`, deterministik): satu Worker dibuat lambat; dynamic menghasilkan makespan lebih kecil dan imbalance factor lebih rendah dari static (dengan margin toleransi); distribusi task berbeda antar Worker pada dynamic.
Smoke: jalankan e2e static dan dynamic, cetak ringkasan perbandingan.
Commit: `feat(phase-05): add static and dynamic schedulers with load metrics`

## FASE 6 — Fault tolerance
Tujuan: pengujian (e), pemulihan task saat Worker gagal.
Task:
- P6-T1 `monitor.py`: thread pemantau; tidak ada pesan melebihi timeout menandai Worker DEAD, tutup koneksi, kembalikan task ASSIGNED ke PENDING (attempts + 1). Putus koneksi dianggap gagal seketika.
- P6-T2 Retry dan dead-letter: task gagal sampai 3 kali menjadi FAILED, tercatat di manifest dan ringkasan, exit code Master bukan nol.
- P6-T3 Idempotensi: hasil terlambat dari Worker yang sudah DEAD atau hasil ganda diabaikan, tercatat di events.
- P6-T4 Worker bergabung ulang dengan `worker_id` sama setelah restart.
- P6-T5 Injeksi kegagalan: `--fail-after-tasks K`, `--fail-after-sec S` (keluar paksa `os._exit`), `--task-fail-rate P` dengan `--seed`; `tools/inject_failure.py` untuk mematikan proses Worker.
- P6-T6 Worker mendeteksi Master hilang dan keluar bersih.
- P6-T7 Event wajib: `worker_dead`, `task_requeued`, `task_failed`, `worker_rejoined`, dengan timestamp untuk menghitung Recovery Time.
Test unit: requeue, batas attempts, duplikat hasil diabaikan, timeout dengan jam palsu.
Test integration: Worker mati di tengah proses dan seluruh task tetap selesai dengan `VERIFY OK`; dua Worker mati bersamaan; semua Worker mati (Master berhenti rapi dengan pesan jelas); task beracun menjadi FAILED setelah 3 kali; Worker rejoin; events memuat data recovery.
Smoke: e2e dengan `--fail-after-tasks 3` pada satu Worker, hasil `E2E OK` dan ada event `worker_dead`.
Commit: `feat(phase-06): add heartbeat monitoring, requeue, retry, failure injection`

## FASE 7 — Metrik dan harness benchmark
Tujuan: pengukuran 6 metrik dan otomatisasi eksperimen E1 sampai E6.
Task:
- P7-T1 `metrics/system.py`: sampler psutil 1 Hz (CPU, memori proses dan sistem), disertakan di heartbeat Worker dan di Master, keluaran `system.csv`.
- P7-T2 `metrics/calc.py`: speedup, efficiency, throughput, imbalance, detection latency, Recovery Time (rumus di EXPERIMENTS.md).
- P7-T3 `bench/runner.py`: matriks eksperimen, ulang N kali, mode localhost (spawn Master dan Worker) dan mode LAN (Worker sudah berjalan di node), keluaran ke `results/raw/<exp>/<run_id>/` dan `results/summary.csv`.
- P7-T4 `bench/report.py`: tabel rata-rata dan simpangan baku, grafik PNG (waktu vs jumlah Worker, speedup, efficiency, throughput, CPU/memori, beban per Worker, timeline recovery). Backend matplotlib `Agg`.
- P7-T5 Metadata lingkungan otomatis (CPU, OS, versi Python, jumlah core, tanggal) ke setiap run.
Test unit: rumus dengan nilai tangan; Recovery Time dari events sintetis; agregasi.
Test integration: runner localhost dengan `sim`, 1 dan 2 Worker, 2 ulangan; hasil dan grafik terbentuk.
Smoke: `python -m pcomp.bench.runner --exp E6 --local --workers 1,2 --reps 2 --algo sim`.
Commit: `feat(phase-07): add metrics collection, calculations, benchmark harness`

## FASE 8 — Kesiapan multi-node (HUMAN-REQUIRED sebagian)
Tujuan: 10 node virtual (1 Master di host + 9 Worker container pada satu laptop) siap menjalankan
sistem. Soal meminta 10 node fisik; deviasi dicatat pada ADR-015 dan wajib diungkap di laporan.
Agent:
- P8-T1 `scripts/check_node.py` (versi Python, psutil, jumlah core, koneksi ke Master, versi protokol).
- P8-T2 `scripts/launch_workers.py` (baca `config/nodes.toml`; mode cetak perintah dan mode ssh).
- P8-T3 `scripts/pack_source.py` (ZIP tanpa data/, output/, .venv, .git).
- P8-T4 Finalisasi `DEPLOYMENT.md`, template inventaris node, checklist pra-eksperimen.
- P8-T5 Opsional bila R1 terjadi: `--data-mode local` (Worker membaca dataset lokal berdasar file, offset, panjang).
- P8-T6 Uji lokal 9 Worker di satu mesin (marker `slow`).
User (checklist, hasil dicatat di `PHASE-08.md`):
- Siapkan 9 Worker container (Python dan dependensi terpasang), jalankan `check_node.py` di 10 node virtual, catat inventaris (host, container/IP, CPU, core, RAM, OS).
- Dry-run dataset kecil di 10 node virtual, kirim log dan hasil ke agent.
Test unit: parsing nodes.toml, perintah ssh yang dibangkitkan, pengecualian ZIP, check_node dengan mock.
Smoke: uji 9 Worker lokal (`pytest -m slow`).
Commit: `feat(phase-08): add node checks, launch scripts, packaging, deployment guide`

## FASE 9 — Eksperimen resmi (HUMAN-REQUIRED)
Tujuan: data hasil nyata untuk laporan.
User: jalankan E1 sampai E6 sesuai EXPERIMENTS.md di 10 node virtual, 3 ulangan; salin `results/raw/` ke repo.
Agent:
- P9-T1 `tools/validate_results.py`: semua run punya metadata, `VERIFY OK`, skema lengkap, jumlah ulangan sesuai.
- P9-T2 Hasilkan `results/summary.csv` dan grafik final.
- P9-T3 `docs/ANALYSIS.md`: analisis tiap eksperimen. Setiap angka diambil dari CSV, sebut file sumbernya. Bahas bila speedup di bawah ideal (overhead jaringan, Amdahl, I/O).
Test unit: validator pada data valid dan rusak.
Smoke: `python -m pcomp.tools.validate_results results/raw` mencetak `RESULTS VALID`.
Commit: `docs(phase-09): add official experiment results and analysis`

## FASE 10 — Dokumentasi, laporan, paket pengumpulan
Tujuan: seluruh deliverable siap.
Task:
- P10-T1 `docs/CODE_GUIDE.md`: struktur kode dan penjelasan tiap modul secara lengkap.
- P10-T2 Draf laporan BAB I sampai BAB IV + Kesimpulan sesuai SUBMISSION.md, dibuat sebagai DOCX dengan skill `laporan-akademik-id`, tabel dan grafik dari hasil fase 9, placeholder gambar beserta instruksi.
- P10-T3 Naskah video demo (maks 5 menit) dan checklist rekaman.
- P10-T4 `README.md` final, `ASSETS.md` final (sumber resmi, tanggal akses, lisensi).
- P10-T5 Uji reproduksi: clone ke folder sementara, setup, jalankan gate penuh.
- P10-T6 `pack_source.py` menghasilkan ZIP; periksa isinya.
Test: gate penuh, uji clone bersih, isi ZIP.
Smoke: ZIP terbuat dan dapat dijalankan dari nol sesuai README.
Commit: `docs(phase-10): add code guide, report draft, demo script, final package` dan tag `v1.0.0`.
