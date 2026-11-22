# PROTOCOL.md — Protokol Master–Worker (PROTOCOL_VERSION = 2)

Transport: TCP, port default 5050. Satu koneksi per Worker, dua arah.

## 1. Frame
```
| 4 byte  | 8 byte        | N byte         | M byte        |
| N (!I)  | M (!Q)        | header JSON    | payload biner |
```
- Big-endian. N = panjang header (UTF-8 JSON), M = panjang payload (boleh 0).
- Batas: N maksimal 64 KiB, M maksimal 64 MiB. Melebihi batas: tutup koneksi.
- Header selalu memuat `type` (string) dan `v` (versi protokol). Field lain sesuai tabel.
- Penerima membaca tepat N dan M byte (loop sampai lengkap), dengan timeout socket.

## 2. Pesan
| Arah | type | Field header | Payload |
|---|---|---|---|
| W→M | `REGISTER` | `worker_id`, `hostname`, `cores`, `procs`, `version` | tidak |
| M→W | `REGISTER_ACK` | `accepted`, `reason`, `heartbeat_interval`, `algo`, `level` | tidak |
| W→M | `REQUEST` | `credits` (int > 0) | tidak |
| M→W | `TASK` | `task_id`, `file`, `index`, `algo`, `level`, `orig_size`, `sha256` | data chunk asli |
| W→M | `RESULT` | `task_id`, `ok`, `orig_size`, `comp_size`, `sha256_in`, `compute_sec`, `error` | data terkompresi (bila ok) |
| W→M | `HEARTBEAT` | `ts`, `cpu_percent`, `mem_percent`, `inflight` | tidak |
| M→W | `HEARTBEAT_ACK` | `ts` | tidak |
| M→W | `SHUTDOWN` | `reason` | tidak |
| W→M | `BYE` | `worker_id` | tidak |
| M→W | `ERROR` | `code`, `message` | tidak |
| M→W | `KILL` | `worker_id`, `reason` | tidak |

Kode error: `VERSION_MISMATCH`, `DUPLICATE_WORKER`, `SERVER_FULL`, `BAD_FRAME`,
`UNKNOWN_TYPE`, `INTERNAL`.

## 3. Aturan
1. Pesan pertama dari Worker wajib `REGISTER`. Selain itu: `ERROR(BAD_FRAME)` lalu tutup.
2. `v` berbeda: `REGISTER_ACK(accepted=false)` + `ERROR(VERSION_MISMATCH)`, tutup.
3. `worker_id` aktif yang sama: `DUPLICATE_WORKER`. `worker_id` yang sudah DEAD boleh mendaftar lagi.
4. Setelah ACK diterima, Worker mengirim `REQUEST{credits=procs}`. Setiap RESULT selesai, Worker mengirim `REQUEST{credits=1}`.
5. Master mengirim TASK hanya jika saldo credit Worker > 0, lalu mengurangi saldo.
6. HEARTBEAT dikirim tiap `heartbeat_interval` (default 2 s), tetap dikirim saat Worker sibuk. Pesan apa pun dari Worker memperbarui `last_seen`.
7. Worker DEAD bila `now - last_seen > heartbeat_timeout` (default 6 s) atau socket error.
8. Master mengirim `SHUTDOWN` saat semua task DONE atau FAILED. Worker membalas `BYE` dan keluar.
9. Penerima mengabaikan field tidak dikenal (kompatibel ke depan dalam versi yang sama). Perubahan format wajib menaikkan `PROTOCOL_VERSION`.
10. Worker di luar kuota run (`len(sesi aktif) >= --expect-workers`): `ERROR(SERVER_FULL)` lalu tutup, tanpa `REGISTER_ACK`. Aturan ini menjaga konfigurasi E6 dengan jumlah Worker lebih kecil tetap murni ketika laptop lain belum dimatikan.
11. `KILL` hanya dikirim Master untuk skenario E5 pada node fisik: Worker wajib langsung keluar tanpa `BYE` (setara SIGKILL) dan tanpa menyelesaikan task yang sedang berjalan. Master mencatat `worker_exit_injected` sebelum mengirim pesan, sehingga lama deteksi (`worker_dead - worker_exit_injected`) dan lama pemulihan diukur dengan jam Master saja.
12. `PROTOCOL_VERSION` naik ke 2 pada Fase 11 karena penambahan pesan `KILL` dan kode error `SERVER_FULL`. Node dengan versi berbeda ditolak saat `REGISTER` (`VERSION_MISMATCH`).

## 4. Timeout
| Nama | Default |
|---|---|
| connect Worker | 5 s per percobaan, 10 percobaan, backoff 0.5 s sampai 5 s |
| socket read | 30 s (heartbeat membuat koneksi tetap hidup) |
| heartbeat interval | 2 s |
| heartbeat timeout | 6 s |
| barrier `--expect-workers` | 120 s lalu mulai dengan Worker yang ada atau berhenti (opsi) |
