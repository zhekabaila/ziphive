# TESTING.md — Strategi Pengujian

## 1. Prinsip
- Test-first. Tidak ada commit tanpa gate lulus (SDLC.md bagian 4).
- Test tidak bergantung pada Silesia atau internet. Data uji dibuat di `tmp_path` oleh fixture.
- Integration test memakai port bebas (bind port 0), proses nyata (`subprocess`), timeout jelas.
- Test deterministik. Gunakan algoritma `sim` dan seed tetap untuk skenario waktu. Test yang gagal 1 dari 5 kali dianggap bug.
- Test yang gagal diperbaiki lewat kode. Mengubah test hanya bila test salah, alasannya dicatat di phase log.

## 2. Jenis dan marker
| Jenis | Marker | Cakupan | Masuk gate |
|---|---|---|---|
| Unit | (tanpa marker) | fungsi dan class terisolasi, tanpa jaringan nyata | G3 |
| Integration | `integration` | Master + Worker proses nyata di localhost | G4, G7 |
| Slow | `slow` | skenario 9 Worker lokal | dijalankan di fase 8 dan 10 |
| Perf | `perf` | perbandingan waktu, informatif saja | tidak |
| E2E | `scripts/e2e_local.py` | alur lengkap sampai verifikasi | G6 |

Coverage minimal 80% untuk `src/pcomp` (G3).

## 3. Fixture di `tests/conftest.py`
`synth_dataset` (folder kecil: teks, acak, berulang, ukuran bervariasi, total sekitar 5 MiB), `free_port`, `start_master`, `start_worker` (mengembalikan handle proses, dibersihkan otomatis), `module_runner`, `events_of(run_dir)`.

## 4. Matriks test per modul (ID dipakai di phase log)
| ID | Modul | Skenario |
|---|---|---|
| UT-BOOT-01..05 | bootstrap | import paket dan versi, banner group.toml valid, banner placeholder, CLI `--version`, parsing `scripts/gate.py` |
| IT-BOOT-01 | bootstrap | entry point `python -m pcomp --version` dijalankan sebagai subprocess |
| UT-PRO-01..06 | protocol | round-trip, payload kosong, frame terpotong, header oversize, JSON rusak, tipe tak dikenal |
| UT-NET-01..03 | net | baca tepat N byte, timeout, connect retry |
| UT-CFG-01..02 | config | muat TOML, override CLI |
| UT-EVT-01 | events | tulis dari banyak thread |
| UT-LOG-01 | logging | setup idempoten, tulis ke file, level berupa string |
| UT-TSK-01..02 | tasks | nilai default task dan himpunan state |
| UT-CHK-01..05 | chunker | file kecil, kelipatan pas, sisa, urutan deterministik, repeat |
| UT-CMP-01..03 | compressor | round-trip gzip, bz2, lzma |
| UT-MAN-01..04 | manifest | skema, rekonstruksi, deteksi rusak, larik `failed` dead-letter |
| UT-SEQ-01 | sequential | manifest dan metrics, penanda `sim`, repeat, input kosong |
| UT-LOC-01..05 | local_parallel | manifest sama dengan sequential, procs 1/2/4, konteks spawn, error task, busy per proses |
| UT-TOOL-01..03 | tools | dataset sintetis deterministik, rencana unduhan tanpa jaringan, injeksi kegagalan (`inject_failure`) |
| UT-TBL-01..09 | TaskTable | semua transisi, attempts, duplikat, requeue, batas attempts, `fail_unfinished` |
| UT-COL-01..03 | collector | tulis chunk, manifest dan verifikasi, metrics, folder repeat |
| UT-MST-01..10 | master/server | REGISTER wajib, versi beda, duplikat, siklus task, hasil tidak valid, tanpa Worker, retry, dead-letter, requeue saat Worker mati, hasil terlambat, abort |
| UT-WRK-01..04 | worker | alamat Master, header REGISTER/RESULT, executor pool, heartbeat |
| UT-WRK-05..13 | worker client | kirim tanpa koneksi, Master tidak terjangkau, penolakan REGISTER, loop terima, loop kirim, `fail_after_tasks`, Master hilang |
| UT-MCLI-01..05 | master/cli | default parser, `--scheduler static` diteruskan, konfigurasi tidak ada, input tidak ada, `--heartbeat-*` dan `--max-attempts` |
| UT-WCLI-01..04 | worker/cli | default parser, konfigurasi tidak ada, exit code mengikuti `WorkerClient.run`, opsi injeksi kegagalan |
| UT-SCH-01..08 | scheduler | LPT, partisi static, credit, kepemilikan static, imbalance, nama scheduler, orfan static, requeue |
| UT-MON-01..03 | monitor | timeout (jam palsu), requeue, batas attempts |
| UT-CAL-01..04 | calc | speedup, efficiency, imbalance, recovery |
| IT-ECHO-01 | net | payload 10 MiB |
| IT-SEQ-01 | sequential | make_dataset, sequential, verify = `VERIFY OK` |
| IT-LOC-01 | local_parallel | sequential vs local `--procs 2`, manifest ekuivalen, keduanya `VERIFY OK` |
| IT-DIST-01..05 | master-worker | 2 dan 3 Worker, procs 2, tanpa Worker, versi beda |
| IT-LB-01..02 | load balancing | static vs dynamic dengan Worker lambat (`sim`, margin toleransi) |
| IT-FT-01..07 | fault tolerance | Worker mati, dua mati, semua mati, task beracun, rejoin, event recovery, Master hilang |
| IT-BENCH-01 | bench | runner lokal menghasilkan summary dan grafik |
| SL-9W-01 | slow | 9 Worker lokal selesai dan `VERIFY OK` |

## 5. Kriteria lulus integration inti
Setiap run: semua task `DONE` (atau `FAILED` pada skenario beracun), `VERIFY OK`, tidak ada proses yatim (Worker dan Master berhenti), `events.jsonl` konsisten (setiap `task_assigned` punya akhir `task_done` atau `task_requeued`).

## 6. Bukti pengujian
Hasil gate disalin ke phase log. Daftar ID test yang ditambah dicatat per fase.
