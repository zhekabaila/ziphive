# Changelog

Format mengikuti Keep a Changelog. Versi `0.<NN>.0` = akhir fase NN. Aturan pencatatan: SDLC.md bagian 6.

## [Unreleased]
### Added
- `docs/CODE_GUIDE.md`: panduan kode dari 40 berkas `src/pcomp` (5.712 baris), 6 skrip `scripts/`, serta peta test; memuat struktur direktori, penjelasan modul/class/fungsi, alur pemanggilan sequential, local parallel, distributed, kegagalan Worker, dan benchmark, daftar berkas keluaran, serta cara menjalankan setiap perintah.
- `README.md` final: status proyek sampai Fase 9, setup `pip install -e ".[dev,analysis]"`, daftar perintah CLI/tool/skrip, struktur repo, langkah menjalankan 10 node virtual beserta rujukan `docs/evidence/RUNBOOK.md`, serta perintah test dan gate.
- `ASSETS.md` final: dataset sintetis `data/bench` (seed 20261122, 2048 MiB, SHA-256 delapan berkas), ukuran dan SHA-256 tujuh grafik serta empat tangkapan layar, versi pustaka yang tercatat, tabel formula beserta lokasi implementasi, dan status lisensi. Silesia/Canterbury tetap ditandai `PERLU DIVERIFIKASI USER` karena belum dipakai.
- `docs/evidence/RUNBOOK.md`: runbook pengambilan empat tangkapan layar bukti (10 node virtual, terminal Master, terminal Worker, bukti E5 satu Worker mati) dengan perintah yang sudah diuji pada skala 1 Master + 9 container, keluaran yang diharapkan, perkiraan durasi terukur, dan tabel penanganan masalah.
- `docs/evidence/README.md` bagian 3a: status pengambilan gambar beserta isi yang terverifikasi, bukti teks pendukung run E5 (2565/2565 task selesai, event `worker_dead` lalu `task_requeued`), dan catatan bahwa angka pada gambar bukan angka laporan.

### Changed
- `scripts/gate.py`: smoke Fase 10 Bagian A menjalankan `scripts/pack_source.py --list` dan mewajibkan `docs/CODE_GUIDE.md` muncul pada daftar paket. Smoke ZIP utuh sesuai PLAN.md fase 10 baru dapat dijalankan pada Bagian B (P10-T5 dan P10-T6).
- `PLAN.md`: status Fase 10 menjadi `IN PROGRESS` (Bagian A selesai, Bagian B belum).

### Docs
- `docs/phase-logs/PHASE-09.md` bagian 11: perintah tangkapan layar kini merujuk `docs/evidence/RUNBOOK.md`.

### Fixed
- Prosedur `docker kill` pada bukti E5 tidak lagi memakai `sleep` buta; kill hanya dijalankan setelah `docker ps` menunjukkan sembilan container `Up`, karena percobaan pertama gagal dengan `container ... is not running` dan gambar bukti harus diulang.

## [0.09.0] - 2026-11-22
### Added
- `scripts/run_experiments.py`: orkestrasi E1-E6 pada 10 node virtual. Menyalakan dan mematikan container Worker per run, membaca port Master dari `master.log` run tersebut, mematikan Worker E5 pada sekitar 50 % progres, menyimpan log tiap container, menjalankan `verify.py` lalu menulis `verify.log`, dan menghapus payload `chunks/` setelah `VERIFY OK`.
- `src/pcomp/tools/validate_results.py`: validasi kelengkapan `results/raw` (metadata, `VERIFY OK`, larangan hasil algoritma `sim`, jumlah ulangan minimal tiga, kesesuaian kolom `summary.csv`); mencetak `RESULTS VALID`.
- Unit test UT-EXP-01..07, UT-VAL-01..07, UT-BEN-09..11, dan UT-CAL-07.
- `docs/ANALYSIS.md`: analisis E1-E6 beserta angka rata-rata dan simpangan baku dari `results/summary.csv` dan `results/summary_agg.csv`.
- `docs/evidence/README.md`: perintah pengambilan tangkapan layar 10 node virtual dan bukti pemulihan E5.
- Hasil eksperimen resmi: 45 run pada `results/raw/`, `results/summary.csv`, `results/summary_agg.csv`, dan 7 grafik pada `results/figures/`; seluruh run `VERIFY OK`.

### Changed
- `src/pcomp/bench/runner.py`: opsi `--pause` beserta `pause_between_runs` (jeda 30 detik antar run), urutan run diubah menjadi ulangan di luar dan konfigurasi di dalam agar pergeseran beban mesin tidak membiaskan satu konfigurasi, grafik dan `summary_agg.csv` dibangun dari seluruh baris `summary.csv` (bukan hanya eksperimen terakhir), serta kolom baru `kill_workers`.
- `src/pcomp/bench/report.py`: `kill_workers` masuk kunci agregat sehingga dua skenario E5 tidak tergabung; `plot_worker_load` memilih run terdistribusi dengan konfigurasi berbeda, bukan empat run pertama.
- `src/pcomp/metrics/calc.py`: `recovery_stats` dan `recovery_time` menghitung seluruh Worker yang diinjeksi, sehingga `retried_tasks` skenario tiga Worker benar.
- `scripts/gate.py`: smoke Fase 9 menjalankan `validate_results` dengan penanda `RESULTS VALID`.
- `EXPERIMENTS.md` bagian 4: skema `summary.csv` memuat `kill_workers`.
- `PLAN.md`: Fase 9 `DONE`, `CURRENT PHASE` menjadi 10.

### Fixed
- Runner tidak membaca ulang `summary.csv` sehingga grafik dan agregat hanya berisi eksperimen terakhir.
- `check_artifacts` dan `validate_results` mewajibkan `events.jsonl` pada mode `sequential` dan `local` yang memang tidak menulisnya.

### Docs
- `docs/phase-logs/PHASE-09.md`: parameter terkunci (dataset 2048 MiB, `lzma` 6, chunk 4 MiB, `--repeat 1`, 3 ulangan, jeda 30 detik), deviasi, masalah, dan keterbatasan.
- Catatan keterbatasan: `cpu_avg_workers` tidak dapat dipakai karena sampler membaca proses utama Worker sedangkan kompresi berjalan pada proses anak `multiprocessing.Pool`; analisis beban memakai `busy_sec`.

## [0.08.0] - 2026-11-22
### Added
- `scripts/check_node.py`: pemeriksaan kesiapan node (versi Python minimal 3.11, psutil, versi paket dan `PROTOCOL_VERSION`, jumlah core, RAM) serta opsi `--master host:port` dan `--ping-master` untuk menguji keterjangkauan port Master tanpa mengirim pesan protokol.
- `scripts/launch_workers.py`: membaca `config/nodes.toml`, memisahkan peran Master dan Worker, menolak placeholder yang belum diisi, lalu membangkitkan perintah Worker `python -m pcomp.worker --master <host:port> --id w<N> --procs <P>`; mode `--print`, `--ssh`, dan `--ssh --dry-run`.
- `scripts/pack_source.py`: arsip ZIP sumber berisi `src/`, `tests/`, `scripts/`, `config/`, `docs/`, dokumen `.md`, `pyproject.toml`, `requirements*.txt`, `Makefile`, dan `results/`, tanpa `data/`, `output/`, `.venv`, `.git`, cache, dan `results/dev/`.
- Unit test UT-NODE-01..04, UT-LAUNCH-01..04, UT-PACK-01..03 dan integration test SL-9W-01 (9 Worker lokal, marker `slow`).
- Fixture `load_script` pada `tests/conftest.py` untuk memuat berkas `scripts/` sebagai modul di unit test.
- Validasi 10 node virtual pada satu laptop (ADR-015): image `ziphive-node:min` (Alpine 3.20, Python 3.12.13, psutil 5.9.8, 77,8 MB), 1 Master di host dan 9 Worker container, seluruh node `CHECK NODE OK`, serta dry-run 64 MiB `VERIFY OK` (17 task, 9 Worker, 2,62 detik, 24,46 MB/s).

### Changed
- `DEPLOYMENT.md`: template inventaris 10 node, langkah `pip install -e .`, contoh keluaran `check_node.py`, pemakaian `launch_workers.py` dan `pack_source.py`, checklist pra-eksperimen, serta catatan bahwa `--data-mode local` belum tersedia.
- Rencana pelaksanaan Fase 8 dan 9 diubah dari 10 node fisik menjadi 10 node virtual (1 Master di host + 9 Worker container pada satu laptop) berdasarkan keputusan user 2026-11-22 (ADR-015); `AGENTS.md`, `PLAN.md`, `PROMPTS.md`, `SUBMISSION.md`, `DEPLOYMENT.md`, dan `ARCHITECTURE.md` disesuaikan. Persetujuan dosen: TIDAK DIKETAHUI.

### Docs
- `DEPLOYMENT.md` bagian 1 diisi dari data nyata n1 (Master, macOS 26.6.2, Apple M1, 8 core, 8.0 GiB, Python 3.14.4); baris n2 sampai n10 ditandai `TIDAK ADA DATA`.
- `DEPLOYMENT.md` bagian 2 menambahkan catatan Debian 11 (Python 3.9.2, tanpa `bullseye-backports`) beserta cara menyiapkan Python 3.11 dari sumber, dan tabel troubleshooting memuat gejala tersebut serta peringatan `koneksi Worker berakhir` akibat `check_node.py --master`.
- `docs/phase-logs/PHASE-08.md` bagian 13 diisi checklist 10 node virtual, bagian 13.1 sampai 13.2 memuat bukti `check_node.py` n1 serta validasi 2 mesin (Master macOS + VM Debian arm64), dan bagian 13.3 sampai 13.4 memuat keputusan serta bukti dry-run 10 node virtual dengan `VERIFY OK`.
- `DEPLOYMENT.md` bagian 0 memuat runbook 10 node virtual (image Alpine minimal, perintah Master dan Worker container, `host.docker.internal`).

- `scripts/gate.py`: smoke Fase 8 menjalankan `pytest -m slow` dengan penanda `1 passed`.
- `ARCHITECTURE.md` bagian 11 mencatat bahwa `--data-mode local` belum tersedia (ADR-014).
- `PLAN.md`: status Fase 8 menjadi `DONE` dan `CURRENT PHASE` menjadi 9; catatan deviasi 10 node virtual ditambahkan.

## [0.07.0] - 2026-11-21
### Added
- `src/pcomp/metrics/system.py`: `Sample`, `ProcessSampler`, `SystemSampler` (psutil 1 Hz dengan sumber dan jam yang dapat disuntikkan), `SystemLog` penulis `system.csv` thread-safe, `read_system_csv`, dan `summarise_usage` untuk rata-rata pemakaian per peran.
- `src/pcomp/metrics/calc.py`: speedup, efficiency, throughput, imbalance factor, detection latency, Recovery Time, dan `recovery_stats` dari events, seluruhnya mengikuti EXPERIMENTS.md bagian 3.
- `src/pcomp/bench/runner.py`: harness E1-E6 (`plan_runs`, `RunSpec`), eksekusi sequential/local/distributed/lan, metadata lingkungan `env.json` (CPU, OS, versi Python, core, RAM, tanggal), `system.csv` per run, kolom `summary.csv` persis EXPERIMENTS.md bagian 4, dan verifikasi manifest tiap run.
- `src/pcomp/bench/report.py`: agregasi rata-rata serta simpangan baku per konfigurasi dan tujuh grafik PNG (`time_vs_workers`, `speedup`, `efficiency`, `throughput`, `cpu_mem`, `worker_load`, `recovery_timeline`) dengan backend `Agg`.
- Hasil algoritma `sim` ditulis ke `results/dev/` (`results/dev/raw`-nya sendiri, `results/dev/summary.csv`, `results/dev/figures`), sedangkan algoritma nyata ke `results/raw/`, `results/summary.csv`, dan `results/figures`; metadata `algo` selalu tercatat pada `spec.json` dan `metrics.json` agar validator Fase 9 dapat menolak data simulasi.
- Unit test UT-CAL-01..04, UT-SYS-01..03, UT-BEN-01..07, UT-RPT-01..02 dan integration test IT-BENCH-01.
- Dependensi opsional `analysis` (`matplotlib>=3.7`) pada `pyproject.toml`, `requirements-dev.txt`, dan ADR-012.

### Changed
- `src/pcomp/master/server.py`: `SystemLog` dan `SystemSampler` peran `master` berjalan di `run()`, dan setiap HEARTBEAT Worker dicatat ke `system.csv` lewat `_record_usage`.
- `src/pcomp/worker/heartbeat.py`: `HeartbeatSender` menerima `sampler`; nilai `cpu_percent` dan `mem_percent` kini berasal dari psutil, bukan 0.0.
- `src/pcomp/worker/client.py`: heartbeat memakai `ProcessSampler().usage`.
- `src/pcomp/constants.py`: `SYSTEM_SAMPLE_INTERVAL`, `SYSTEM_CSV_NAME`, `BENCH_ENV_NAME`, dan versi `0.07.0`.
- `scripts/gate.py`: smoke Fase 7 menjalankan `python -m pcomp.bench.runner --exp E6 --local --workers 1,2 --reps 2 --algo sim` dengan penanda `BENCH OK`.
- `.gitignore`: `results/dev/` tidak dilacak karena hanya memuat hasil algoritma `sim`.
- `TESTING.md` bagian 4 memuat baris UT-SYS, UT-BEN, dan UT-RPT.

## [0.06.0] - 2026-11-21
### Added
- `src/pcomp/master/monitor.py`: `Monitor` dengan timeout heartbeat, jam yang dapat diganti jam palsu pada unit test, thread latar yang dapat dihentikan, dan pemanggilan `MasterState.drop_worker` untuk setiap Worker DEAD.
- `src/pcomp/tasks.py`: `Task.fail_reason`, `TaskTable.requeue_task`, `requeue_from`, `fail_unfinished`, dan `failed_tasks` untuk pemulihan task serta dead-letter.
- `src/pcomp/manifest.py`: `FailedEntry` dan larik `failed` pada manifest (aditif, `MANIFEST_VERSION` tetap 1); `Collector.write_manifest(failed=...)`.
- `src/pcomp/worker/executor.py`: `task_fail_rate` dengan `seed` tetap untuk mensimulasikan kegagalan task deterministik.
- `src/pcomp/tools/inject_failure.py`: pencatatan `worker_exit_injected` lalu penghentian proses Worker (`SIGTERM`).
- Event `worker_dead`, `task_requeued`, `task_failed`, `worker_rejoined`, `late_or_duplicate`, dan `worker_exit_injected`, seluruhnya bertimestamp.
- `metrics.json` distributed memuat `tasks_retried`, `failed_tasks`, dan `worker_stats` agregat per `worker_id` (termasuk sesi Worker yang mati atau bergabung ulang).
- Worker: `--fail-after-tasks`, `--fail-after-sec`, `--task-fail-rate`, `--seed`. Master: `--heartbeat-interval`, `--heartbeat-timeout`, `--max-attempts`.
- Unit test UT-MON-01..03, UT-TBL-07..09, UT-SCH-07..08, UT-WRK-12..13, UT-MAN-04, UT-TOOL-03, UT-WCLI-04, UT-MCLI-05, UT-MST-07..10 dan integration test IT-FT-01..07.

### Changed
- `src/pcomp/master/server.py`: `MasterState.register` membedakan `worker_registered` dan `worker_rejoined`; `handle_result` melakukan retry sampai `max_attempts` lalu dead-letter; hasil ganda atau terlambat dicatat `late_or_duplicate`; `drop_worker` menutup sesi dan me-requeue task; `abort` menandai task belum selesai sebagai FAILED bila semua Worker mati; dispatch yang gagal mengirim task me-requeue task dan menjatuhkan Worker.
- `src/pcomp/master/scheduler.py`: hook `on_worker_dead` dan `on_requeue`; `StaticScheduler` memindahkan jatah Worker mati ke antrean bersama.
- `src/pcomp/master/server.py`: exit code Master bukan nol bila ada task FAILED atau masih PENDING/ASSIGNED.
- `src/pcomp/worker/client.py`: socket memakai timeout heartbeat, deteksi Master hilang (`MASTER HILANG`) untuk timeout maupun koneksi terputus, serta timer `fail_after_sec`.
- `src/pcomp/master/cli.py`, `src/pcomp/worker/cli.py`: opsi baru masuk `OVERRIDE_KEYS` sehingga dapat menimpa TOML.
- `scripts/e2e_local.py`: opsi injeksi kegagalan dan heartbeat, toleransi Worker pertama yang sengaja dimatikan, pemeriksaan event `worker_dead`; `events.jsonl` lama dihapus setiap run agar hitungan event hanya berasal dari run tersebut.
- `scripts/gate.py`: smoke Fase 6 memakai `--fail-after-tasks 3` dengan penanda `E2E OK` dan `worker_dead`.
- `ARCHITECTURE.md` bagian 4, 7, 8 dan `TESTING.md` bagian 4 disinkronkan dengan perilaku Fase 6.

## [0.05.0] - 2026-11-21
### Added
- `src/pcomp/master/scheduler.py`: antarmuka `Scheduler`, `StaticScheduler` (partisi round-robin saat barrier), `DynamicScheduler` (LPT berbasis credit), `build_scheduler`, dan `imbalance_factor`.
- `src/pcomp/tasks.py`: `TaskTable.take_largest` (LPT, seri diputus task_id terkecil) dan `take_task` untuk jatah static; `take_next` tetap FIFO.
- Worker `--throttle`: jeda per task di dalam proses pool untuk meniru Worker lambat, ikut terhitung pada `compute_sec`.
- `metrics.json` distributed memuat `scheduler` (`static` atau `dynamic`) dan `imbalance` = max(busy) / mean(busy).
- `scripts/e2e_local.py`: opsi `--scheduler`, `--throttle`, `--repeat`, dan mode `--compare` yang menjalankan static lalu dynamic serta mencetak ringkasan perbandingan.
- Unit test UT-SCH-01..06, UT-WRK-11 dan integration test IT-LB-01..02.

### Changed
- `src/pcomp/master/server.py`: dispatch memakai scheduler yang dipilih; `MasterState` menerima objek `Scheduler`.
- `src/pcomp/master/cli.py`: `--scheduler static` kini diterima (sebelumnya ditolak pada Fase 4).
- `src/pcomp/config.py`: validasi `throttle` menjadi tidak negatif; `config/worker.toml` default `throttle = 0.0`.
- `src/pcomp/worker/client.py`: `Executor` menerima `throttle` dari konfigurasi Worker.
- `scripts/gate.py`: smoke Fase 5 memakai `scripts/e2e_local.py --compare` dengan penanda `LB COMPARE OK`.
- `TESTING.md` bagian 4: perbarui UT-SCH-01..06, UT-WRK-11, UT-MCLI-02, dan IT-LB-01..02.

## [0.04.0] - 2026-11-20
### Added
- `src/pcomp/tasks.py`: `TaskTable` ber-lock dengan dispatch FIFO (`take_next`), klaim hasil idempoten (`claim_result`), `mark_done`, `mark_failed`, `counts`, `all_finished`, `snapshot`.
- `src/pcomp/master/server.py`: `MasterServer` dengan accept loop dan satu thread handler per Worker, registry `WorkerSession` berbasis credit, barrier `--expect-workers`, dispatch FIFO, validasi hasil (sha256 masukan, ukuran asli, ukuran payload), serta `MasterState` yang bebas socket agar mudah diuji.
- `src/pcomp/master/collector.py`: penulisan chunk hasil, `manifest.json`, `metrics.json`, dan entri `events.jsonl`.
- `src/pcomp/master/cli.py`, `src/pcomp/master/__main__.py`: entry point `python -m pcomp.master` dengan penimpaan TOML oleh CLI dan `--barrier-timeout`.
- `src/pcomp/worker/client.py`, `executor.py`, `heartbeat.py`, `cli.py`, `__main__.py`: Worker yang mendaftar, meminta credit, mengompresi di `multiprocessing.Pool`, mengirim `RESULT`, dan mengirim heartbeat berkala.
- `scripts/e2e_local.py`: smoke end-to-end 1 Master + N Worker di localhost dengan port bebas dan pencetakan `E2E OK`.
- Unit test UT-TBL-01..06, UT-COL-01..03, UT-MST-01..06, UT-WRK-01..10, UT-MCLI-01..04, UT-WCLI-01..03 dan integration test IT-DIST-01..05.

### Changed
- `src/pcomp/constants.py`: tambah `DEFAULT_BARRIER_TIMEOUT`; `__version__` dan versi `pyproject.toml` menjadi `0.04.0`.
- `tests/conftest.py`: fixture `free_port`, `synth_dataset`, `module_runner`, `start_master`, `start_worker`, `events_of`.
- `scripts/gate.py`: smoke Fase 4 memakai `scripts/e2e_local.py --workers 3` dengan penanda `E2E OK`.
- `TESTING.md` bagian 3 dan 4: tambah `module_runner`, UT-COL, UT-MST, UT-WRK.

### Fixed
- Master menunggu `BYE` setelah `SHUTDOWN` sehingga koneksi tidak direset dan Worker tidak keluar dengan kode galat.
- `build_register_header` mengisi `v` dan `version` dengan nilai sama agar penolakan versi protokol benar-benar terjadi.
- CLI Master mengubah `FileNotFoundError` folder input menjadi pesan `MASTER GAGAL`, bukan traceback.

## [0.03.0] - 2026-11-20
### Added
- `src/pcomp/local_parallel.py`: baseline paralel satu mesin dengan `multiprocessing.Pool` start method `spawn`, `imap_unordered`, fungsi kerja top-level `run_task`, serta `manifest.json` dan `metrics.json` yang identik dengan baseline sequential.
- `metrics.json` local memuat `time_s`, `throughput_mbs`, `busy_per_process`, `tasks_ok`, `tasks_failed`, dan `errors`.
- `compressor.compress_task` dan `compressor.TaskResult`: kompresi satu task dengan penanganan error, dipakai bersama baseline local dan Worker Fase 4.
- `manifest.make_entry`: helper pembentuk entri manifest untuk sequential, local, dan collector.
- Unit test UT-LOC-01..05 dan integration test IT-LOC-01.

### Changed
- `src/pcomp/constants.py`: tambah `DEFAULT_PROCS`; `__version__` dan versi `pyproject.toml` menjadi `0.03.0`.
- `src/pcomp/sequential.py`: memakai `manifest.make_entry` (perilaku tidak berubah).
- `scripts/gate.py`: smoke Fase 3 (sequential, local `--procs 4`, verify) dengan penanda `SEQUENTIAL OK` dan `LOCAL OK`.
- `TESTING.md` bagian 4: tambah baris UT-LOC-01..05 dan IT-LOC-01.

## [0.02.0] - 2026-11-20
### Added
- `src/pcomp/tasks.py`: dataclass `Task` dan enum `TaskState` (PENDING, ASSIGNED, DONE, FAILED).
- `src/pcomp/chunker.py`: pemindaian folder deterministik, pemecahan file per chunk, `--repeat`, file kosong dilewati.
- `src/pcomp/compressor.py`: registri `gzip`, `bz2`, `lzma`, `sim` (khusus test) dengan `compress`, `decompress`, `file_extension`, `is_simulated`.
- `src/pcomp/manifest.py`: `manifest.json` versi 1, validasi skema, rekonstruksi file, verifikasi per chunk (ukuran dan SHA-256).
- `src/pcomp/sequential.py`: baseline satu proses beserta `metrics.json` (waktu, throughput, rasio, jumlah task, penanda `simulated`).
- `src/pcomp/tools/make_dataset.py`: dataset sintetis deterministik (teks, acak, berulang, campuran) dengan `dataset.json`.
- `src/pcomp/tools/download_corpus.py`: unduhan korpus dengan URL wajib eksplisit, `--expected-sha256`, dan `--dry-run`; tidak dijalankan otomatis.
- `src/pcomp/tools/verify.py`: verifikasi manifest, mencetak `VERIFY OK` atau daftar chunk rusak.
- Unit test UT-TSK-01..02, UT-CHK-01..05, UT-CMP-01..03, UT-MAN-01..03, UT-SEQ-01, UT-TOOL-01..02 dan integration test IT-SEQ-01.

### Changed
- `src/pcomp/constants.py`: tambah `MIB`, `DEFAULT_CHUNK_MB`, `DEFAULT_REPEAT`, `DEFAULT_ALGO`, `DEFAULT_LEVEL`, `SIM_SECONDS_PER_MB`; `__version__` dan versi `pyproject.toml` menjadi `0.02.0`.
- `src/pcomp/banner.py`: tambah `try_print_banner` agar CLI tetap berjalan bila `group.toml` belum lengkap.
- `scripts/gate.py`: smoke Fase 2 (`make_dataset`, `sequential`, `verify`) dan pengecekan keluaran `VERIFY OK`.
- `TESTING.md` bagian 4: tambah baris UT-TSK, UT-SEQ, UT-TOOL, IT-SEQ.
- `ASSETS.md`: kolom tanggal akses dan SHA-256 dataset diisi "diisi user" karena belum ada unduhan nyata.

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
