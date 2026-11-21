# PHASE-05 — Dynamic load balancing

- Branch: phase/05-load-balancing
- Mulai / selesai: 2026-11-21 / 2026-11-21
- Status: DONE

## 1. Tujuan
Pengujian (d), perbandingan sebelum dan sesudah mekanisme (PLAN.md Fase 5). Lingkup hanya P5-T1
sampai P5-T5: antarmuka `Scheduler`, `StaticScheduler` (partisi round-robin di awal),
`DynamicScheduler` (LPT berbasis credit), opsi `--scheduler static|dynamic` dan `--throttle` pada
Worker, serta metrik waktu sibuk per Worker, jumlah task per Worker, dan imbalance factor. Monitor
heartbeat, requeue, retry (Fase 6), dan sampler psutil (Fase 7) belum termasuk fase ini.

## 2. Ringkasan hasil
Master kini memilih task melalui antarmuka `Scheduler`. `DynamicScheduler` mengambil task terbesar
lebih dulu setiap kali Worker meminta credit, sedangkan `StaticScheduler` membagi task round-robin
sekali saat barrier lalu tidak menyeimbangkan lagi. Worker mendapat opsi `--throttle` untuk meniru
mesin lambat, dan `metrics.json` mencatat scheduler yang dipakai, waktu sibuk serta jumlah task per
Worker, dan imbalance factor. Pada uji localhost dengan satu Worker lambat, dynamic menyelesaikan
10 task dalam 1,218594 detik dengan imbalance 1,628296, sedangkan static memerlukan 2,849092 detik
dengan imbalance 1,933789. Seluruh hasil tetap `VERIFY OK`.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P5-T1 | Antarmuka `Scheduler` di `master/scheduler.py` | DONE | `Scheduler` ABC, `build_scheduler`, `imbalance_factor` |
| P5-T2 | `StaticScheduler` partisi round-robin | DONE | Partisi memakai urutan `task_id` saat barrier |
| P5-T3 | `DynamicScheduler` LPT berbasis credit | DONE | `TaskTable.take_largest`, seri diputus `task_id` terkecil |
| P5-T4 | Opsi `--scheduler static|dynamic` dan Worker `--throttle` | DONE | Throttle berjalan di dalam proses pool |
| P5-T5 | Metrik waktu sibuk, jumlah task per Worker, imbalance factor | DONE | `worker_stats` dan `imbalance` pada `metrics.json` |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/master/scheduler.py` | add | Antarmuka scheduler, static/dynamic, imbalance factor |
| `src/pcomp/master/server.py` | mod | Dispatch memakai scheduler, metrik `scheduler` dan `imbalance` |
| `src/pcomp/tasks.py` | mod | `take_largest` (LPT) dan `take_task` (jatah static) |
| `src/pcomp/worker/executor.py` | mod | `throttle` per task dan `compute_sec` mencakup jeda |
| `src/pcomp/worker/client.py` | mod | Meneruskan `throttle` konfigurasi ke `Executor` |
| `src/pcomp/worker/cli.py` | mod | Opsi `--throttle` |
| `src/pcomp/master/cli.py` | mod | `--scheduler static` diterima |
| `src/pcomp/config.py` | mod | Validasi `throttle` tidak negatif |
| `config/worker.toml` | mod | Default `throttle = 0.0` |
| `scripts/e2e_local.py` | mod | Opsi `--scheduler`, `--throttle`, `--repeat`, mode `--compare` |
| `scripts/gate.py` | mod | Smoke Fase 5 dan penanda `LB COMPARE OK` |
| `tests/unit/test_scheduler.py` | add | UT-SCH-01..06 |
| `tests/unit/test_worker.py` | mod | UT-WRK-11 throttle |
| `tests/unit/test_master_cli.py` | mod | UT-MCLI-02 menguji penerusan scheduler static |
| `tests/unit/test_config.py` | mod | Default throttle menjadi 0.0 |
| `tests/integration/test_load_balancing.py` | add | IT-LB-01..02 |
| `TESTING.md` | mod | Perbarui UT-SCH, UT-WRK-11, UT-MCLI, IT-LB |
| `DECISIONS.md` | mod | ADR-008 scheduler, ADR-009 throttle |
| `CHANGELOG.md` | mod | Entri `0.05.0` |
| `PLAN.md` | mod | Status fase 5 DONE, `CURRENT PHASE: 6` |
| `pyproject.toml` | mod | Versi `0.05.0` |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 7 | 167 | UT-SCH-01..06 dan UT-WRK-11 |
| Integration | 2 | 11 | IT-LB-01..02 memakai `sim`, satu Worker `--throttle 0.5` |

Coverage: 83.07% pada gate penuh terakhir, dengan rentang 82.96%-83.07% pada run berulang (ambang
80%). Nilai bergeser sedikit karena sebagian baris bergantung waktu; sebelum fase ini 82.53% pada
160 unit test.

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=87 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 33 source files` |
| G3 Unit+cov | PASS | `Total coverage: 83.07% | 167 passed, 11 deselected in 37.15s` |
| G4 Integration | PASS | `11 passed, 167 deselected in 31.70s` |
| G5 Regresi | PASS | Seluruh test fase lama ikut dijalankan pada G3 dan G4 |
| G6 Smoke | PASS | `scripts/e2e_local.py --compare ... -> rc=0: LB COMPARE OK` |
| G7 Flaky x3 | PASS | `3 kali lulus` |
| G8 Dokumen | PASS | `CHANGELOG, phase log, dan status PLAN sinkron` |
| G9 Repo | PASS | `93 file terlacak, tidak ada pelanggaran` |

Smoke manual yang dikutip:
```
scheduler  time_s   imbalance  tasks_per_worker
static     2.849092 1.933789   w1=5,w2=5
dynamic    1.218594 1.628296   w1=9,w2=1
LB COMPARE OK
```

## 7. Deviasi dari rencana
1. `StaticScheduler` memakai partisi round-robin berdasarkan urutan `task_id` saat barrier. Worker
   yang mendaftar setelah barrier tidak mendapat jatah karena partisi tidak dihitung ulang. Alasan
   dan konsekuensinya dicatat pada ADR-008.
2. `imbalance` dihitung di `master/server.py` karena `metrics/calc.py` baru dibuat pada Fase 7.
   Fungsi `imbalance_factor` diletakkan di `master/scheduler.py` agar dapat dipakai ulang.
3. `scripts/e2e_local.py` diperluas (bukan skrip baru) dengan mode `--compare`, mengikuti struktur
   repo pada AGENTS.md bagian 5.
4. `config/worker.toml` default `throttle` diubah dari 1.0 menjadi 0.0 dan validasi diubah dari
   `> 0` menjadi `>= 0`. Tanpa perubahan ini, Worker normal selalu tidur satu detik per task dan
   tidak ada cara mematikan throttle. Perubahan ini menggantikan nilai default Fase 0.
5. UT-MCLI-02 yang sebelumnya menguji penolakan `--scheduler static` ditulis ulang menjadi pengujian
   penerusan opsi tersebut ke `MasterServer`, sesuai perilaku baru P5-T4. Assertion tidak dilemahkan;
   perilaku yang diuji memang berubah.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| IT-LB mengharapkan 8 task tetapi mendapat 10 | `build_dataset` menulis `dataset.json` sehingga ada 5 file, bukan 4 | `EXPECTED_TASKS` disesuaikan menjadi 10 (5 file x 2 repeat) |
| `--scheduler static` tidak bisa dipakai | CLI Master masih menolak static dengan pesan Fase 4 | Penolakan dihapus, scheduler dipilih di `MasterServer` |
| Worker normal tidur 1 detik per task | `worker.toml` bernilai `throttle = 1.0` dan validasi mewajibkan `> 0` | Default menjadi 0.0 dan validasi `>= 0` |
| `compute_sec` tidak mencerminkan Worker lambat | Throttle di luar fungsi kompresi tidak terukur | `run_task` di executor mengukur ulang `compute_sec` termasuk jeda |
| Imbalance bisa membesar karena pembagian nol | Rata-rata `busy` nol membuat pembagian tidak terdefinisi | `imbalance_factor` mengembalikan 1.0 bila data kosong atau rata-rata nol |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
- Partisi static tidak pernah dihitung ulang. Bila Worker static mati atau lebih lambat, task pada
  jatahnya tidak dipindahkan; pemulihan baru tersedia pada Fase 6.
- Dynamic memakai LPT berdasarkan ukuran chunk, bukan estimasi waktu kompresi per jenis data.
- `--throttle` adalah jeda tidur per task, bukan pembatasan CPU atau I/O.
- `imbalance` memakai `compute_sec` yang dilaporkan Worker sendiri dan memasukkan seluruh Worker
  terdaftar, termasuk yang tidak pernah mendapat task (nilai 0).
- Static dan dynamic tetap memakai protokol credit yang sama; static hanya membatasi sumber task,
  bukan menghapus mekanisme credit.
- Belum ada eksperimen resmi E4; angka pada fase ini berasal dari uji `sim` dan smoke `gzip` serta
  tidak boleh dipakai di laporan.

## 11. Catatan serah-terima ke fase berikutnya
- `Scheduler.take` dipanggil di dalam lock `MasterState`; Fase 6 harus mengembalikan task ke
  `TaskTable` (state PENDING) tanpa memanggil scheduler dari dalam lock yang sama secara berbalik.
- `Task.assigned_at` dan `Task.attempts` sudah terisi sehingga monitor Fase 6 dapat memakai data itu
  untuk requeue dan batas percobaan.
- `StaticScheduler.take` mengambil `task_id` dari antreannya sebelum memanggil `take_task`. Bila
  `take_task` mengembalikan `None` (misalnya task sudah di-requeue), id tersebut hilang dari antrean
  static; perlu ditangani saat requeue diimplementasikan.
- `imbalance_factor` dapat dipindahkan atau diimpor oleh `metrics/calc.py` pada Fase 7.
- `--throttle` siap dipakai untuk eksperimen E4, tetapi harus 0 pada eksperimen resmi.

## 12. Commit
Hash: lihat `git log --oneline` (commit `feat(phase-05): add static and dynamic schedulers with load
metrics`, merge `--no-ff` ke `main`). Tag: phase-05-done
