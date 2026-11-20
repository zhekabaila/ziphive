# PHASE-00 — Bootstrap repo dan tooling

- Branch: phase/00-bootstrap
- Mulai / selesai: 2026-11-20 / 2026-11-20
- Status: DONE

## 1. Tujuan
Repo siap, gate bisa berjalan, kerangka folder ada (PLAN.md Fase 0). Lingkup hanya P0-T1 sampai
P0-T7. Tidak ada protokol, chunker, compressor, Master, Worker, atau logika aplikasi pada fase ini.

## 2. Ringkasan hasil
Repo kini memiliki `pyproject.toml`, empat file requirement, `Makefile`, `.gitignore`, dan struktur
paket `src/pcomp` dengan enam subpaket kosong. `constants.py` dan `banner.py` membaca identitas
kelompok dari `config/group.toml` (masih placeholder), dan CLI `python -m pcomp` serta
`python -m pcomp --version` sudah berjalan. `scripts/gate.py` menjalankan G1 sampai G9 dengan mode
`--quick` dan menulis `reports/gate-latest.txt`. Empat file konfigurasi default sudah tersedia.
Test bootstrap ditulis lebih dulu (merah: 4 error koleksi, `ModuleNotFoundError: No module named
'pcomp'`), lalu implementasi sampai hijau: 22 unit test dan 1 integration test lulus, coverage
96,12%.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P0-T1 | `.gitignore` (data/, output/, reports/, .venv, cache tools) | DONE | Repo dan branch `main` sudah ada sebelumnya, tidak diulang |
| P0-T2 | `pyproject.toml`, `requirements.txt`, `requirements-worker.txt`, `requirements-dev.txt` | DONE | src layout, Python >= 3.11, ruff 100, mypy strict, marker integration/perf/slow, timeout 60 s |
| P0-T3 | Kerangka folder sesuai AGENTS.md bagian 5, semua paket berisi `__init__.py` | DONE | `master`, `worker`, `metrics`, `bench`, `tools` masih kosong |
| P0-T4 | `config/group.toml` (placeholder), `master.toml`, `worker.toml`, `nodes.toml` | DONE | `group.toml` hanya placeholder, belum diisi user |
| P0-T5 | `constants.py`, `banner.py`, `python -m pcomp --version` | DONE | Banner memberi peringatan bila placeholder belum diisi |
| P0-T6 | `scripts/gate.py` (G1-G9, `--quick`, `reports/gate-latest.txt`), `Makefile` | DONE | G7 dilewati untuk fase < 4 sesuai SDLC.md |
| P0-T7 | `README.md` singkat, salin seluruh dokumen perencanaan | DONE | Dokumen perencanaan sudah ada di root dan ikut ter-commit |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `.gitignore` | add | P0-T1: artefak lokal dan data tidak masuk repo |
| `pyproject.toml` | add | P0-T2: metadata paket, ruff, mypy, pytest |
| `requirements.txt` | add | P0-T2: dependensi runtime Master |
| `requirements-worker.txt` | add | P0-T2: dependensi runtime Worker (psutil) |
| `requirements-dev.txt` | add | P0-T2: pytest, ruff, mypy, types-psutil |
| `Makefile` | add | P0-T6: pembungkus perintah standar |
| `README.md` | add | P0-T7: setup dan perintah |
| `PLAN.md` | mod | Status fase 0 dan `CURRENT PHASE` |
| `CHANGELOG.md` | mod | Entri `0.00.0` (SDLC.md bagian 6) |
| `TESTING.md` | mod | Tambah baris UT-BOOT dan IT-BOOT pada matriks test |
| `docs/phase-logs/_TEMPLATE.md` | mod | Dipindah dari `_TEMPLATE.md` agar sesuai path SDLC.md |
| `docs/phase-logs/PHASE-00.md` | add | Phase log fase ini |
| `config/group.toml` | add | P0-T4: identitas kelompok (placeholder) |
| `config/master.toml` | add | P0-T4: default Master (ARCHITECTURE.md bagian 10) |
| `config/worker.toml` | add | P0-T4: default Worker |
| `config/nodes.toml` | add | P0-T4: daftar 10 node (host placeholder) |
| `src/pcomp/__init__.py` | add | P0-T3: paket utama |
| `src/pcomp/__main__.py` | add | P0-T5: entry point CLI |
| `src/pcomp/constants.py` | add | P0-T5: konstanta global |
| `src/pcomp/banner.py` | add | P0-T5: banner identitas kelompok |
| `src/pcomp/master/__init__.py` | add | P0-T3: kerangka paket |
| `src/pcomp/worker/__init__.py` | add | P0-T3: kerangka paket |
| `src/pcomp/metrics/__init__.py` | add | P0-T3: kerangka paket |
| `src/pcomp/bench/__init__.py` | add | P0-T3: kerangka paket |
| `src/pcomp/tools/__init__.py` | add | P0-T3: kerangka paket |
| `scripts/gate.py` | add | P0-T6: Verification Gate G1-G9 |
| `tests/conftest.py` | add | Fixture `repo_root`, `valid_group_file`, `placeholder_group_file` |
| `tests/unit/test_package.py` | add | UT-BOOT-01 |
| `tests/unit/test_banner.py` | add | UT-BOOT-02 dan UT-BOOT-03 |
| `tests/unit/test_cli.py` | add | UT-BOOT-04 |
| `tests/unit/test_gate.py` | add | UT-BOOT-05 |
| `tests/integration/test_cli_smoke.py` | add | IT-BOOT-01 |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 22 | 22 | UT-BOOT-01 import dan versi, UT-BOOT-02 banner valid, UT-BOOT-03 banner placeholder, UT-BOOT-04 CLI, UT-BOOT-05 parsing gate |
| Integration | 1 | 1 | IT-BOOT-01: `python -m pcomp --version` sebagai subprocess |

Coverage: 96,12% (`--cov=src/pcomp --cov-fail-under=80`).

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=33 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 9 source files` |
| G3 Unit+cov | PASS | `Total coverage: 96.12% | 22 passed, 1 deselected` |
| G4 Integration | PASS | `1 passed, 22 deselected` |
| G5 Regresi | PASS | seluruh test dijalankan oleh G3 dan G4 |
| G6 Smoke | PASS | `python -m pcomp --version -> rc=0: ZipHive 0.00.0` |
| G7 Flaky x3 | SKIP | dilewati: berlaku fase 4 ke atas (SDLC.md G7) |
| G8 Dokumen | PASS | CHANGELOG `0.00.0`, PHASE-00 terisi, status PLAN `DONE` |
| G9 Repo | PASS | tidak ada file > 5 MB, `data/` dan `output/` tidak terlacak |

Keluaran lengkap: `reports/gate-latest.txt` (tidak di-commit karena `reports/` di-ignore).

## 7. Deviasi dari rencana
1. `_TEMPLATE.md` berada di root, sedangkan SDLC.md bagian 1 dan 6 menyebut
   `docs/phase-logs/_TEMPLATE.md`. File dipindah ke path tersebut (bukan disalin) agar hanya ada
   satu sumber template.
2. PLAN.md Fase 0 menetapkan smoke "`python scripts/gate.py` seluruhnya PASS". Karena gate tidak
   dapat memverifikasi dirinya sendiri secara rekursif, G6 memeriksa bagian pertama smoke
   (`python -m pcomp --version`), sedangkan kriteria "gate seluruhnya PASS" dipenuhi oleh agregat
   G1 sampai G9 pada run yang sama.
3. SDLC.md bagian 1 menaruh gate di langkah 5 dan dokumentasi di langkah 6, sedangkan G8 memeriksa
   dokumen. Gate dijalankan dua kali: run antara (G8 gagal, tercatat di transkrip) lalu run penuh
   setelah dokumen fase dilengkapi. Keputusan ini dicatat, bukan mengubah gate.
4. `CURRENT PHASE` bergeser ke 1 sebelum commit, sementara fase 1 masih TODO. Gate memakai aturan
   `resolve_gate_phase`: bila fase di `CURRENT PHASE` masih TODO, gate memverifikasi fase terakhir
   yang sudah dikerjakan. Aturan ini diuji di UT-BOOT-05.
5. TESTING.md bagian 4 belum punya ID untuk test bootstrap. Ditambahkan baris UT-BOOT-01..05 dan
   IT-BOOT-01 agar ID test yang dipakai phase log dapat dilacak.
6. Dependensi dev `ruff`, `mypy`, `pytest-timeout`, `types-psutil` dipasang di lingkungan lokal
   melalui `requirements-dev.txt`; tidak ada dependensi runtime baru (tetap `psutil`).

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| `ModuleNotFoundError: No module named 'pcomp'` saat test merah | Paket belum ada dan `src` belum di `sys.path` | `pythonpath = ["src"]` di pyproject; gate menambahkan `PYTHONPATH=src` |
| `AttributeError: 'NoneType' object has no attribute '__dict__'` saat memuat `scripts/gate.py` | `dataclass` butuh modul terdaftar di `sys.modules` saat dieksekusi via importlib | Test mendaftarkan modul ke `sys.modules` sebelum `exec_module` |
| `python -m pcomp` gagal di luar pytest | Paket belum terpasang | `pip install -e .` (didokumentasikan di README); gate tidak bergantung pada instalasi |
| G3 gagal karena sampel PLAN pada test tidak konsisten | `PLAN_SAMPLE` menandai fase 3 TODO padahal `CURRENT PHASE: 3` | Sampel diperbaiki menjadi fase 3 IN PROGRESS; logika gate tidak diubah |
| `ruff format --check` gagal pada 2 file | Baris melebihi 100 karakter dan format belum dirapikan | `ruff format .` lalu ulangi G1 |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. Urutan gate dan dokumentasi (SDLC.md bagian 1 langkah 5-6 vs G8) masih merupakan celah proses;
   saat ini diselesaikan dengan menjalankan gate dua kali. Usulan perbaikan dokumen dicatat, belum
   diimplementasikan karena di luar lingkup fase 0.
2. G6 bersifat self-referential untuk fase 0 (lihat bagian 7 butir 2).
3. `reports/` di-ignore sehingga `gate-latest.txt` tidak ikut repo; bukti gate hanya ada di phase log.
4. Belum ada CI otomatis; gate dijalankan manual di mesin pengembang (Windows, PowerShell).
5. Lingkungan pengembangan memakai Python 3.14.4, sedangkan target dokumen 3.11+. Versi `ruff` dan
   `mypy` belum dipin nomornya di `requirements-dev.txt`; risiko R2 (versi beda antar node) tetap.
6. `config/nodes.toml` berisi placeholder `<IP_N1>` sampai `<IP_N10>` dan harus diisi user pada Fase 8.

## 11. Catatan serah-terima ke fase berikutnya
1. Fase 1 menambah `protocol.py`, `net.py`, `config.py`, `logging_setup.py`, `metrics/events.py`;
   `src/pcomp/metrics/__init__.py` sudah ada dan tidak perlu dibuat ulang.
2. `scripts/gate.py` menyimpan smoke per fase di `SMOKE_COMMANDS`; fase 1 wajib menambah entri
   `1: [pytest -m integration -k echo]` agar G6 tidak gagal.
3. Jalankan `python -m pytest` dan `python scripts/gate.py` dari akar repo. Perintah `ruff` dan
   `mypy` dipanggil sebagai `python -m ruff` / `python -m mypy` karena folder Scripts Python tidak
   ada di PATH mesin ini.
4. `python -m pcomp` membutuhkan `pip install -e .` atau `PYTHONPATH=src`.
5. Placeholder `config/group.toml` belum diisi; banner akan menampilkan peringatan sampai user
   mengisinya.

## 12. Commit
Hash: diisi pada commit akhir fase (lihat `git log`). Tag: phase-00-done
