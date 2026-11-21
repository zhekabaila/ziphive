# PHASE-06 — Fault tolerance

- Branch: phase/06-fault-tolerance
- Mulai / selesai: 2026-11-21 / 2026-11-21
- Status: DONE

## 1. Tujuan
Pengujian (e), pemulihan task saat Worker gagal (PLAN.md Fase 6). Lingkup hanya P6-T1 sampai
P6-T7: `monitor.py` dengan timeout heartbeat dan requeue, retry serta dead-letter setelah 3
percobaan, idempotensi hasil terlambat/ganda, Worker bergabung ulang, injeksi kegagalan
(`--fail-after-tasks`, `--fail-after-sec`, `--task-fail-rate`, `--seed`, `tools/inject_failure.py`),
deteksi Master hilang oleh Worker, dan event `worker_dead`, `task_requeued`, `task_failed`,
`worker_rejoined`, `late_or_duplicate`, `worker_exit_injected`. Sampler psutil, harness benchmark,
dan skrip deployment node belum termasuk fase ini.

## 2. Ringkasan hasil
Master kini memantau heartbeat tiap Worker lewat `Monitor`, menandai Worker yang tidak mengirim
pesan melebihi `heartbeat_timeout` sebagai DEAD, menutup koneksinya, dan mengembalikan task yang
sedang dipegangnya ke antrean. Task dicoba ulang paling banyak `max_attempts` kali (default 3);
setelah itu task menjadi FAILED, tercatat pada larik `failed` manifest, pada `failed_tasks` di
`metrics.json`, dan membuat exit code Master bukan nol. Hasil ganda atau terlambat dari Worker yang
sudah DEAD diabaikan. Worker dengan `worker_id` sama dapat bergabung ulang dan langsung menerima
task. Worker yang kehilangan Master keluar dengan kode galat dan pesan `WORKER: MASTER HILANG`.
Seluruh integration test fault tolerance lulus tiga kali berturut-turut pada G7.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P6-T1 | `monitor.py`: timeout heartbeat, Worker DEAD, requeue | DONE | `Monitor.sweep` memakai jam yang dapat diganti jam palsu |
| P6-T2 | Retry dan dead-letter setelah 3 percobaan | DONE | `TaskTable.requeue_task`, `failed` manifest, exit code bukan nol |
| P6-T3 | Idempotensi hasil terlambat dan ganda | DONE | Event `late_or_duplicate`, hasil tidak ditulis |
| P6-T4 | Worker bergabung ulang dengan `worker_id` sama | DONE | `MasterState.register` mengirim `worker_rejoined` |
| P6-T5 | Injeksi kegagalan Worker dan `tools/inject_failure.py` | DONE | Opsi CLI Worker dan skrip e2e ikut ditambah |
| P6-T6 | Worker mendeteksi Master hilang dan keluar bersih | DONE | Timeout dan koneksi terputus sama-sama ditangani |
| P6-T7 | Event wajib dengan timestamp untuk Recovery Time | DONE | Seluruh event memakai `ts` yang sama dengan `events.jsonl` |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/master/monitor.py` | add | Pemantau heartbeat dengan jam yang dapat diganti dan thread yang dapat dihentikan |
| `src/pcomp/master/server.py` | mod | Registry sesi dengan `last_seen`/`dead`, retry, dead-letter, requeue, abort, deteksi kekosongan Worker, agregasi `worker_stats` |
| `src/pcomp/master/scheduler.py` | mod | Hook `on_worker_dead` dan `on_requeue`; `StaticScheduler` memindahkan jatah Worker mati |
| `src/pcomp/master/collector.py` | mod | `write_manifest(failed=...)` untuk dead-letter |
| `src/pcomp/master/cli.py` | mod | Opsi `--heartbeat-interval`, `--heartbeat-timeout`, `--max-attempts` |
| `src/pcomp/tasks.py` | mod | `fail_reason`, `requeue_task`, `requeue_from`, `fail_unfinished`, `failed_tasks` |
| `src/pcomp/manifest.py` | mod | `FailedEntry` dan larik `failed` (aditif) |
| `src/pcomp/worker/client.py` | mod | Timeout heartbeat, deteksi Master hilang, `fail_after_tasks`, `fail_after_sec` |
| `src/pcomp/worker/executor.py` | mod | `task_fail_rate` deterministik dengan `seed` |
| `src/pcomp/worker/cli.py` | mod | Opsi injeksi kegagalan Worker |
| `src/pcomp/tools/inject_failure.py` | add | Catat `worker_exit_injected` lalu hentikan PID Worker |
| `src/pcomp/constants.py` | mod | Versi `0.06.0` |
| `scripts/e2e_local.py` | mod | Opsi injeksi kegagalan, heartbeat, `--max-attempts`, cek event `worker_dead` |
| `scripts/gate.py` | mod | Smoke Fase 6 dan keluaran yang diharapkan |
| `tests/unit/test_monitor.py` | add | UT-MON-01..03 |
| `tests/unit/test_task_table.py` | mod | UT-TBL-07..09 |
| `tests/unit/test_scheduler.py` | mod | UT-SCH-07..08 |
| `tests/unit/test_worker.py` | mod | UT-WRK-12..13 |
| `tests/unit/test_manifest.py` | mod | UT-MAN-04 dan UT-MAN-04b |
| `tests/unit/test_master_server.py` | mod | UT-MST-05 disesuaikan, UT-MST-07..10 |
| `tests/unit/test_master_cli.py` | mod | UT-MCLI-05 |
| `tests/unit/test_worker_cli.py` | mod | UT-WCLI-04 |
| `tests/unit/test_inject_failure.py` | add | UT-TOOL-03 |
| `tests/integration/test_fault_tolerance.py` | add | IT-FT-01..07 |
| `ARCHITECTURE.md` | mod | Bagian 4, 7, 8 disinkronkan dengan semantik attempts dan dead-letter |
| `TESTING.md` | mod | Matriks UT dan IT fase ini |
| `CHANGELOG.md`, `DECISIONS.md`, `PLAN.md`, `pyproject.toml` | mod | Catatan rilis, ADR-010/ADR-011, status fase, versi |
| `docs/phase-logs/PHASE-06.md` | add | Phase log ini |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 19 | 186 | UT-MON-01..03, UT-TBL-07..09, UT-SCH-07..08, UT-WRK-12..13, UT-MAN-04/04b, UT-TOOL-03, UT-WCLI-04, UT-MCLI-05, UT-MST-07..10 |
| Integration | 7 | 18 | IT-FT-01..07, dijalankan tiga kali pada G7 |

Coverage: 83.14% (G3, ambang 80%).

Bukti merah sebelum implementasi: `python -m pytest` gagal dengan
`ModuleNotFoundError: No module named 'pcomp.master.monitor'` dan
`ImportError: cannot import name 'FailedEntry' from 'pcomp.manifest'`.

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=93 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 35 source files` |
| G3 Unit+cov | PASS | `Total coverage: 83.14%` dengan `186 passed, 18 deselected in 39.50s` |
| G4 Integration | PASS | `18 passed, 186 deselected in 54.24s` |
| G5 Regresi | PASS | seluruh test fase lama ikut dijalankan G3 dan G4 |
| G6 Smoke | PASS | smoke `--fail-after-tasks 3` menghasilkan `E2E OK` dan event `worker_dead` |
| G7 Flaky x3 | PASS | `3 kali lulus` |
| G8 Dokumen | PASS | CHANGELOG, phase log, dan status PLAN sinkron |
| G9 Repo | PASS | `97 file terlacak, tidak ada pelanggaran` |

## 7. Deviasi dari rencana
1. ARCHITECTURE.md bagian 4 menyebut requeue menaikkan `attempts`, sedangkan implementasi sejak
   Fase 4 menaikkannya saat penugasan. Semantik implementasi dipertahankan (batas 3 percobaan
   menjadi jelas) dan dokumen diperbaiki; dicatat sebagai ADR-010.
2. Larik `failed` ditambahkan pada manifest sebagai field opsional tanpa menaikkan
   `MANIFEST_VERSION`; dicatat sebagai ADR-011.
3. `MasterState.register` memindahkan emisi event `worker_registered` dari `MasterServer` agar
   `worker_rejoined` dapat dibedakan pada satu tempat.
4. Abort saat semua Worker mati memakai tenggang satu `heartbeat_timeout` sebelum Master menyerah,
   supaya Worker yang sedang bergabung ulang tidak langsung dianggap hilang.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| IT-FT-07 gagal dengan `WinError 10054` | Master yang dihentikan memutus koneksi sehingga Worker menerima `ConnectionResetError`, bukan `TimeoutError` | Penanganan `ConnectionError` pada loop Worker mencetak `MASTER HILANG` dengan kode keluar galat |
| Lint `B027` pada `Scheduler` | Metode hook kosong pada kelas ABC | Badan metode diberi `return None` |
| Mypy `MasterState has no attribute requeue_task` | Requeue dipanggil pada state, bukan pada `TaskTable` | Panggilan diarahkan ke `self.state.table.requeue_task` |
| Worker mati saat Master sedang mengirim task | `send_msg` gagal di tengah dispatch | Task di-requeue lalu Worker dijatuhkan lewat `drop_worker` |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. Master tetap satu titik kegagalan; bila Master mati, run diulang dari awal (tidak ada
   checkpoint).
2. Deteksi Worker mati bergantung pada timeout heartbeat, sehingga pemulihan terlambat paling
   cepat satu `heartbeat_timeout`.
3. `task_fail_rate` adalah simulasi kegagalan task di dalam proses Worker, bukan kegagalan nyata
   akibat data rusak; dipakai hanya untuk menguji retry dan tidak dipakai pada eksperimen resmi.
4. Penghentian proses pada `tools/inject_failure.py` memakai `SIGTERM`; di Windows sinyal ini
   dipetakan ke penghentian proses, sehingga perilakunya berbeda dari Linux dan perlu dicatat pada
   laporan.
5. Statistik Worker yang mati tetap diagregasi berdasarkan `worker_id`, sehingga Worker yang
   bergabung ulang menambah `procs` maksimumnya, bukan sesi baru.

## 11. Catatan serah-terima ke fase berikutnya
- Event `worker_dead`, `task_requeued`, `task_failed`, `worker_rejoined`, dan `late_or_duplicate`
  sudah bertimestamp dan dapat dipakai menghitung detection latency serta Recovery Time pada
  EXPERIMENTS.md bagian 3.
- `metrics.json` distributed memuat `tasks_retried`, `failed_tasks`, dan `worker_stats` agregat;
  harness benchmark Fase 7 dapat membacanya langsung.
- Opsi `--heartbeat-interval`, `--heartbeat-timeout`, dan `--max-attempts` sudah tersedia di CLI
  Master; `--fail-after-tasks`, `--fail-after-sec`, `--task-fail-rate`, dan `--seed` tersedia di
  CLI Worker.
- Jangan memakai nilai `task_fail_rate` bukan nol atau `throttle` bukan nol pada eksperimen resmi.

## 12. Commit
Hash: `feat(phase-06): add heartbeat monitoring, requeue, retry, failure injection` (lihat `git log` pada branch `main`). Tag: `phase-06-done`.
