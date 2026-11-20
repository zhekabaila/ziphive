# PHASE-03 — Local parallel

- Branch: phase/03-local-parallel
- Mulai / selesai: 2026-11-20 / 2026-11-20
- Status: DONE

## 1. Tujuan
Baseline pengujian (b) dan dasar logika eksekusi Worker (PLAN.md Fase 3). Lingkup hanya P3-T1 sampai
P3-T3: `local_parallel.py` memakai `multiprocessing` satu mesin, metrik waktu/throughput/waktu sibuk
per proses, dan penanganan error task tanpa mematikan pool. Tidak ada socket, jaringan, Master,
Worker, atau scheduler pada fase ini.

## 2. Ringkasan hasil
`pcomp.local_parallel` menjalankan seluruh task pada `multiprocessing.Pool` dengan start method
`spawn` dan `imap_unordered`, lalu menulis `manifest.json` serta `metrics.json` yang identik dengan
baseline sequential pada run yang sama. Fungsi kerja `run_task` bersifat top-level dan seluruh
argumen serta hasilnya dapat dipickle. Logika kompresi satu task dipindahkan ke fungsi netral
`compress_task` di `compressor.py` agar Worker Fase 4 memakai implementasi yang sama. Kegagalan task
(termasuk gagal membaca chunk) dikembalikan sebagai `TaskResult` gagal, dicatat di
`metrics["errors"]`, dan pool tetap menyelesaikan task lain. Metrik mencatat waktu total,
throughput, rasio, jumlah task berhasil/gagal, dan waktu sibuk per proses (`busy_per_process`).
Test unit 118 dan integration 4 lulus, coverage 81,43%.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P3-T1 | `local_parallel.py` CLI: `Pool(p)`, `imap_unordered`, fungsi kerja top-level | DONE | Start method `spawn`, manifest diurutkan ulang per `task_id` |
| P3-T2 | Metrik: waktu, throughput, waktu sibuk per proses | DONE | `busy_per_process` memakai pid proses pool |
| P3-T3 | Penanganan error task (dicatat, tidak mematikan pool) | DONE | Gagal baca dan gagal kompres sama-sama dicatat |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/local_parallel.py` | add | P3-T1..T3: pool spawn, metrik, penanganan error |
| `src/pcomp/compressor.py` | mod | `TaskResult` dan `compress_task` netral untuk dipakai ulang Worker Fase 4 |
| `src/pcomp/manifest.py` | mod | Helper `make_entry` agar sequential dan local membangun entri dengan cara sama |
| `src/pcomp/sequential.py` | mod | Memakai `make_entry` (perilaku tidak berubah) |
| `src/pcomp/constants.py` | mod | `DEFAULT_PROCS = 4` (sama dengan `config/worker.toml`), versi `0.03.0` |
| `pyproject.toml` | mod | Versi `0.03.0` |
| `scripts/gate.py` | mod | `SMOKE_COMMANDS[3]`, `SMOKE_EXPECTED[3] = ["SEQUENTIAL OK", "LOCAL OK"]` |
| `TESTING.md` | mod | Baris UT-LOC-01..05 dan IT-LOC-01 |
| `CHANGELOG.md` | mod | Entri `0.03.0` |
| `PLAN.md` | mod | Status fase 3 `DONE`, `CURRENT PHASE: 4` |
| `docs/phase-logs/PHASE-03.md` | add | Phase log fase ini |
| `tests/unit/test_local_parallel.py` | add | UT-LOC-01..05 |
| `tests/integration/test_local_parallel_cli.py` | add | IT-LOC-01 |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 10 | 118 | UT-LOC-01 manifest sama dengan sequential, UT-LOC-02 procs 1/2/4, UT-LOC-03 konteks spawn dan pickle, UT-LOC-04 error task, UT-LOC-05 busy per proses, plus input kosong |
| Integration | 1 | 4 | IT-LOC-01: sequential vs local `--procs 2`, manifest ekuivalen, keduanya `VERIFY OK` |

Coverage: 81,43% (`--cov=src/pcomp --cov-fail-under=80`).

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=65 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 23 source files` |
| G3 Unit+cov | PASS | `Total coverage: 81.43% | 118 passed, 4 deselected` |
| G4 Integration | PASS | `4 passed, 118 deselected` |
| G5 Regresi | PASS | `seluruh test fase lama ikut dijalankan oleh G3 dan G4` |
| G6 Smoke | PASS | `make_dataset -> DATASET OK; sequential -> SEQUENTIAL OK; verify -> VERIFY OK; local_parallel --procs 4 -> LOCAL OK; verify -> VERIFY OK` |
| G7 Flaky x3 | SKIP | `dilewati: berlaku fase 4 ke atas (SDLC.md G7)` |
| G8 Dokumen | PASS | CHANGELOG `0.03.0`, PHASE-03 terisi, status PLAN `DONE` |
| G9 Repo | PASS | `71 file terlacak, tidak ada pelanggaran` |

Keluaran lengkap: `reports/gate-latest.txt` (tidak di-commit karena `reports/` di-ignore).

Smoke manual pada `data/synth` (20 MiB, 9 task, algo default `lzma` level 6, chunk 4 MiB):

- sequential: `time_s: 3.17471`, `throughput: 6.300033 MB/s`, `SEQUENTIAL OK`, `chunks: 9`, `VERIFY OK`;
- local `--procs 4`: `time_s: 2.176157`, `throughput: 9.190872 MB/s`, `LOCAL OK`, `chunks: 9`,
  `VERIFY OK`;
- rasio kedua run sama: `2.630871`.

Angka di atas hanya bukti smoke, bukan hasil eksperimen resmi.

## 7. Deviasi dari rencana
1. Lokasi `compress_task`: diletakkan di `compressor.py`, bukan di `worker/executor.py`, karena
   modul `compressor` netral dan tidak bergantung pada jaringan. Worker Fase 4 tinggal memanggilnya.
   Ini sesuai instruksi khusus fase.
2. `run_local` menerima parameter opsional `tasks` agar test dapat menyisipkan task yang sengaja
   rusak (P3-T3). Pemakaian normal tetap `plan_tasks`.
3. Penanda kelulusan CLI `LOCAL OK` dan `LOCAL FAILED` ditambahkan karena PLAN.md hanya menyebut
   `VERIFY OK` pada smoke. G6 memeriksa `SEQUENTIAL OK`, `LOCAL OK`, dan rc semua perintah.
4. `read_chunk` yang gagal dibungkus menjadi `TaskResult` gagal di `run_task`. Tanpa ini, exception
   dari proses pool membatalkan `imap_unordered` sehingga pool ikut berhenti.
5. `DEFAULT_PROCS = 4` di `constants.py` mengikuti nilai `config/worker.toml`; PLAN.md tidak
   menetapkan default jumlah proses untuk baseline local.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| Test error task gagal dengan `FileNotFoundError` bocor | `read_chunk` melempar exception sebelum `compress_task` sempat menangkapnya | `run_task` menangkap `OSError` dan mengembalikan `TaskResult` gagal |
| `F821 ManifestEntry` setelah refactor | Anotasi `list[ManifestEntry]` masih dipakai di `sequential.py` | Import `ManifestEntry` dikembalikan |
| mypy: `get_context` bertipe `BaseContext` | Anotasi balik `SpawnContext` lebih sempit dari typeshed | `typing.cast(SpawnContext, ...)` |
| G8 gagal pada run pertama | CHANGELOG dan phase log belum diisi | Dokumentasi fase dilengkapi lalu gate penuh diulang |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. Pool hanya memakai start method `spawn`; tidak ada opsi `fork` karena AGENTS.md aturan 8
   mengutamakan keseragaman lintas platform. Akibatnya ada overhead start proses pada run pendek.
2. Pool dibuat ulang setiap kali `run_local` dipanggil; Worker Fase 4 perlu mempertahankan pool
   selama sesi agar overhead ini tidak berulang per task.
3. Hasil kompresi dikumpulkan di proses induk sebelum ditulis, sehingga memori induk menampung
   seluruh chunk terkompresi satu run (bukan streaming).
4. `busy_per_process` memakai pid proses, sehingga kunci berbeda antar run dan tidak dapat
   dibandingkan langsung; agregasi per Worker baru ada di Fase 7.
5. Metrik sistem (CPU, memori proses) belum ada pada fase ini; dijadwalkan di Fase 7.
6. Task yang gagal tidak masuk manifest dan tidak dikembalikan ke antrean; retry adalah lingkup
   Fase 6 (dead-letter) dan Fase 4 (requeue).
7. Jumlah task pada dataset kecil lebih sedikit dari jumlah proses, sehingga speedup smoke tidak
   proporsional terhadap `--procs`.
8. G7 (cek flaky 3 kali) belum berlaku sampai Fase 4.

## 11. Catatan serah-terima ke fase berikutnya
1. Worker Fase 4 wajib memakai `pcomp.compressor.compress_task(task, data, algo, level)`; jangan
   menulis ulang logika kompresi atau penanganan error.
2. `TaskResult` membawa `sha256` data asli dan `comp_size`, sehingga Master dapat memvalidasi hasil
   (P4-T5) tanpa menghitung ulang hash masukan.
3. `manifest.make_entry` adalah satu-satunya cara membangun entri manifest; dipakai sequential,
   local, dan nanti collector Master, agar skema tetap identik.
4. `run_local` mengurutkan hasil berdasarkan `task_id` sebelum menulis manifest. Collector Master
   harus melakukan hal yang sama karena `imap_unordered` tidak menjamin urutan.
5. `pool_context()` mengembalikan konteks `spawn`; pakai helper ini di Worker agar konsisten.
6. Nama field `metrics.json` local (`procs`, `tasks_ok`, `tasks_failed`, `busy_per_process`,
   `errors`) menjadi acuan `metrics.json` Master pada Fase 4.
7. Smoke Fase 3 sudah terdaftar di `scripts/gate.py`; Fase 4 perlu menambah `SMOKE_COMMANDS[4]`
   (`scripts/e2e_local.py --workers 3`) dan penanda `E2E OK`.

## 12. Commit
Hash: diisi pada commit akhir fase (lihat `git log`). Tag: phase-03-done
