# Changelog

Format mengikuti Keep a Changelog. Versi `0.<NN>.0` = akhir fase NN. Aturan pencatatan: SDLC.md bagian 6.

## [Unreleased]
### Added
- (kosong)

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
