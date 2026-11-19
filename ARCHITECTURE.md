# ARCHITECTURE.md

## 1. Gambaran
Master memecah dataset menjadi task (chunk). Tiap Worker menarik task sesuai kapasitasnya, mengompresi di beberapa proses, lalu mengirim hasil ke Master. Master memantau Worker, mengembalikan task Worker yang gagal ke antrean, dan memverifikasi hasil.

```
                  +---------------------------------+
  data/ ------->  |             MASTER              |  ----> output/<run_id>/
 (Silesia dll)    |  Chunker  TaskTable  Scheduler  |        chunks, manifest.json,
                  |  Monitor  Collector  EventLog   |        metrics.json, events.jsonl
                  +----+---------+---------+--------+
                       | TCP     | TCP     | TCP   (port 5050)
              +--------+--+  +---+-------+ +-+-----------+
              |  WORKER 1 |  |  WORKER 2 | |  WORKER 9   |
              | net loop  |  |    ...    | |     ...     |
              | Pool(p)   |  |           | |             |
              | heartbeat |  |           | |             |
              +-----------+  +-----------+ +-------------+
```
Topologi: star. 1 node Master, 9 node Worker, satu jaringan (kabel atau wireless). Worker tidak saling berkomunikasi.

## 2. Komponen Master
| Modul | Tanggung jawab |
|---|---|
| `server.py` | Accept koneksi, satu thread handler per Worker, registry Worker, start barrier `--expect-workers` |
| `scheduler.py` | `StaticScheduler` dan `DynamicScheduler` (memilih task berikutnya untuk Worker tertentu) |
| `tasks.py` (`TaskTable`) | Seluruh state task, dilindungi satu lock |
| `monitor.py` | Thread pemeriksa heartbeat, menandai Worker DEAD, requeue |
| `collector.py` | Menulis chunk hasil, manifest, metrics, deteksi selesai, SHUTDOWN |
| `metrics/events.py` | Log JSONL berstempel waktu dari jam Master |

## 3. Komponen Worker
| Modul | Tanggung jawab |
|---|---|
| `client.py` | Connect, REGISTER, loop terima TASK, kirim RESULT, atur credit |
| `executor.py` | `multiprocessing.Pool(procs)`, fungsi kompresi top-level (spawn-safe) |
| `heartbeat.py` | Thread kirim HEARTBEAT (CPU, memori, jumlah task berjalan) |

Thread di Worker: thread utama (baca socket), thread kirim (satu lock kirim, hasil dari callback Pool masuk antrean), thread heartbeat. Proses: `procs` proses pool (default `os.cpu_count()`).

## 4. Model task dan state machine
```
PENDING --assign--> ASSIGNED --result ok--> DONE
   ^                    |
   |                    +--worker dead / error (attempts < 3)--> PENDING (attempts + 1)
   |                    +--worker dead / error (attempts = 3)--> FAILED
   +---------------------------------------------------------------+
```
Field `Task`: `task_id`, `file`, `index`, `offset`, `length`, `state`, `attempts`, `assigned_to`, `assigned_at`, `sha256`, `comp_size`, `done_at`.
Aturan: hasil hanya diterima jika task `ASSIGNED` ke Worker pengirim. Hasil dari Worker DEAD atau hasil ganda diabaikan (idempotensi) dan dicatat sebagai event.

## 5. Task decomposition
1. Pindai folder dataset, urut deterministik (path).
2. Tiap file dipecah per `chunk_size` (default 4 MiB). Chunk terakhir boleh lebih kecil. File kosong dilewati.
3. `--repeat k` mengulang seluruh daftar k kali dengan `task_id` berbeda (penskalaan beban, diungkap di laporan).
4. Master membaca isi chunk saat dispatch (lazy), menghitung sha256, dan mengirim bersama TASK. Memori Master terbatas pada task yang sedang berjalan.

## 6. Dynamic load balancing
- Dynamic (utama): Worker mengirim `REQUEST{credits}`; Master menyimpan saldo credit per Worker dan mengirim satu TASK per credit selama ada task PENDING. Worker mengirim credit baru setiap satu task selesai. Antrean diurutkan terbesar dulu (LPT) agar task besar tidak tertinggal di akhir.
- Static (pembanding): saat start, task dibagi round-robin rata per jumlah ke semua Worker; tidak ada penyeimbangan.
- Metrik pembeda: makespan, waktu sibuk per Worker, imbalance factor = max(busy) / mean(busy).

## 7. Fault tolerance
| Kegagalan | Deteksi | Penanganan |
|---|---|---|
| Worker crash atau jaringan putus | EOF/error socket, atau tidak ada pesan lebih dari 6 detik | DEAD, task ASSIGNED kembali PENDING, attempts + 1 |
| Task error di Worker | RESULT `ok=false` | Retry sampai 3 kali, lalu FAILED (dead-letter) |
| Hasil rusak | sha256 masukan atau ukuran tidak cocok | Dianggap error task, retry |
| Hasil ganda atau terlambat | Task bukan ASSIGNED ke pengirim | Diabaikan, dicatat |
| Master hilang | Worker tidak menerima HEARTBEAT_ACK 6 detik | Worker berhenti rapi |
| Worker kembali | REGISTER dengan `worker_id` lama | Sesi baru, credit dihitung ulang |
Master tidak direplikasi (single point of failure), dicatat sebagai keterbatasan di laporan.

## 8. Alur data dan integritas
Master: baca chunk, hitung sha256, kirim TASK+payload. Worker: hitung sha256 data diterima (dikirim balik), kompresi, kirim RESULT+payload terkompresi. Master: bandingkan sha256, tulis `chunks/<file>.<index>.<ext>`, catat di manifest. Verifikasi akhir (`tools/verify.py`): dekompresi semua chunk, gabung, bandingkan sha256 file asli.

## 9. Pengukuran
Waktu mulai: saat task pertama dikirim (setelah barrier). Waktu selesai: saat hasil terakhir tertulis. Dipisahkan: waktu kompresi di Worker (`compute_sec`), perkiraan waktu transfer (waktu round-trip dikurangi compute). CPU dan memori dari psutil 1 Hz. Rumus lengkap di EXPERIMENTS.md.

## 10. Konfigurasi (TOML + CLI)
`master.toml`: host, port, input, out, algo, level, chunk_mb, repeat, scheduler, expect_workers, heartbeat_interval, heartbeat_timeout, max_attempts.
`worker.toml`: master, worker_id, procs, throttle, fail_after_tasks, fail_after_sec, task_fail_rate, seed.
`nodes.toml`: daftar node (nama, host, role, user, python).
CLI menimpa TOML.

## 11. Batasan yang diketahui
- Bandwidth keluar Master dapat menjadi bottleneck (R1 di PLAN.md).
- Master tunggal, tanpa checkpoint: bila Master mati, run diulang dari awal.
- Chunk independen mengurangi rasio kompresi dibanding file utuh.
- Satu Master melayani 9 Worker dengan thread, cukup untuk skala tugas ini.
