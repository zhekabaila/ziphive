# SDLC.md — Siklus Pengembangan per Fase

Model: iteratif per fase. Satu fase = satu siklus lengkap. Pelaksana: AI agent. Pengawas: user.

## 1. Siklus satu fase
```
[1 Baca] -> [2 Rencana] -> [3 Test-first] -> [4 Implementasi] -> [5 Verifikasi Gate]
     ^                                                                  |
     |                                         gagal: perbaiki, ulang dari gate
     |                                                                  v
[8 Serah-terima] <- [7 Commit & Tag] <- [6 Dokumentasi & Pencatatan] <- lulus
```
1. Baca: AGENTS.md, PLAN.md fase aktif, dokumen desain terkait. Buat branch `phase/NN-slug` dari `main`.
2. Rencana: salin `docs/phase-logs/_TEMPLATE.md` ke `PHASE-NN.md`, isi tujuan dan daftar task. Cocokkan dengan PLAN.md.
3. Test-first: tulis unit test dan integration test untuk task fase ini. Jalankan, pastikan gagal karena fitur belum ada.
4. Implementasi: kerjakan task satu per satu sampai test hijau. Perubahan kecil dan terarah.
5. Verifikasi: jalankan `python scripts/gate.py` (bagian 4). Gagal: perbaiki akar masalah, jalankan ulang gate penuh.
6. Dokumentasi: lengkapi phase log, `CHANGELOG.md`, status di `PLAN.md`, serta `ARCHITECTURE.md`/`PROTOCOL.md`/`DECISIONS.md` bila ada perubahan desain.
7. Commit & tag: bagian 5.
8. Serah-terima: laporan akhir fase (AGENTS.md bagian 8). Berhenti. Fase berikutnya dimulai setelah user memberi perintah lanjut, kecuali user sudah menyatakan "lanjut otomatis".

## 2. Definition of Ready (boleh mulai fase)
Fase sebelumnya DONE dan bertag. `main` bersih. Gate fase sebelumnya masih hijau di awal sesi.

## 3. Definition of Done (fase selesai)
Semua task di PLAN.md fase tersebut terpenuhi, gate lulus, dokumen dan log lengkap, commit dan tag dibuat, `CURRENT PHASE` bergeser.

## 4. Verification Gate (`scripts/gate.py`, semua wajib lulus)
| ID | Pemeriksaan | Perintah | Kriteria |
|---|---|---|---|
| G1 | Lint dan format | `ruff check .` dan `ruff format --check .` | 0 error |
| G2 | Type check | `mypy src` | 0 error |
| G3 | Unit test + coverage | `pytest -m "not integration and not perf and not slow" --cov=src/pcomp --cov-fail-under=80` | semua lulus, coverage minimal 80% |
| G4 | Integration test | `pytest -m integration` | semua lulus |
| G5 | Regresi | G3 + G4 mencakup seluruh test semua fase | tidak ada test fase lama yang gagal |
| G6 | Smoke test fase | perintah "Smoke" pada PLAN.md fase aktif | keluaran sesuai yang tertulis |
| G7 | Cek flaky (fase 4 ke atas) | `pytest -m integration` diulang 3 kali | 3 kali lulus |
| G8 | Sinkron dokumen | gate memeriksa: entri CHANGELOG, `PHASE-NN.md` terisi, status PLAN.md | lengkap |
| G9 | Kebersihan repo | `git status`, ukuran file | tidak ada file liar, tidak ada file lebih dari 5 MB, `data/` dan `output/` tidak ikut |

`gate.py` mencetak tabel PASS/FAIL dan menyimpan ringkasannya ke `reports/gate-latest.txt`. Salin ringkasan itu ke phase log.

Kegagalan gate: (1) baca pesan error, (2) cari akar masalah, (3) perbaiki kode, bukan test, kecuali test memang salah dan alasannya dicatat di phase log, (4) jalankan ulang gate PENUH.

## 5. Aturan Git
- Branch: `main` (selalu hijau) dan `phase/NN-slug` (satu per fase).
- Commit hanya setelah gate lulus. Stage file secara eksplisit (`git add <path>`), periksa `git diff --staged --stat`. Jangan `git add -A` tanpa memeriksa.
- Format commit (Conventional Commits):
```
<type>(phase-NN): <ringkasan imperatif, maks 72 karakter>

Changes:
- <perubahan 1>
- <perubahan 2>
Tests: unit <n> passed, integration <n> passed, coverage <x>%
Gate: G1-G9 PASS
Phase-Log: docs/phase-logs/PHASE-NN.md
```
type: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`, `perf`.
- Setelah commit: `git checkout main && git merge --no-ff phase/NN-slug`, lalu `git tag -a phase-NN-done -m "Phase NN done"`. Jalankan `python scripts/gate.py --quick` di `main` sebagai konfirmasi.
- Satu fase boleh memiliki beberapa commit atomik, tetapi setiap commit harus lulus G1 sampai G4 sendiri. Commit akhir fase wajib lulus gate penuh.
- Bug fase lama ditemukan belakangan: buat commit `fix(phase-XX)` baru beserta test regresi, catat di CHANGELOG bagian Fixed dan phase log fase aktif (bagian "Back-fix"). Tidak boleh menulis ulang sejarah.

## 6. Pencatatan perubahan (wajib, tiga lapis)
1. Commit message: ringkas, sesuai format bagian 5.
2. `CHANGELOG.md` (format Keep a Changelog): tulis di `[Unreleased]` selama fase berjalan. Saat commit akhir fase, pindahkan ke versi `0.<NN>.0 - <tanggal>`. Kategori: Added, Changed, Fixed, Removed, Security, Docs.
3. `docs/phase-logs/PHASE-NN.md`: catatan rinci, isi dari `_TEMPLATE.md`. Wajib memuat tabel file yang diubah beserta alasan, test yang ditambah, hasil gate, deviasi dari rencana, masalah dan solusinya, keterbatasan yang diketahui.

Perubahan desain: perbarui `ARCHITECTURE.md`/`PROTOCOL.md`, tambah entri `DECISIONS.md` (konteks, keputusan, konsekuensi), dan sebut di phase log.

## 7. Versi
Tag `phase-NN-done` tiap fase. `v1.0.0` setelah Fase 10. Versi protokol (`PROTOCOL_VERSION` di constants.py) dinaikkan bila format pesan berubah.

## 8. Pengecualian fase HUMAN-REQUIRED
Fase 8 dipecah dua: bagian agent di-commit dan bertag `phase-08a-done` (status PLAN.md: IN PROGRESS menunggu user, CURRENT PHASE tetap 8), lalu bagian pencatatan hasil user menghasilkan `phase-08-done`. Fase 10 boleh memakai commit atomik per bagian (10A, 10B); tag `phase-10-done` dan `v1.0.0` hanya di akhir bagian B. Urutan prompt lengkap ada di `PROMPTS.md`.
