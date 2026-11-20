# PHASE-04 — Master–Worker inti

- Branch: phase/04-master-worker-core
- Mulai / selesai: 2026-11-20 / 2026-11-20
- Status: DONE

## 1. Tujuan
Pemrosesan terdistribusi dasar, pengujian (c), sesuai PLAN.md Fase 4. Lingkup hanya P4-T1 sampai P4-T6:
Master dengan accept loop, registry Worker, `TaskTable` ber-lock, dispatch FIFO berbasis credit,
barrier `--expect-workers`, collector yang menulis chunk/manifest/metrics/events, Worker dengan
`Pool` dan heartbeat, validasi hasil, serta `scripts/e2e_local.py`. Monitor heartbeat timeout,
requeue, retry, static scheduler, injeksi kegagalan, dan sampler psutil belum termasuk fase ini.

## 2. Ringkasan hasil
Master dan Worker berbasis TCP berjalan di localhost. Master membagi dataset menjadi task, melayani
satu thread per Worker, mengirim TASK sesuai saldo credit (FIFO), memvalidasi RESULT (sha256 masukan,
ukuran asli, ukuran payload), lalu menulis chunk, `manifest.json`, `metrics.json`, dan
`events.jsonl`. Worker mendaftar, mengirim heartbeat berkala, mengompresi di `multiprocessing.Pool`,
dan mengirim RESULT diikuti permintaan credit baru. Seluruh task selesai tepat sekali pada 2 dan 3
Worker, `tools/verify.py` mencetak `VERIFY OK`, dan smoke `E2E OK` lulus.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P4-T1 | `server.py`: accept loop, registry, `TaskTable`, dispatch FIFO, barrier | DONE | Logika bebas socket dipisah ke `MasterState` agar dapat diuji unit |
| P4-T2 | `collector.py`: chunk, manifest, metrics, events, deteksi selesai, SHUTDOWN | DONE | SHUTDOWN dikirim sekali, handler menunggu BYE |
| P4-T3 | `worker/client.py` dan `executor.py` | DONE | `Executor` memakai `multiprocessing.Pool` dengan konteks spawn |
| P4-T4 | `worker/heartbeat.py` | DONE | Interval dari `REGISTER_ACK`; CPU/memori masih 0.0 |
| P4-T5 | Validasi sha256 masukan, ukuran hasil, versi protokol | DONE | Versi beda: `REGISTER_ACK(accepted=false)` + `ERROR(VERSION_MISMATCH)` |
| P4-T6 | `scripts/e2e_local.py` | DONE | Port bebas, dataset sintetis, pencetakan `E2E OK` |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/master/__init__.py` | add | Paket Master |
| `src/pcomp/master/server.py` | add | Accept loop, registry, dispatch FIFO, validasi hasil, finalisasi |
| `src/pcomp/master/collector.py` | add | Penulisan chunk, manifest, metrics |
| `src/pcomp/master/cli.py` | add | Entry point Master dengan penimpaan CLI |
| `src/pcomp/master/__main__.py` | add | `python -m pcomp.master` |
| `src/pcomp/worker/__init__.py` | add | Paket Worker |
| `src/pcomp/worker/client.py` | add | REGISTER, terima TASK, kirim RESULT dan credit |
| `src/pcomp/worker/executor.py` | add | Pool proses untuk `compress_task` |
| `src/pcomp/worker/heartbeat.py` | add | Pengirim HEARTBEAT berkala |
| `src/pcomp/worker/cli.py` | add | Entry point Worker dengan penimpaan CLI |
| `src/pcomp/worker/__main__.py` | add | `python -m pcomp.worker` |
| `src/pcomp/tasks.py` | mod | Tambah `TaskTable` ber-lock |
| `src/pcomp/constants.py` | mod | `DEFAULT_BARRIER_TIMEOUT`, versi `0.04.0` |
| `scripts/e2e_local.py` | add | Smoke 1 Master + N Worker di localhost |
| `scripts/gate.py` | mod | Smoke Fase 4 dan penanda `E2E OK` |
| `tests/conftest.py` | mod | Fixture jaringan dan `module_runner` |
| `tests/unit/test_task_table.py` | add | UT-TBL-01..06 |
| `tests/unit/test_collector.py` | add | UT-COL-01..03 |
| `tests/unit/test_master_server.py` | add | UT-MST-01..06 |
| `tests/unit/test_worker.py` | add | UT-WRK-01..10 |
| `tests/unit/test_master_cli.py` | add | UT-MCLI-01..04 |
| `tests/unit/test_worker_cli.py` | add | UT-WCLI-01..03 |
| `tests/integration/test_master_worker.py` | add | IT-DIST-01..05 |
| `TESTING.md` | mod | Fixture dan baris matriks UT-COL, UT-MST, UT-WRK, UT-MCLI, UT-WCLI |
| `CHANGELOG.md` | mod | Entri `0.04.0` |
| `PLAN.md` | mod | Status fase 4 DONE, `CURRENT PHASE: 5` |
| `pyproject.toml` | mod | Versi `0.04.0` |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 42 | 160 | `pytest -m "not integration and not perf and not slow"` |
| Integration | 5 | 9 | `pytest -m integration`, seluruhnya di bawah 60 detik per test |

Coverage: 82.53% (gate G3, ambang 80%). Sebelum fase ini 81.43% pada 118 unit test.

ID test baru: UT-TBL-01..06, UT-COL-01..03, UT-MST-01..06, UT-WRK-01..10, UT-MCLI-01..04,
UT-WCLI-01..03, IT-DIST-01..05.

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=83 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 32 source files` |
| G3 Unit+cov | PASS | `Total coverage: 82.53% | 160 passed, 9 deselected in 34.83s` |
| G4 Integration | PASS | `9 passed, 160 deselected in 13.61s` |
| G5 Regresi | PASS | Seluruh test fase lama ikut dijalankan pada G3 dan G4 |
| G6 Smoke | PASS | `scripts/e2e_local.py --workers 3 -> rc=0: E2E OK` |
| G7 Flaky x3 | PASS | `3 kali lulus` |
| G8 Dokumen | PASS | `CHANGELOG, phase log, dan status PLAN sinkron` |
| G9 Repo | PASS | `75 file terlacak, tidak ada pelanggaran` |

Smoke manual yang dikutip:
```
workers      : 3
tasks        : 5
tasks_ok     : 5
tasks_failed : 0
total_mb     : 8.000777
ratio        : 2.629982
time_s       : 1.223123
VERIFY OK
E2E OK
```

## 7. Deviasi dari rencana
1. `MasterServer._finalize` dijadikan metode publik `finalize()` yang idempoten agar unit test dapat
   memanggil finalisasi setelah `SHUTDOWN` tanpa menjalankan accept loop sungguhan.
2. `MasterServer` tetap memindai folder input di konstruktor (gagal cepat). CLI Master menangkap
   `FileNotFoundError` dan mencetak `MASTER GAGAL`, bukan traceback. Unit test koneksi menyiapkan
   dataset kecil lewat helper `make_dataset` yang sudah ada di file test.
3. `build_register_header` mengisi field `v` dan `version` dengan nilai yang sama. Tanpa ini, hook
   `--protocol-version` tidak benar-benar menghasilkan penolakan versi karena `validate_message`
   memeriksa `v`, sedangkan PROTOCOL.md bagian 2 mencantumkan keduanya pada REGISTER.
4. Metrik `scheduler` ditulis sebagai `"fifo"` karena static scheduler baru ada pada Fase 5.
5. `--barrier-timeout` hanya argumen CLI, tidak ditambahkan ke `config/master.toml`, agar file
   konfigurasi tetap sesuai ARCHITECTURE.md bagian 10.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| 7 unit test merah `FileNotFoundError: folder input tidak ditemukan` | Test koneksi tidak menyiapkan dataset, sedangkan konstruktor memindai input | Test menyiapkan dataset kecil; CLI menangani input tidak ada dengan pesan galat |
| Worker kadang keluar dengan kode 1 pada IT-DIST | Master menutup socket tepat setelah `SHUTDOWN` sehingga `BYE` atau frame terakhir bisa hilang karena RST | Handler Master tetap membaca sampai `BYE` setelah `shutdown_sent`, baru menutup koneksi |
| IT-DIST-05 lulus padahal versi Worker berbeda | Hook `--protocol-version` hanya mengubah field `version`, bukan `v` yang diperiksa `validate_message` | `build_register_header` menyamakan `v` dan `version` |
| G3 turun ke 74.76% | Modul Master/Worker baru banyak baris socket yang belum tersentuh unit test | Tambah UT-MST, UT-COL, UT-WRK, UT-MCLI, UT-WCLI; coverage 82.53% |
| Master tidak mengirim `ERROR` untuk `REQUEST` dengan credit tidak valid | `validate_message` melempar `ProtocolError` dan handler hanya mencatat log | Handler mengirim `ERROR(BAD_FRAME)` lalu menutup koneksi |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
- Belum ada monitor heartbeat timeout dan requeue. Bila Worker mati saat memegang task, task tetap
  `ASSIGNED` dan run tidak pernah selesai sampai proses Master dihentikan (Fase 6).
- Belum ada retry dan `max_attempts`; task dengan hasil tidak valid langsung `FAILED` dan tidak
  diulang. Master keluar dengan kode galat bila ada task `FAILED`.
- Belum ada static scheduler; CLI menolak `--scheduler static` dengan pesan Fase 5.
- `HEARTBEAT` mengirim `cpu_percent` dan `mem_percent` bernilai 0.0 karena sampler psutil baru
  dijadwalkan pada Fase 7.
- Belum ada throttling dan injeksi kegagalan pada Worker (`throttle`, `fail_after_*`,
  `task_fail_rate`, `seed` masih dibaca dari konfigurasi tetapi belum dipakai).
- `--protocol-version` pada CLI Worker adalah hook pengujian penolakan versi, bukan fitur produksi.
- Metrik `busy_sec` Worker dihitung dari `compute_sec` yang dilaporkan Worker sendiri.
- Start barrier tetap mulai dengan Worker yang tersedia bila batas waktu habis; perilaku ini
  mengikuti PROTOCOL.md bagian 4 dan dicatat pada log sebagai `warning`.

## 11. Catatan serah-terima ke fase berikutnya
- Titik sambung scheduler: `MasterState.take()` memanggil `TaskTable.take_next()` (FIFO). Fase 5
  perlu mengganti bagian ini dengan antarmuka `Scheduler` tanpa mengubah protokol.
- `WorkerSession.assigned_at` dan `Task.attempts` sudah terisi sehingga monitor Fase 6 dapat
  memakai `last_seen` dan `assigned_at` tanpa perubahan skema.
- `Collector`, `EventLog`, dan `Metrics` sudah menerima data apa adanya; metrik tambahan fase
  berikutnya cukup ditambahkan pada `finalize()`.
- `tests/conftest.py` menyediakan `start_master`, `start_worker`, dan `module_runner` yang bersih
  dari proses yatim, siap dipakai IT-LB dan IT-FT.

## 12. Commit
Hash: lihat `git log --oneline` (commit `feat(phase-04): add master-worker distributed processing core`,
merge `--no-ff` ke `main`). Tag: phase-04-done
