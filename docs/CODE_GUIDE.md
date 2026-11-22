# CODE_GUIDE.md — Panduan Kode ZipHive

Dokumen ini menjelaskan struktur kode yang benar-benar ada di repo pada Fase 10 (versi paket
`1.0.0`). Isinya disusun dari pembacaan berkas sumber, bukan dari rencana. Rujukan desain yang
lebih konseptual ada di `ARCHITECTURE.md` (komponen dan state machine), `FLOW.md` (urutan
kejadian), dan `PROTOCOL.md` (format pesan). Panduan ini menjelaskan **di mana** setiap hal
diimplementasikan dan **bagaimana** memakainya.

Angka yang dipakai di sini: 40 berkas Python di `src/pcomp` (5.712 baris), 6 skrip di `scripts/`
(1.912 baris), 34 berkas unit test dan 9 berkas integration test di `tests/`.

## 1. Peta direktori

```
src/pcomp/                 paket Python utama (import name: pcomp)
  __init__.py              metadata paket
  __main__.py              CLI `python -m pcomp` (versi dan banner)
  constants.py             seluruh konstanta dan nilai default
  config.py                pemuatan TOML + override CLI
  logging_setup.py         konfigurasi logging
  banner.py                banner identitas kelompok dari config/group.toml
  protocol.py              frame, tipe pesan, validasi field
  net.py                   helper socket (kirim/terima frame, connect retry)
  tasks.py                 Task, TaskState, TaskTable (state machine ber-lock)
  chunker.py               pemindaian dataset dan pemecahan menjadi chunk
  compressor.py            registri algoritma dan compress_task
  manifest.py              manifest.json: tulis, baca, rekonstruksi, verifikasi
  sequential.py            baseline satu proses (CLI)
  local_parallel.py        baseline multiprocessing satu mesin (CLI)
  master/                  sisi Master
    server.py              MasterState + MasterServer (accept loop, dispatch)
    scheduler.py           Scheduler, StaticScheduler, DynamicScheduler
    monitor.py             pemantau heartbeat dan requeue
    collector.py           penulisan chunk, manifest, metrics
    cli.py                 CLI `python -m pcomp.master`
  worker/                  sisi Worker
    client.py              WorkerClient (REGISTER, TASK, RESULT, BYE)
    executor.py            Executor (multiprocessing.Pool)
    heartbeat.py           HeartbeatSender
    cli.py                 CLI `python -m pcomp.worker`
  metrics/
    events.py              EventLog JSONL thread-safe
    system.py              sampler psutil dan system.csv
    calc.py                rumus metrik dan statistik recovery
  bench/
    runner.py              harness E1-E6
    report.py              agregasi dan grafik PNG
  tools/
    make_dataset.py        dataset sintetis deterministik
    download_corpus.py     unduh korpus dari URL resmi
    verify.py              verifikasi manifest
    inject_failure.py      hentikan proses Worker dari luar
    validate_results.py    validasi results/raw
scripts/                   utilitas di luar paket (dijalankan dengan python scripts/...)
  gate.py                  Verification Gate G1-G9
  e2e_local.py             uji end-to-end 1 Master + N Worker di localhost
  check_node.py            pemeriksaan kesiapan node
  launch_workers.py        cetak/jalankan perintah Worker dari config/nodes.toml
  pack_source.py           paket ZIP sumber
  run_experiments.py       orkestrasi E1-E6 pada 10 node virtual
tests/
  conftest.py              fixture bersama
  unit/                    unit test per modul
  integration/             test dengan proses dan socket nyata
config/                    group.toml, master.toml, worker.toml, nodes.toml
```

## 2. Modul inti

### 2.1 `constants.py`

Satu tempat untuk seluruh nilai tetap. Tidak ada state yang dapat berubah.

| Kelompok | Nilai penting |
|---|---|
| Identitas | `PROJECT_NAME="ZipHive"`, `PACKAGE_NAME="pcomp"`, `__version__="1.0.0"` |
| Protokol | `PROTOCOL_VERSION=1`, `FRAME_PREFIX_SIZE=12` (4 byte panjang header + 8 byte panjang payload), `MAX_HEADER_BYTES=64 KiB`, `MAX_PAYLOAD_BYTES=64 MiB` |
| Jaringan | `DEFAULT_PORT=5050`, `DEFAULT_SOCKET_TIMEOUT=30.0`, `DEFAULT_CONNECT_TIMEOUT=5.0`, `DEFAULT_CONNECT_ATTEMPTS=10`, backoff `0.5` sampai `5.0` detik |
| Heartbeat | `DEFAULT_HEARTBEAT_INTERVAL=2.0`, `DEFAULT_HEARTBEAT_TIMEOUT=6.0`, `DEFAULT_MAX_ATTEMPTS=3`, `DEFAULT_BARRIER_TIMEOUT=120.0` |
| Kompresi | `DEFAULT_ALGO="lzma"`, `DEFAULT_LEVEL=6`, `DEFAULT_CHUNK_MB=4`, `DEFAULT_REPEAT=1`, `SIM_SECONDS_PER_MB=0.02` |
| Metrik | `SYSTEM_SAMPLE_INTERVAL=1.0`, `SYSTEM_CSV_NAME="system.csv"`, `BENCH_ENV_NAME="env.json"` |
| Lain | `MIB=1024*1024`, `DEFAULT_PROCS=4`, `EXIT_OK=0`, `EXIT_ERROR=1` |

`PROTOCOL_VERSION` dan `__version__` wajib naik bila format pesan berubah (`PROTOCOL.md`).

### 2.2 `config.py`

Membaca TOML lalu menimpa nilainya dengan argumen CLI.

- `MasterConfig` dan `WorkerConfig` adalah `@dataclass(frozen=True)`. Field-nya mengikuti
  `ARCHITECTURE.md` bagian 10 dan `config/*.toml`.
- `load_toml(path)` mengubah `tomllib.TOMLDecodeError` menjadi `ConfigError`.
- `_merged(path, default_path, overrides)` memuat TOML; nilai `None` pada `overrides` diabaikan
  sehingga CLI hanya menimpa yang benar-benar diberikan.
- `load_master_config(path, overrides)` dan `load_worker_config(path, overrides)` memvalidasi
  nilai: port 1-65535, `level` 0-9, `chunk_mb >= 1`, `repeat >= 1`, scheduler `static|dynamic`,
  `expect_workers >= 1`, heartbeat positif, `max_attempts >= 1`, `throttle >= 0`,
  `task_fail_rate` 0-1. Kesalahan dilempar sebagai `ConfigError` (turunan `ValueError`).

CLI Master memakai `OVERRIDE_KEYS` di `master/cli.py`; CLI Worker memakai `OVERRIDE_KEYS` di
`worker/cli.py`. Kunci yang tidak ada di daftar itu tidak dapat ditimpa dari CLI.

### 2.3 `logging_setup.py`

`setup_logging(level, log_file=None, logger_name="pcomp")` menyiapkan satu handler stream dan
opsional handler file. Handler lama yang ditandai `_pcomp_handler` dilepas lebih dulu, sehingga
fungsi aman dipanggil berulang (dipakai test dan CLI). Format baku:
`"%(asctime)s %(levelname)s %(name)s: %(message)s"`.

### 2.4 `banner.py`

Membaca `config/group.toml` dan mencetak identitas kelompok (AGENTS.md bagian 3).

- `Member` dan `GroupInfo` menyimpan nama, NPM, tema, mata kuliah, institusi, dan nama kelompok.
- `is_placeholder(value)` mendeteksi penanda `<ISI ...>` atau `BELUM DIISI`.
- `load_group_info(path)` memvalidasi field wajib; `GroupInfo.has_placeholder` bernilai benar bila
  masih ada placeholder.
- `render_banner(info)` menyusun teks, `print_banner(info)` mencetaknya.
- `try_print_banner(path)` dipakai semua CLI: bila file tidak ada atau placeholder terdeteksi,
  program mencetak peringatan dan tetap berjalan. Nilai placeholder diisi user, bukan agent.

### 2.5 `protocol.py`

Implementasi `PROTOCOL.md` bagian 1 dan 2.

- `MessageType` (StrEnum): `REGISTER`, `REGISTER_ACK`, `REQUEST`, `TASK`, `RESULT`, `HEARTBEAT`,
  `HEARTBEAT_ACK`, `SHUTDOWN`, `BYE`, `ERROR`.
- `ErrorCode`: `VERSION_MISMATCH`, `DUPLICATE_WORKER`, `BAD_FRAME`, `UNKNOWN_TYPE`, `INTERNAL`.
- `Frame(header, payload)` adalah hasil baca satu frame.
- `REQUIRED_FIELDS` memetakan setiap tipe pesan ke field wajib beserta validator tipe. Contoh
  `TASK` wajib memuat `task_id`, `file`, `index`, `algo`, `level`, `orig_size`, `sha256`;
  `RESULT` wajib memuat `task_id`, `ok`, `orig_size`, `comp_size`, `sha256_in`, `compute_sec`,
  `error`.
- `encode_header` menolak header di atas 64 KiB; `decode_header` menolak JSON rusak atau bukan
  objek.
- `decode_frame_prefix` membaca `!I` (header) dan `!Q` (payload) lalu memeriksa batas ukuran.
- `encode_frame` menyusun `prefix + header JSON + payload`; `build_frame` membangun sekaligus
  memvalidasi header siap kirim.
- `validate_message(header, expected_version=PROTOCOL_VERSION)` memeriksa `type`, `v`, field
  wajib, `credits > 0` pada `REQUEST`, dan kode `ERROR` yang dikenal. Field tambahan diabaikan
  (aturan kompatibilitas).
- Pengecualian: `ProtocolError`, `BadFrameError`, `UnknownMessageTypeError`,
  `VersionMismatchError`.

### 2.6 `net.py`

- `recv_exact(sock, size)` membaca tepat `size` byte dari potongan TCP; `ConnectionError` bila
  koneksi tertutup lebih awal.
- `send_msg(sock, header, payload=b"")` mengirim satu frame utuh.
- `recv_msg(sock)` membaca prefix 12 byte, lalu header, lalu payload sesuai panjang yang
  dideklarasikan.
- `connect_with_retry(host, port)` mencoba `DEFAULT_CONNECT_ATTEMPTS` kali dengan backoff;
  kegagalan terakhir menjadi `ConnectionError`.
- `close_quietly(sock)` menutup socket tanpa melempar error.

Semua socket yang dibuka pemanggil wajib mendapat timeout. Master memakai
`DEFAULT_SOCKET_TIMEOUT`; Worker memakai `DEFAULT_HEARTBEAT_TIMEOUT` setelah REGISTER agar
koneksi mati terdeteksi lebih cepat.

### 2.7 `tasks.py`

Model state task sesuai `ARCHITECTURE.md` bagian 4.

- `TaskState`: `PENDING`, `ASSIGNED`, `DONE`, `FAILED`.
- `Task` menyimpan `task_id`, `file`, `index`, `offset`, `length`, state, `attempts`,
  `assigned_to`, `assigned_at`, `sha256`, `comp_size`, `done_at`, `fail_reason`.
- `TaskTable` melindungi seluruh isi dengan satu `threading.Lock`.
  - `take_next` mengambil `task_id` terkecil (FIFO).
  - `take_largest` mengambil task terbesar (LPT); seri diputus `task_id` terkecil.
  - `take_task` mengambil task tertentu (dipakai scheduler static).
  - `_assign` menaikkan `attempts` dan mengisi `assigned_to`/`assigned_at`.
  - `claim_result` hanya mengembalikan task berstatus `ASSIGNED` milik Worker pengirim; hasil
    ganda atau terlambat ditolak.
  - `mark_done`, `mark_failed`, `requeue_task`, `requeue_from`, `fail_unfinished` memindahkan
    state secara atomik.
  - `_requeue_locked` mengembalikan task ke `PENDING`, atau menandainya `FAILED` bila
    `attempts >= max_attempts` (dead-letter).
  - `counts`, `all_finished`, `failed_tasks`, `snapshot` dipakai Master saat finalisasi.

### 2.8 `chunker.py`

- `chunk_size_bytes(chunk_mb)` mengubah MiB ke byte (`chunk_mb >= 1`).
- `scan_files(root)` memindai `root.rglob("*")`, melewati file kosong, dan mengurutkan berdasarkan
  path relatif POSIX agar deterministik.
- `plan_tasks(root, chunk_mb, repeat)` memecah tiap file menjadi `Task` berurutan. `repeat > 1`
  mengulang seluruh daftar file sehingga `task_id` bertambah terus; salinan dibedakan di manifest.
- `read_chunk(root, task)` membuka file, `seek(offset)`, lalu membaca `length` byte.
- `copy_index(task_id, per_copy)` menghitung nomor salinan `--repeat`.

### 2.9 `compressor.py`

- `ALGORITHMS = ("gzip", "bz2", "lzma", "sim")`; ekstensi hasil `gz`, `bz2`, `xz`, `sim`.
- `_validate(algo, level)` menolak algoritma tak dikenal, level di luar 0-9, dan `bz2` level 0.
- `compress` dan `decompress` memakai modul stdlib (`gzip`, `bz2`, `lzma`). Algoritma `sim`
  hanya tidur `SIM_SECONDS_PER_MB` detik per MiB dan mengembalikan data apa adanya.
- `TaskResult` menyimpan `task_id`, `ok`, `sha256`, `comp_size`, `data`, `error`, `compute_sec`.
- `compress_task(task, data, algo, level)` menghitung SHA-256 data masukan, menangkap semua
  pengecualian kompresi sebagai `ok=False`, dan mengukur `compute_sec`. Fungsi ini netral modul
  supaya baseline lokal dan Worker memakai logika yang sama.
- `file_extension(algo)` dan `is_simulated(algo)` dipakai manifest dan harness.

### 2.10 `manifest.py`

`manifest.json` adalah bukti hasil kompresi: satu entri per chunk, berisi hash data asli.

- `ManifestEntry` (task, file, index, offset, length, sha256, output, comp_size, copy) dan
  `FailedEntry` (task, file, index, offset, length, attempts, reason).
- `Manifest` menyimpan `version=1`, algoritma, level, chunk size, repeat, total byte asli dan
  hasil, daftar entri, serta daftar gagal. Properti `ratio = total_orig_bytes /
  total_comp_bytes`.
- `chunk_output_name(file, index, algo, copy, repeat)` menghasilkan
  `chunks/<file>.<index:04d>.<ext>`; bila `repeat > 1` menjadi `chunks/r<copy>/...`.
- `make_entry`, `build_manifest`, `to_dict`, `from_dict` menyusun dan memvalidasi struktur.
  `_require` menolak field hilang atau bertipe salah (`ManifestError`).
- `write_manifest`/`read_manifest` menulis dan membaca JSON indentasi 2.
- `reconstruct_file(manifest, out_dir, file, copy=0)` menggabungkan chunk satu file setelah
  dekompresi.
- `verify_entries(manifest, out_dir)` mendekompresi setiap chunk, membandingkan panjang dan
  SHA-256 dengan manifest, dan mengembalikan `EntryVerification(entry, ok, reason)`.

### 2.11 `sequential.py`

Baseline satu proses (eksperimen E1).

- `run_sequential(input_dir, out_dir, algo, level, chunk_mb, repeat, ...)`:
  `plan_tasks` → untuk setiap task `read_chunk` → `compress_task` → tulis chunk lewat
  `chunk_output_name` → `build_manifest`/`write_manifest` → `metrics.json`.
- `SequentialResult(manifest, metrics)` mengembalikan hasil dalam bentuk objek.
- CLI: `python -m pcomp.sequential --input ... --out ...` dengan opsi `--algo`, `--level`,
  `--chunk-mb`, `--repeat`, `--group-config`. Cetakan akhir `SEQUENTIAL OK`.

### 2.12 `local_parallel.py`

Baseline paralel satu mesin (eksperimen E2) sekaligus tempat `pool_context()` yang dipakai Worker.

- `LOCAL_START_METHOD = "spawn"`; `pool_context()` mengembalikan konteks spawn agar aman di
  macOS dan Windows (AGENTS.md aturan 8).
- `run_task(payload)` adalah fungsi top-level: menerima `(task, input_dir, algo, level)`, membaca
  chunk, lalu `compress_task`. Kegagalan baca menjadi `TaskResult(ok=False)`, bukan kegagalan pool.
- `run_local(...)` memakai `Pool(procs).imap_unordered`, mencatat `busy` per PID, menulis chunk
  dan manifest yang identik dengan baseline sequential, lalu menyusun `metrics.json` (mode
  `local`, `procs`, waktu, throughput, `busy_sec` per proses, dan daftar error).
- CLI: `python -m pcomp.local_parallel --input ... --out ... --procs 4`. Cetakan akhir
  `LOCAL OK`.

## 3. Sisi Master

### 3.1 `master/server.py` (760 baris, inti sistem)

**`MasterState`** adalah logika Master tanpa socket:

| Metode | Perilaku |
|---|---|
| `register(session)` | Menolak `worker_id` yang masih aktif (`WorkerRejected` dengan `DUPLICATE_WORKER`); mencatat event `worker_registered` atau `worker_rejoined` |
| `touch(worker_id)` | Memperbarui `last_seen` setiap pesan diterima |
| `add_credits` / `take` | Menambah saldo credit; `take` hanya memberi task bila credit > 0, lalu mengurangi credit dan menambah `inflight` |
| `handle_result(session, header, payload)` | `claim_result` (idempotensi) → `is_valid_result` → `collector.write_chunk` → `mark_done`; bila gagal, requeue atau dead-letter, lalu mencatat `task_done`/`task_requeued`/`task_failed` |
| `drop_worker(worker_id, reason, now)` | Menandai Worker mati, menutup socket, mencatat `worker_dead`, meminta scheduler memindahkan jatah, lalu `requeue_from` |
| `abort(reason, now)` | Menandai seluruh task belum selesai sebagai `FAILED` |
| `begin()` | Mengaktifkan `started`, mencatat `start_time`, memanggil `scheduler.start` |

`is_valid_result(task, header, payload)` memeriksa `ok`, `sha256_in` sama dengan hash data yang
dikirim Master, `orig_size` sama dengan `task.length`, dan `comp_size` sama dengan panjang payload.

**`MasterServer`** mengurus socket dan siklus hidup:

1. `__init__` memuat `plan_tasks`, membuat `EventLog`, scheduler (`build_scheduler`), `Collector`,
   `MasterState`, `Monitor`, dan `SystemLog`/`SystemSampler`.
2. `run()` membuka listener (`SO_REUSEADDR`, backlog 16, timeout accept 0,2 detik), menjalankan
   monitor dan sampler, lalu:
   - menerima koneksi dan menjalankan `serve_connection` pada thread daemon;
   - menunggu barrier `expect_workers`; bila `barrier_timeout` habis tetapi ada Worker, run tetap
     dimulai dengan Worker yang ada;
   - mendispatch task ke semua sesi pada setiap putaran;
   - memantau kondisi semua Worker mati sebelum task selesai (setelah `heartbeat_timeout`,
     `abort` dan berhenti);
   - memanggil `finalize()` bila run sudah dimulai.
3. `serve_connection(sock)` hanya menerima `REGISTER` sebagai pesan pertama, membalas
   `REGISTER_ACK` (berisi `heartbeat_interval`, `algo`, `level`), lalu melayani `REQUEST`,
   `RESULT`, `HEARTBEAT` (dibalas `HEARTBEAT_ACK` dan dicatat ke `system.csv`), dan `BYE`.
   Setelah `SHUTDOWN` dikirim, handler tetap membaca sampai `BYE` agar frame terakhir tidak hilang.
4. `_dispatch(session)` mengambil task sesuai credit, membaca chunk, menghitung SHA-256, mengirim
   `TASK` beserta payload, dan mencatat `task_assigned`. Kegagalan kirim membuat Worker dianggap
   putus dan task di-requeue.
5. `_maybe_finish()` mengirim `SHUTDOWN` ke semua Worker sekali saja setelah semua task selesai.
6. `finalize()` (idempoten) menulis manifest (termasuk dead-letter), `metrics.json`, dan event
   `run_finished`. Isi `metrics.json`: mode, algoritma, level, chunk, repeat, scheduler, jumlah
   Worker, `worker_stats` (task selesai/gagal, `busy_sec`), jumlah task, task ok/gagal/retry,
   total byte, `ratio`, `imbalance`, `time_s`, `throughput_mbs`, `simulated`, `started_at`.

Kode keluar Master `0` hanya bila tidak ada task `FAILED`, `PENDING`, atau `ASSIGNED`.

### 3.2 `master/scheduler.py`

- `Scheduler` (ABC): `start(table, worker_ids)`, `take(table, worker_id, now)`, ditambah hook
  `on_worker_dead(worker_id)` dan `on_requeue(task)`.
- `DynamicScheduler` (`name="dynamic"`): `take` memanggil `table.take_largest` (LPT). Tidak ada
  rencana awal; kapasitas tercermin dari credit yang diminta Worker.
- `StaticScheduler` (`name="static"`): `start` membagi `task_id` round-robin ke Worker yang hadir
  saat barrier. `take` mengambil dari antrean milik Worker, lalu dari `_orphans`. Saat Worker mati
  atau task di-requeue, id dipindahkan ke `_orphans` agar dapat diambil Worker hidup.
- `build_scheduler(name)` memetakan `"static"`/`"dynamic"`, selain itu `ValueError`.
- `imbalance_factor(busy) = max(busy) / mean(busy)`; `1.0` untuk data kosong atau rata-rata nol.

### 3.3 `master/monitor.py`

`Monitor(state, timeout, interval, clock=time.time, on_dead=None)` menjalankan thread daemon.
`sweep()` menandai Worker dengan `now - last_seen > timeout` sebagai mati lewat
`state.drop_worker(..., "heartbeat timeout", now)` dan mengembalikan daftar id. `_loop` memanggil
`sweep` setiap `interval`; pengecualian dicatat dengan `logger.exception` agar monitor tidak
mematikan Master. `MasterServer` memakai `interval = max(0.05, min(0.5, heartbeat_timeout / 2))`.

### 3.4 `master/collector.py`

`Collector(out_dir, algo, level, chunk_mb, repeat, total_tasks)`:

- `write_chunk(task, data, sha256, comp_size)` menentukan nama file (`chunk_output_name`),
  menulis byte chunk, dan menambahkan `ManifestEntry` di bawah lock.
- `manifest(failed)` mengurutkan entri berdasarkan `task_id` dan memanggil `build_manifest`.
- `write_manifest(failed)` menulis `manifest.json`; `write_metrics(metrics)` menulis
  `metrics.json` (indentasi 2).
- `_copy_of(task_id)` memakai `copy_index(task_id, total_tasks // repeat)`.

### 3.5 `master/cli.py`

`python -m pcomp.master` membaca `config/master.toml`, menimpa dengan opsi CLI, lalu menjalankan
`MasterServer`. Opsi: `--config`, `--host`, `--port`, `--input`, `--out`, `--algo`, `--level`,
`--chunk-mb`, `--repeat`, `--expect-workers`, `--scheduler`, `--heartbeat-interval`,
`--heartbeat-timeout`, `--max-attempts`, `--barrier-timeout`, `--group-config`, `--log-level`.
Cetakan akhir: blok metrik lalu `MASTER OK` atau `MASTER FAILED`.

## 4. Sisi Worker

### 4.1 `worker/client.py`

`WorkerClient(config, protocol_version, hostname, clock)` menjalankan satu Worker:

1. `parse_master_address("host:port")` memvalidasi alamat; `connect_with_retry` mencoba koneksi.
2. Mengirim `REGISTER` (`worker_id`, `hostname`, `cores=1`, `procs`, `version`) dan menunggu
   `REGISTER_ACK`. Penolakan dilaporkan lewat `_report_rejection` (membaca pesan `ERROR`).
3. Setelah diterima: `sock.settimeout(DEFAULT_HEARTBEAT_TIMEOUT)`, membuat `Executor(procs)`,
   `HeartbeatSender`, thread `sender`, lalu mengirim `REQUEST(credits=procs)`.
4. `_receive_loop` menangani `TASK` (membuat `Task` dari header, menyimpan di `_inflight`,
   `executor.submit`), `HEARTBEAT_ACK` (abaikan), `SHUTDOWN` (kembali `EXIT_OK`), dan `ERROR`.
5. `_sender_loop` mengirim `RESULT` beserta payload lalu `REQUEST(credits=1)` untuk setiap hasil;
   setelah itu `_after_result_sent` menghitung hasil dan memanggil `os._exit(1)` bila
   `--fail-after-tasks` tercapai.
6. Thread `fail-timer` memanggil `os._exit(1)` setelah `--fail-after-sec` bila run belum selesai.
7. `finally`: hentikan heartbeat, kirim `BYE`, tutup pool, tunggu thread sender, tutup socket.
   Timeout atau koneksi putus dicetak sebagai `WORKER: MASTER HILANG ...`.

`build_register_header` dan `build_result_header` menyusun header sesuai `PROTOCOL.md`.

### 4.2 `worker/executor.py`

- `run_task(task, data, algo, level, throttle, task_fail_rate=0.0, seed=0)` adalah fungsi
  top-level untuk pool. Bila `throttle > 0`, tidur dulu; bila `task_fail_rate > 0`, memakai
  `Random(seed * 1_000_003 + task.task_id)` agar kegagalan deterministik untuk test retry.
- `Executor(procs, on_result, throttle, task_fail_rate, seed, context=None)` membuat
  `multiprocessing.Pool` dengan `pool_context()` (spawn). `submit` memakai `apply_async` dengan
  callback `on_result`; `close()` memanggil `close()` lalu `join()`.

### 4.3 `worker/heartbeat.py`

`HeartbeatSender(send, interval, inflight, sampler=None, clock=time.time)` menjalankan thread
daemon yang mengirim header `HEARTBEAT` berisi `ts`, `cpu_percent`, `mem_percent`, `inflight`.
Bila `sampler` tidak diberikan, nilai CPU/memori dikirim `0.0` agar test deterministik.

### 4.4 `worker/cli.py`

`python -m pcomp.worker` membaca `config/worker.toml` dan menimpa dengan opsi CLI: `--config`,
`--master`, `--id`, `--procs`, `--throttle`, `--fail-after-tasks`, `--fail-after-sec`,
`--task-fail-rate`, `--seed`, `--protocol-version`, `--group-config`, `--log-level`.
Cetakan akhir `WORKER OK (<id>)` atau `WORKER FAILED (<id>)`.

## 5. Metrik

### 5.1 `metrics/events.py`

`EventLog(path, clock=time.time)` membuka file append dan menulis satu baris JSON per event
(`{"ts": ..., "event": ..., ...field}`) di bawah lock. Konteks `with EventLog(...)` menutup file
otomatis. `read_events(path)` membaca kembali JSONL menjadi daftar dict.

Event yang dipakai sistem: `worker_registered`, `worker_rejoined`, `run_started`, `task_assigned`,
`task_done`, `task_requeued`, `task_failed`, `worker_dead`, `worker_disconnected`, `run_finished`,
`late_or_duplicate`, `worker_exit_injected`.

### 5.2 `metrics/system.py`

- `Sample(ts, role, node, worker_id, cpu_percent, mem_percent, rss_mb)`; `as_row()` menjaga urutan
  kolom `SYSTEM_CSV_COLUMNS`.
- `ProcessSampler(pid=None)`: `usage()` mengembalikan `(cpu_percent, mem_percent)` proses sendiri;
  `snapshot()` menambahkan `rss_mb`. Panggilan `cpu_percent` pertama dipakai sebagai baseline.
- `SystemSampler(sink, role, node, worker_id, interval=1.0, sampler=None, clock)` mengambil sampel
  berkala lewat thread daemon; `sample_once()` menulis satu baris.
- `SystemLog(path)` menulis `system.csv` (header ditulis saat baris pertama) di bawah lock;
  `read_system_csv(path)` mengembalikan daftar `Sample`.
- `summarise_usage(samples)` menghitung rata-rata CPU/memori untuk peran `master`/`local` dan
  `worker` menjadi `UsageSummary`.

### 5.3 `metrics/calc.py`

Rumus sesuai `EXPERIMENTS.md` bagian 3:

| Fungsi | Rumus |
|---|---|
| `speedup(t_base, t_n)` | `S = t_base / t_n` (0 bila `t_n <= 0`) |
| `efficiency(speedup_value, n)` | `E = S / n` |
| `throughput_mbs(total_bytes, time_s)` | `(total_bytes / MiB) / time_s` |
| `imbalance_factor(busy)` | `max(busy) / mean(busy)`, 1,0 bila kosong |
| `detection_latency(events, kill_ts)` | timestamp `worker_dead` pertama setelah kill dikurangi `kill_ts` |
| `recovery_time(events, kill_ts, workers)` | timestamp `task_done` terakhir dari task yang di-requeue setelah kill dikurangi `kill_ts` |

`recovery_stats(events, worker_id=None)` merangkum satu siklus kegagalan menjadi `RecoveryStats`
(`worker_id`, `kill_ts`, `detect_s`, `recovery_s`, `retried_tasks`). Bila satu run
menghentikan beberapa Worker, `killed_workers` dan cakupan `scope` membuat seluruh Worker yang
diinjeksi ikut dihitung.

## 6. Harness benchmark

### 6.1 `bench/runner.py`

- `EXPERIMENTS = ("E1", ..., "E6")`; `RunSpec(exp, mode, workers, procs, scheduler, throttle,
  kill_workers)`.
- `plan_runs(exp, workers, procs, reps, scheduler, throttle, kill_workers)` menyusun matriks:
  E1 sequential; E2 local untuk setiap `procs`; E3 distributed 9 Worker; E4 static dan dynamic
  dengan `throttle`; E5 distributed dengan `kill_workers`; E6 distributed untuk setiap jumlah
  Worker.
- `results_root`, `summary_path`, `figures_dir` mengarahkan hasil algoritma `sim` ke
  `results/dev/` dan algoritma nyata ke `results/raw/`, `results/summary.csv`,
  `results/figures/`.
- `collect_env()` mengumpulkan CPU, arsitektur, OS, versi Python, jumlah core, RAM, dan hostname
  ke `env.json` per run.
- Mode `--local` menjalankan Master dan Worker sebagai subprocess di mesin ini; mode `--lan`
  menjalankan Master saja dan menunggu Worker yang dijalankan manual di node lain.
- Setiap run: siapkan dataset (`--input` atau sintetis), jalankan konfigurasi, verifikasi
  manifest (`_verify`), baca `metrics.json`, hitung metrik tambahan, lalu tambahkan satu baris ke
  `summary.csv` (kolom `SUMMARY_COLUMNS`).
- `pause_between_runs(seconds)` menyediakan jeda antar run (dipakai `--pause`).
- `main` mencetak `BENCH OK` setelah seluruh run dan (kecuali `--no-report`) membangun agregat dan
  grafik.

### 6.2 `bench/report.py`

- `aggregate(rows, keys)` mengelompokkan baris berdasarkan `GROUP_KEYS = ("exp", "workers",
  "procs", "scheduler", "kill_workers")` dan menghitung rata-rata serta simpangan baku kolom
  metrik.
- `write_aggregate_csv(path, rows)` menulis `summary_agg.csv`.
- Grafik: `plot_time_vs_workers`, `plot_speedup`, `plot_efficiency`, `plot_throughput`,
  `plot_cpu_mem`, `plot_worker_load`, `plot_recovery_timeline`; semuanya memakai backend
  `matplotlib.use("Agg")`. `plot_all(rows)` membangun seluruh grafik ke folder `figures/`.
- `plot_worker_load` membaca `worker_stats` dari beberapa `run_dir`; `plot_recovery_timeline`
  membaca event untuk menggambar urutan deteksi dan pemulihan.

## 7. Alat bantu (`tools/`)

| Modul | Fungsi utama | Perilaku |
|---|---|---|
| `make_dataset.py` | `build_dataset(out_dir, size_mb, seed, files)` | Membuat file bergaya `text`, `random`, `repeat`, `mixed` secara deterministik dan menulis `dataset.json` berisi seed, ukuran, dan SHA-256 tiap file |
| `download_corpus.py` | `build_plan`, `sha256_file`, `download` | Mengunduh satu URL http/https ke folder tujuan, menghitung SHA-256, mendukung `--dry-run` dan `--expected-sha256`; URL wajib berasal dari `ASSETS.md` |
| `verify.py` | `verify_run(manifest_path, out_dir=None)` | Membaca manifest lalu `verify_entries`; CLI mencetak `VERIFY OK` atau daftar chunk gagal |
| `inject_failure.py` | `inject(pid, worker_id, events_path, reason)` | Mencatat `worker_exit_injected` lalu mengirim `SIGTERM` ke PID Worker |
| `validate_results.py` | `validate_root(root, min_reps=3)` | Memeriksa `results/raw`: eksperimen E1-E6 ada, tiap run punya `spec.json`, `env.json`, `metrics.json`, `manifest.json` (dan `events.jsonl` untuk mode distributed), `verify.log` berisi `VERIFY OK`, algoritma bukan `sim`, jumlah ulangan minimal 3, dan `summary.csv` sinkron; mencetak `RESULTS VALID` |

## 8. Skrip (`scripts/`)

| Skrip | Peran | Perintah penting |
|---|---|---|
| `gate.py` | Verification Gate G1-G9 | `python scripts/gate.py`, `--quick` |
| `e2e_local.py` | 1 Master + N Worker lokal | `python scripts/e2e_local.py --workers 3`; `--compare` untuk static vs dynamic; opsi injeksi `--fail-after-tasks`, `--task-fail-rate` |
| `check_node.py` | Kesiapan node | `python scripts/check_node.py --master host:port`, `--ping-master`, `--json` |
| `launch_workers.py` | Perintah Worker dari `config/nodes.toml` | `--print`, `--ssh`, `--ssh --dry-run`, `--port`, `--procs`, `--dir` |
| `pack_source.py` | ZIP sumber | `--list`, `--out`, `--repo` |
| `run_experiments.py` | Orkestrasi E1-E6 dengan container | `--exps`, `--reps`, `--pause`, `--input`, `--algo`, `--level`, `--chunk-mb`, `--repeat`, `--workers`, `--procs`, `--throttle`, `--kill-workers`, `--kill-fraction`, `--out-root`, `--timeout`, `--keep-payload` |

`gate.py` menjalankan G1 lint/format, G2 mypy, G3 unit test dengan coverage minimal 80 %, G4
integration test, G5 regresi (G3+G4), G6 smoke fase dari `SMOKE_COMMANDS`, G7 integration test 3
kali untuk fase 4 ke atas, G8 sinkronisasi CHANGELOG/phase log/status PLAN, dan G9 kebersihan repo
(tidak ada `data/` atau `output/` terlacak, tidak ada file > 5 MB, tidak ada file liar).

## 9. Alur pemanggilan

### 9.1 Sequential

```
python -m pcomp.sequential
  -> banner.try_print_banner
  -> chunker.plan_tasks(input, chunk_mb, repeat)
  -> untuk tiap task: chunker.read_chunk -> compressor.compress_task
  -> manifest.chunk_output_name / make_entry / build_manifest / write_manifest
  -> metrics.json -> cetak SEQUENTIAL OK
```

### 9.2 Local parallel

```
python -m pcomp.local_parallel
  -> chunker.plan_tasks
  -> local_parallel.pool_context().Pool(procs).imap_unordered(run_task)
       -> run_task: chunker.read_chunk -> compressor.compress_task
  -> tulis chunk -> manifest -> metrics.json -> cetak LOCAL OK
```

### 9.3 Distributed (jalur utama)

```
Master (master/cli.py -> MasterServer.run)
  accept -> thread serve_connection
  REGISTER  -> MasterState.register -> REGISTER_ACK
  barrier   -> MasterServer.begin -> MasterState.begin -> Scheduler.start
  dispatch  -> MasterState.take -> read_chunk + sha256 -> TASK(payload)
Worker (worker/cli.py -> WorkerClient.run)
  TASK      -> Executor.submit -> worker/executor.run_task -> compressor.compress_task
  RESULT    -> MasterState.handle_result -> Collector.write_chunk -> TaskTable.mark_done
  REQUEST(1)-> MasterState.add_credits -> dispatch berikutnya
selesai     -> MasterServer._maybe_finish -> SHUTDOWN -> Worker BYE
finalisasi  -> MasterServer.finalize -> manifest.json + metrics.json + event run_finished
```

Kredit adalah mekanisme aliran balik: Worker meminta `procs` credit saat awal dan satu credit
setiap kali mengirim hasil. Master tidak pernah mengirim lebih banyak task daripada credit yang
tersedia, sehingga Worker lambat otomatis menerima lebih sedikit task (dynamic load balancing).

### 9.4 Kegagalan Worker

```
Monitor.sweep (tiap <= 0,5 detik)
  -> MasterState.drop_worker("heartbeat timeout")
     -> event worker_dead
     -> Scheduler.on_worker_dead
     -> TaskTable.requeue_from (attempts + 1)
        -> PENDING: event task_requeued -> didispatch ke Worker hidup
        -> attempts >= max_attempts: FAILED -> event task_failed -> dead-letter di manifest
```

Koneksi putus juga langsung dianggap mati (`drop_worker` di blok `finally` handler). Hasil
terlambat atau ganda dari Worker yang sudah mati diabaikan lewat `claim_result` dan dicatat
sebagai `late_or_duplicate`.

### 9.5 Benchmark

```
python -m pcomp.bench.runner --exp E3 --lan ...
  -> plan_runs -> untuk tiap RunSpec: _execute
       -> siapkan dataset -> jalankan Master/Worker -> verify manifest
       -> metrics.json + events.jsonl + system.csv + env.json
  -> append baris ke results/summary.csv
  -> (kecuali --no-report) aggregate + write_aggregate_csv + plot_all
  -> cetak BENCH OK
```

## 10. Berkas keluaran

| Berkas | Ditulis oleh | Isi |
|---|---|---|
| `manifest.json` | `manifest.write_manifest` | versi, algoritma, level, chunk, repeat, total byte, entri chunk (hash, offset, ukuran, nama hasil), daftar gagal |
| `metrics.json` | `sequential`, `local_parallel`, `Collector` | mode, waktu, throughput, jumlah task, rasio, `worker_stats`, metrik tambahan |
| `events.jsonl` | `metrics.events.EventLog` | satu JSON per kejadian, dipakai menghitung recovery |
| `system.csv` | `metrics.system.SystemLog` | kolom `ts, role, node, worker_id, cpu_percent, mem_percent, rss_mb` |
| `verify.log` | `tools.verify` / harness | keluaran verifikasi per run (`VERIFY OK`) |
| `results/summary.csv` | `bench.runner` | satu baris per run dengan kolom `SUMMARY_COLUMNS` |
| `results/summary_agg.csv` | `bench.report.write_aggregate_csv` | rata-rata dan simpangan baku per kelompok konfigurasi |
| `results/figures/*.png` | `bench.report.plot_all` | tujuh grafik hasil eksperimen |

## 11. Cara menjalankan setiap perintah

Semua perintah dijalankan dari akar repo. Bila paket belum dipasang dengan
`pip install -e ".[dev]"`, tambahkan `PYTHONPATH=src` di depan perintah Python (dipakai gate).

### 11.1 Persiapan

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev,analysis]"   # dev: test/lint, analysis: matplotlib
python -m pcomp --version            # mencetak "ZipHive 1.0.0"
python -m pcomp                      # mencetak banner dari config/group.toml
```

### 11.2 Baseline dan dataset

```bash
python -m pcomp.tools.make_dataset --out data/synth --size-mb 20 --seed 1 --files 4
python -m pcomp.sequential --input data/synth --out output/seq --algo lzma --level 6
python -m pcomp.tools.verify --manifest output/seq/manifest.json
python -m pcomp.local_parallel --input data/synth --out output/local --procs 4
python -m pcomp.tools.verify --manifest output/local/manifest.json
```

Keluaran yang diharapkan: `SEQUENTIAL OK`, `VERIFY OK`, `LOCAL OK`, `VERIFY OK`.

### 11.3 Master dan Worker (dua terminal)

```bash
# Terminal 1 (Master)
python -m pcomp.master --input data/synth --out output/run1 \
  --expect-workers 2 --scheduler dynamic --heartbeat-interval 2 --heartbeat-timeout 6

# Terminal 2 dan 3 (Worker, worker_id harus unik)
python -m pcomp.worker --master 127.0.0.1:5050 --id w1 --procs 2
python -m pcomp.worker --master 127.0.0.1:5050 --id w2 --procs 2
```

Master mulai memproses setelah jumlah Worker mencapai `expect_workers` atau `--barrier-timeout`
habis. Ketika semua task selesai, Master mengirim `SHUTDOWN`, mencetak blok metrik dan
`MASTER OK`; Worker mencetak `WORKER OK (w1)`. Verifikasi dengan
`python -m pcomp.tools.verify --manifest output/run1/manifest.json`.

### 11.4 End-to-end lokal

```bash
python scripts/e2e_local.py --workers 3
python scripts/e2e_local.py --workers 2 --compare --algo gzip --size-mb 4 --chunk-mb 1 \
  --repeat 2 --worker-procs 1 --slow-throttle 0.4
python scripts/e2e_local.py --workers 2 --algo gzip --size-mb 4 --chunk-mb 1 --repeat 2 \
  --worker-procs 1 --fail-after-tasks 3 --heartbeat-interval 0.2 --heartbeat-timeout 1.0
```

Keluaran: `E2E OK` untuk satu skenario, `LB COMPARE OK` untuk `--compare`.

### 11.5 Benchmark

```bash
python -m pcomp.bench.runner --exp E6 --local --workers 1,2 --reps 2 --algo sim
python -m pcomp.bench.runner --exp E1 --local --input data/bench --reps 3
python -m pcomp.bench.runner --exp E3 --lan --host 0.0.0.0 --port 5050 --workers 9
```

Hasil algoritma `sim` masuk `results/dev/`; algoritma nyata masuk `results/raw/`,
`results/summary.csv`, dan `results/figures/`. Mode `--lan` hanya menjalankan Master; Worker
dijalankan manual di node lain.

### 11.6 Alat verifikasi dan validasi

```bash
python -m pcomp.tools.verify --manifest output/run1/manifest.json
python -m pcomp.tools.validate_results results/raw
python -m pcomp.tools.inject_failure --events output/run1/events.jsonl --pid 12345 \
  --worker-id w1 --reason manual
python -m pcomp.tools.download_corpus --url <URL_RESMI> --out data/silesia --dry-run
```

`validate_results` mencetak jumlah run per eksperimen dan `RESULTS VALID` bila seluruh syarat
terpenuhi.

### 11.7 Node dan paket

```bash
python scripts/check_node.py                       # periksa Python, psutil, protokol, core, RAM
python scripts/check_node.py --master 10.0.0.1:5050 --ping-master
python scripts/launch_workers.py --print           # cetak perintah Worker dari nodes.toml
python scripts/launch_workers.py --ssh             # jalankan lewat ssh (butuh nodes.toml terisi)
python scripts/pack_source.py --list               # daftar berkas yang akan dipaketkan
python scripts/pack_source.py                      # buat dist/ziphive-source-1.0.0.zip
```

`launch_workers.py` menolak placeholder di `config/nodes.toml`. `check_node.py` tidak mengirim
pesan protokol; Master akan mencatat `koneksi Worker berakhir` bila `--master` dipakai untuk uji
port.

### 11.8 Eksperimen 10 node virtual

Prasyarat: image `ziphive-node:min` sudah ada, dataset di `data/bench` (atau biarkan skrip
membuatnya), dan container Worker tidak sedang berjalan.

```bash
python scripts/run_experiments.py --exps E1,E2,E3,E4,E5,E6 --reps 3 --pause 30
```

Skrip menjalankan Master di host, menyalakan 9 container Worker per run, mematikan Worker pada E5
sesuai `--kill-workers` (default `1,3`) setelah sekitar 50 % task selesai, menyimpan log tiap
container, menjalankan `verify.py`, lalu menghapus payload `chunks/` (kecuali `--keep-payload`).
Prosedur tangkapan layar bukti ada di `docs/evidence/RUNBOOK.md`.

### 11.9 Test dan gate

```bash
python -m pytest -m "not integration and not perf and not slow"   # unit test
python -m pytest -m integration                                    # integration test
python -m pytest -m slow                                           # 9 Worker lokal
python -m pytest tests/unit/test_tasks.py -q                       # satu berkas
python scripts/gate.py --quick                                     # G1 + G3
python scripts/gate.py                                             # G1-G9 (wajib sebelum commit)
```

Bila paket belum terpasang, gate tetap dapat dijalankan dengan
`PYTHONPATH=src python scripts/gate.py`. Gate menulis ringkasan ke `reports/gate-latest.txt`.

## 12. Peta test

| Lokasi | Cakupan |
|---|---|
| `tests/unit/test_protocol.py`, `test_net.py` | frame, validasi header, pembacaan terpotong, retry koneksi |
| `tests/unit/test_config.py`, `test_banner.py`, `test_cli.py` | pemuatan TOML, override, banner, entry point |
| `tests/unit/test_tasks.py`, `test_task_table.py`, `test_chunker.py` | state machine dan pemecahan chunk |
| `tests/unit/test_compressor.py`, `test_manifest.py`, `test_sequential.py`, `test_local_parallel.py` | kompresi, manifest, baseline |
| `tests/unit/test_master_server.py`, `test_scheduler.py`, `test_monitor.py`, `test_collector.py`, `test_master_cli.py` | logika Master, credit, LPT, static, requeue, finalisasi |
| `tests/unit/test_events.py`, `test_system.py`, `test_calc.py` | event log, sampler, rumus metrik dan recovery |
| `tests/unit/test_bench.py`, `test_report.py` | perencanaan run, agregasi, grafik |
| `tests/unit/test_tools.py`, `test_validate_results.py`, `test_inject_failure.py` | alat bantu dan validator hasil |
| `tests/unit/test_gate.py`, `test_check_node.py`, `test_launch_workers.py`, `test_pack_source.py` | skrip utilitas |
| `tests/integration/test_echo.py` | server echo, payload besar |
| `tests/integration/test_master_worker.py`, `test_load_balancing.py`, `test_fault_tolerance.py` | Master-Worker nyata, load balancing, worker mati dan requeue |
| `tests/integration/test_sequential_cli.py`, `test_local_parallel_cli.py`, `test_cli_smoke.py`, `test_bench_cli.py` | CLI nyata dan harness |
| `tests/integration/test_slow_9_workers.py` | 9 Worker lokal (marker `slow`) |

Fixture di `tests/conftest.py`: `repo_root`, `load_script` (memuat skrip `scripts/` sebagai
modul), `valid_group_file`, `placeholder_group_file`, `free_port`, `synth_dataset`,
`module_runner`, `start_master`, `start_worker`, `events_of`.

## 13. Batas yang perlu diketahui

- Hasil algoritma `sim` hanya untuk test dan tidak pernah masuk `results/raw/` atau laporan
  (`is_simulated` dan `validate_results` menjaga aturan ini).
- Payload chunk hasil eksperimen resmi dihapus setelah `VERIFY OK`; verifikasi ulang memerlukan
  run baru. Bukti yang tersimpan adalah `manifest.json`, `verify.log`, dan `summary.csv`.
- `cpu_avg_workers` pada `results/summary.csv` tidak dapat dipakai karena sampler membaca proses
  induk Worker, sedangkan kompresi berjalan di proses anak `multiprocessing.Pool`. Analisis beban
  memakai `busy_sec` per Worker.
- Pelaksanaan 10 node memakai node virtual (ADR-015), bukan 10 perangkat fisik. Deviasi ini wajib
  diungkap di laporan dan video.
