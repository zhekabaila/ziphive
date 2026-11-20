# PHASE-02 — Mesin kompresi, task decomposition, baseline sequential

- Branch: phase/02-compression-sequential
- Mulai / selesai: 2026-11-20 / 2026-11-20
- Status: DONE

## 1. Tujuan
Pecah dataset menjadi task, kompresi, verifikasi, dan siapkan baseline pengujian (a) (PLAN.md Fase 2).
Lingkup hanya P2-T1 sampai P2-T6. Tidak ada jaringan, Master, Worker, atau multiprocessing pada fase
ini.

## 2. Ringkasan hasil
Dataset kini dipindai dengan urutan deterministik dan dipecah menjadi task per chunk 4 MiB (dapat
diubah lewat `--chunk-mb`), file kosong dilewati, dan `--repeat` menggandakan daftar task dengan
folder salinan `chunks/rN`. Empat algoritma tersedia lewat satu registri: `gzip`, `bz2`, `lzma`, dan
`sim` (khusus test, ditandai `simulated: true` di `metrics.json`). Manifest JSON mencatat file asal,
urutan chunk, offset, panjang, SHA-256 data asli, nama file hasil, dan ukuran hasil, sehingga
rekonstruksi menghasilkan byte identik dan verifikasi mendeteksi chunk rusak atau hilang. Baseline
`pcomp.sequential` menulis `manifest.json` dan `metrics.json` (waktu, throughput, rasio, jumlah task).
Seluruh test ditulis lebih dulu (merah: 6 error koleksi `ModuleNotFoundError`), lalu implementasi
sampai hijau: 108 unit test dan 3 integration test lulus, coverage 82,87%.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P2-T1 | `tasks.py`: dataclass `Task`, enum `TaskState` | DONE | Empat state: PENDING, ASSIGNED, DONE, FAILED |
| P2-T2 | `chunker.py`: pindai folder, pecah per chunk, `--repeat`, lewati file kosong | DONE | Urutan berdasarkan path relatif POSIX |
| P2-T3 | `compressor.py`: `compress`/`decompress`, registri algoritma | DONE | `gzip`, `bz2`, `lzma`, `sim`; level 0-9 |
| P2-T4 | `manifest.py`: tulis/baca `manifest.json`, rekonstruksi, verifikasi | DONE | Skema versi 1, validasi field wajib |
| P2-T5 | `tools/make_dataset.py`, `tools/download_corpus.py`, `tools/verify.py` | DONE | `download_corpus` tidak dijalankan otomatis |
| P2-T6 | `sequential.py` CLI dengan `metrics.json` | DONE | Field selaras skema CSV EXPERIMENTS.md bagian 4 |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/tasks.py` | add | P2-T1: model task dan state machine |
| `src/pcomp/chunker.py` | add | P2-T2: pemindaian folder dan task decomposition |
| `src/pcomp/compressor.py` | add | P2-T3: registri dan round-trip algoritma kompresi |
| `src/pcomp/manifest.py` | add | P2-T4: manifest, rekonstruksi, verifikasi |
| `src/pcomp/sequential.py` | add | P2-T6: baseline sequential dan `metrics.json` |
| `src/pcomp/tools/make_dataset.py` | add | P2-T5: dataset sintetis deterministik |
| `src/pcomp/tools/download_corpus.py` | add | P2-T5: unduh korpus, wajib `--url` eksplisit |
| `src/pcomp/tools/verify.py` | add | P2-T5: verifikasi manifest, cetak `VERIFY OK` |
| `src/pcomp/constants.py` | mod | `MIB`, default chunk/repeat/algo/level, `SIM_SECONDS_PER_MB`, versi `0.02.0` |
| `src/pcomp/banner.py` | mod | `try_print_banner` agar CLI tetap jalan saat `group.toml` belum lengkap |
| `pyproject.toml` | mod | Versi `0.02.0` |
| `scripts/gate.py` | mod | `SMOKE_COMMANDS[2]`, `SMOKE_EXPECTED[2] = ["VERIFY OK"]` |
| `TESTING.md` | mod | Baris UT-TSK, UT-SEQ, UT-TOOL, IT-SEQ |
| `ASSETS.md` | mod | Kolom data belum diunduh diisi "diisi user" |
| `CHANGELOG.md` | mod | Entri `0.02.0` |
| `PLAN.md` | mod | Status fase 2 `DONE`, `CURRENT PHASE: 3` |
| `docs/phase-logs/PHASE-02.md` | add | Phase log fase ini |
| `tests/unit/test_tasks.py` | add | UT-TSK-01..02 |
| `tests/unit/test_chunker.py` | add | UT-CHK-01..05 (batas chunk, urutan, repeat) |
| `tests/unit/test_compressor.py` | add | UT-CMP-01..03 (round-trip per algoritma) |
| `tests/unit/test_manifest.py` | add | UT-MAN-01..03 (skema, rekonstruksi, deteksi rusak) |
| `tests/unit/test_sequential.py` | add | UT-SEQ-01 dan varian `sim`, `--repeat`, input kosong |
| `tests/unit/test_tools.py` | add | UT-TOOL-01..02 (dataset sintetis, rencana unduhan) |
| `tests/unit/test_banner.py` | mod | Test `try_print_banner` valid dan tidak ada |
| `tests/integration/test_sequential_cli.py` | add | IT-SEQ-01: make_dataset, sequential, verify |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 44 | 108 | UT-TSK 3, UT-CHK 9, UT-CMP 12, UT-MAN 8, UT-SEQ 4, UT-TOOL 6, banner 2 |
| Integration | 1 | 3 | IT-SEQ-01: dataset sintetis 2 MiB, `VERIFY OK` |

Coverage: 82,87% (`--cov=src/pcomp --cov-fail-under=80`). Penurunan dari 92,17% terjadi karena modul
baru diuji lewat perilaku publiknya, sedangkan cabang penanganan galat I/O belum semuanya tersentuh.

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=61 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 22 source files` |
| G3 Unit+cov | PASS | `Total coverage: 82.87% | 108 passed, 3 deselected` |
| G4 Integration | PASS | `3 passed, 108 deselected` |
| G5 Regresi | PASS | `seluruh test fase lama ikut dijalankan oleh G3 dan G4` |
| G6 Smoke | PASS | `make_dataset -> rc=0: DATASET OK; sequential -> rc=0: SEQUENTIAL OK; verify -> rc=0: VERIFY OK` |
| G7 Flaky x3 | SKIP | `dilewati: berlaku fase 4 ke atas (SDLC.md G7)` |
| G8 Dokumen | PASS | CHANGELOG `0.02.0`, PHASE-02 terisi, status PLAN `DONE` |
| G9 Repo | PASS | `55 file terlacak, tidak ada pelanggaran` |

Keluaran lengkap: `reports/gate-latest.txt` (tidak di-commit karena `reports/` di-ignore).

Smoke manual 20 MiB (`data/synth`, 4 file): `DATASET OK`, lalu sequential `tasks: 9`,
`total_mb: 20.000778`, `ratio: 2.630871`, `time_s: 4.185133`, `throughput: 4.779007 MB/s`,
`SEQUENTIAL OK`, lalu verify `chunks: 9`, `VERIFY OK`. Angka ini berasal dari dataset sintetis
`data/synth` dan hanya bukti smoke, bukan hasil eksperimen.

## 7. Deviasi dari rencana
1. Nama file chunk tidak ditetapkan ARCHITECTURE.md bagian 5. Dipakai
   `chunks/<file>.<index:04d>.<ext>` dan `chunks/r<copy>/<...>` bila `--repeat` lebih dari 1.
   Dampak: manifest menyimpan path ini sehingga konsumen manifest tidak perlu menebak nama.
2. Ditambahkan `try_print_banner` di `banner.py` beserta 2 unit test. Alasannya, CLI baru akan gagal
   bila `config/group.toml` tidak terbaca, padahal AGENTS.md mewajibkan banner dan default
   `config/group.toml` masih berisi placeholder. Perilaku lama `print_banner` tidak berubah.
3. Ditambahkan ID test yang belum ada di matriks TESTING.md bagian 4: UT-TSK, UT-SEQ, UT-TOOL,
   IT-SEQ. ID dicatat di TESTING.md agar phase log dapat merujuknya.
4. `download_corpus.py` mendukung `--dry-run` dan `--expected-sha256`. Tidak ada unduhan nyata pada
   fase ini, sehingga ASSETS.md diisi "diisi user" untuk kolom tanggal akses dan SHA-256.
5. Default `algo`/`level`/`chunk_mb` diambil dari rekomendasi EXPERIMENTS.md bagian 1 (`lzma`,
   level 6, chunk 4 MiB), bukan angka baru.
6. Test `scan_files` diubah memakai `path.relative_to(root)` (bukan `path.as_posix()`) karena
   `rglob` mengembalikan path absolut di Windows. Test diperbaiki, bukan implementasi.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| 6 error koleksi saat test merah | Modul `tasks`, `chunker`, `compressor`, `manifest`, `sequential`, `tools` belum ada | Implementasi modul sesuai kontrak PLAN.md P2-T1..T6 |
| `import file mismatch` saat koleksi | `tests/unit/test_sequential.py` dan `tests/integration/test_sequential.py` bernama modul sama | File integration diganti nama `test_sequential_cli.py` |
| Asersi urutan file gagal di Windows | `rglob` mengembalikan path absolut | Test memakai `path.relative_to(root).as_posix()` |
| `UP017` dan `SIM117` dari ruff | `datetime.now(timezone.utc)` dan `with` bersarang | Pakai `datetime.UTC` dan satu `with` multi-konteks |
| G8 gagal pada run pertama | CHANGELOG dan phase log belum diisi | Dokumentasi fase dilengkapi lalu gate penuh diulang |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. `dataset.json` ditulis di dalam folder dataset sehingga ikut dipindai dan dikompresi sebagai data.
   Ukuran total chunk jadi sedikit lebih besar dari ukuran dataset murni.
2. Kompresi per chunk menurunkan rasio dibanding kompresi file utuh (EXPERIMENTS.md bagian 7).
   Angka rasio fase ini tidak boleh dibandingkan langsung dengan alat kompresi file tunggal.
3. `--repeat` menggandakan beban dari file yang sama, bukan menambah data baru
   (EXPERIMENTS.md bagian 7). Task salinan diberi folder `chunks/rN` agar tidak bertabrakan.
4. Algoritma `sim` hanya untuk test: tidak mengompres, hanya tidur sebanding ukuran, dan hasilnya
   ditandai `simulated: true`. Data hasil `sim` tidak boleh masuk laporan.
5. `download_corpus.py` belum pernah dijalankan karena URL resmi harus diberikan user. SHA-256 dan
   tanggal akses di ASSETS.md masih "diisi user".
6. `metrics.json` sequential belum memuat metrik sistem (CPU, memori, imbalance). Itu lingkup
   Fase 7.
7. `verify.py` mendekompresi seluruh chunk di memori satu per satu; aman untuk chunk 4 MiB tetapi
   tidak untuk `--chunk-mb` sangat besar.
8. Level kompresi divalidasi 0-9, tetapi `bz2` menolak level 0 karena pustaka standar tidak
   menyediakannya. Perbedaan ini belum didokumentasikan di CLI `--help`.
9. G7 (cek flaky 3 kali) belum berlaku sampai Fase 4.
10. Belum ada validasi bahwa chunk yang ditulis benar-benar berasal dari offset yang diminta selain
    lewat SHA-256 data asli pada manifest.

## 11. Catatan serah-terima ke fase berikutnya
1. Fase 3 wajib memakai ulang `chunker.plan_tasks`, `chunker.read_chunk`, `compressor.compress`,
   dan `manifest.chunk_output_name`; jangan menyalin logika penamaan chunk agar manifest tetap
   kompatibel dengan `tools/verify.py`.
2. `compressor.compress` menerima dan mengembalikan `bytes`, sehingga aman dikirim ke proses anak
   lewat `multiprocessing`; objek `Task` hanya berisi tipe primitif dan mudah dipickle.
3. `run_sequential` menerima parameter `clock` agar pengukuran waktu dapat diganti di test. Pola ini
   dapat dipakai untuk uji deterministik di fase berikutnya.
4. Nama field `metrics.json` (`time_s`, `throughput_mbs`, `ratio`, `total_mb`, `tasks`) sengaja
   mengikuti skema `results/summary.csv` pada EXPERIMENTS.md bagian 4.
5. `sim` sudah ditandai `simulated: true`; setiap agregasi hasil wajib membuang baris ini.
6. Smoke Fase 2 sudah terdaftar di `scripts/gate.py` (`SMOKE_COMMANDS[2]`); Fase 3 perlu menambah
   entri `SMOKE_COMMANDS[3]`, jika tidak G6 akan gagal.

## 12. Commit
Hash: diisi pada commit akhir fase (lihat `git log`). Tag: phase-02-done
