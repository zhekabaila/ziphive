# PHASE-10 — Dokumentasi, laporan, paket pengumpulan

- Branch: `phase/10-final` (Bagian A), `phase/10-final-b` (Bagian B)
- Mulai / selesai: 2026-11-22 / 2026-11-22
- Status: DONE

## 1. Tujuan
Menyiapkan seluruh deliverable akhir sesuai PLAN.md fase 10: panduan kode (`docs/CODE_GUIDE.md`),
`README.md` final, `ASSETS.md` final, laporan DOCX, naskah video, uji reproduksi, dan paket ZIP.
Pelaksanaan dibagi dua bagian atas instruksi user 2026-11-22. Bagian A mengerjakan P10-T1 dan
P10-T4. Bagian B mengerjakan P10-T2, P10-T3, P10-T5, dan P10-T6.

## 2. Ringkasan hasil
Bagian A: `docs/CODE_GUIDE.md` disusun dari pembacaan 40 berkas `src/pcomp` (5.712 baris), 6 skrip
`scripts/` (1.912 baris), dan struktur test. `README.md` ditulis ulang dari kondisi Fase 9, dan
`ASSETS.md` diisi dari data nyata (dataset sintetis, tujuh grafik, empat tangkapan layar, versi
pustaka, tabel formula).

Bagian B: laporan UAS dibangun sebagai DOCX melalui `scripts/build_report.py` dan
`scripts/report_content.py` memakai OOXML dari pustaka standar, dengan sampul, daftar isi otomatis,
BAB I sampai BAB IV, kesimpulan, dan daftar pustaka. Sebelas gambar disematkan (tujuh grafik
`results/figures/` dan empat tangkapan layar `reports/img/`), sedangkan dua diagram yang belum ada
(topologi dan urutan pesan) serta logo universitas ditandai kotak placeholder berisi nomor, isi, dan
cara memperoleh. Seluruh angka laporan disalin dari `results/summary.csv`,
`results/summary_agg.csv`, dan `docs/ANALYSIS.md`. `docs/DEMO_SCRIPT.md` memuat naskah lima menit
sesuai tabel adegan `SUBMISSION.md` bagian 3, daftar perintah, checklist rekaman, dan daftar bahan.
Smoke fase 10 diganti menjadi `scripts/smoke_package.py` yang membangun ZIP, memeriksa isi, lalu
menjalankan perintah dari nol pada folder hasil ekstrak. Versi proyek naik dari `0.09.0` menjadi
`1.0.0`.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P10-T1 | `docs/CODE_GUIDE.md` | DONE | 40 berkas sumber dibaca; modul, class, fungsi, alur, dan perintah dijelaskan |
| P10-T2 | Draf laporan BAB I-IV + Kesimpulan (DOCX) | DONE | `scripts/build_report.py` dan `scripts/report_content.py`; keluaran `reports/laporan/ZipHive-Laporan-UAS.docx` (1.759,3 KiB, 11 gambar) |
| P10-T3 | Naskah video demo maks 5 menit | DONE | `docs/DEMO_SCRIPT.md` |
| P10-T4 | `README.md` final dan `ASSETS.md` final | DONE | README ditulis ulang; ASSETS diisi dari `data/bench/dataset.json`, `results/figures/`, dan `reports/img/` |
| P10-T5 | Uji reproduksi clone bersih | DONE | Clone ke folder sementara, `pip install -e ".[dev,analysis]"`, gate penuh `PASS` |
| P10-T6 | ZIP sumber dan pemeriksaan isi | DONE | `dist/ziphive-source-1.0.0.zip`, 761 entri, tanpa `data/`, `output/`, `reports/`, `.venv`, `dist/`, `.git` |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `docs/CODE_GUIDE.md` | add | P10-T1 |
| `README.md` | mod | P10-T4 dan P10-T2/T3: status Fase 10, perintah `build_report.py` dan `smoke_package.py`, `docs/DEMO_SCRIPT.md`, bagian `Paket pengumpulan` |
| `ASSETS.md` | mod | P10-T4: isi data nyata, tandai yang belum terverifikasi |
| `docs/DEMO_SCRIPT.md` | add | P10-T3 |
| `docs/phase-logs/PHASE-10.md` | add | Catatan fase ini |
| `scripts/build_report.py` | add | P10-T2: pembangun DOCX berbasis OOXML dan pustaka standar |
| `scripts/report_content.py` | add | P10-T2: isi laporan (BAB I-IV, kesimpulan, daftar pustaka) |
| `scripts/smoke_package.py` | add | P10-T6 dan smoke fase 10: bangun ZIP, periksa isi, jalankan dari nol |
| `scripts/gate.py` | mod | Smoke fase 10 menjadi `smoke_package.py` dengan penanda `PACKAGE OK`; G8 menerima judul versi `1.0.0` untuk fase penutup |
| `tests/unit/test_build_report.py` | add | UT-DOC-01..05: penanda teks, judul bab, ukuran PNG, placeholder, pemeriksa isi ZIP |
| `pyproject.toml` | mod | Versi `1.0.0` |
| `src/pcomp/constants.py` | mod | `__version__ = "1.0.0"` |
| `CHANGELOG.md` | mod | Entri versi `1.0.0` |
| `PLAN.md` | mod | Status fase 10 `DONE` dan catatan fase penutup |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 5 | 241 | UT-DOC-01..05 pada `tests/unit/test_build_report.py` |
| Integration | 0 | 19 | Sama seperti fase 9 |

Coverage: 84,56 % (ambang 80 %). Coverage diukur pada `src/pcomp`, sedangkan skrip baru berada di
`scripts/` sehingga tidak masuk hitungan coverage.

## 6. Hasil Verification Gate
Gate penuh dijalankan 2026-11-22 pukul 20:48, hasil `PASS (seluruh gate wajib lulus)`.

| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!`; `format=126 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 40 source files` |
| G3 Unit+cov | PASS | `241 passed, 20 deselected`, coverage `84.56 %` |
| G4 Integration | PASS | `19 passed, 242 deselected` |
| G5 Regresi | PASS | seluruh test fase lama dijalankan G3 dan G4 |
| G6 Smoke | PASS | `scripts/smoke_package.py` -> `PACKAGE OK: 761 entri, 12 entri wajib lengkap` |
| G7 Flaky x3 | PASS | 3 kali lulus |
| G8 Dokumen | PASS | CHANGELOG versi `1.0.0`, phase log, dan status PLAN sinkron |
| G9 Repo | PASS | `752 file terlacak, tidak ada pelanggaran` |

## 7. Deviasi dari rencana
1. Pengerjaan fase 10 dibagi dua bagian atas instruksi user. Bagian A mengerjakan P10-T1 dan
   P10-T4 tanpa tag, Bagian B mengerjakan P10-T2, P10-T3, P10-T5, dan P10-T6.
2. Struktur bab laporan mengikuti tabel `SUBMISSION.md` bagian 2, yaitu Pendahuluan, Studi Pustaka,
   Metodologi, Hasil dan Pembahasan, lalu Kesimpulan. Skill `laporan-akademik-id` dipakai untuk tata
   bahasa, penomoran, keterangan gambar dan tabel, serta bentuk placeholder, bukan untuk nama bab.
3. DOCX dibangun dengan OOXML langsung dari pustaka standar (`zipfile`) karena `python-docx`,
   `pandoc`, dan LibreOffice tidak tersedia pada mesin ini, sedangkan menambah dependensi baru
   dilarang AGENTS.md bagian 2 butir 7 tanpa catatan di `DECISIONS.md`. Berkas keluaran berada di
   `reports/` yang masuk `.gitignore`, sehingga laporan tidak ikut commit dan dapat dibangun ulang
   dengan `python scripts/build_report.py`.
4. Laporan memakai angka Fase 9 yang sudah bertag `phase-09-done`; tidak ada eksperimen ulang.
5. E7 tetap ditulis sebagai bagian rancangan eksperimen sesuai tabel `SUBMISSION.md` bagian 2, dengan
   keterangan bahwa E7 opsional dan tidak dijalankan sehingga tidak memiliki data.
6. Versi paket akhir `1.0.0` sesuai instruksi user, berbeda dari pola `0.<NN>.0` pada `SDLC.md`
   bagian 6. Gate G8 diperluas agar menerima judul versi `1.0.0` khusus fase penutup.
7. Smoke fase 10 dilaksanakan melalui `scripts/smoke_package.py`, bukan rangkaian perintah terpisah
   di `SMOKE_COMMANDS`, agar pemeriksaan isi ZIP dan eksekusi dari nol berada pada satu skrip yang
   dapat diuji.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| Gate gagal G8 setelah versi dinaikkan menjadi `1.0.0` | Regex G8 hanya menerima judul `## [0.<NN>.0]` | Menambah konstanta `FINAL_PHASE` dan `FINAL_VERSION`; G8 menerima `## [1.0.0]` pada fase penutup |
| Gate fase 10 gagal G6 pada Bagian A karena smoke belum didefinisikan | `SMOKE_COMMANDS` hanya memuat fase 0-9 | Smoke Bagian A memakai `pack_source.py --list`, lalu diganti smoke paket utuh pada Bagian B |
| Skill `laporan-akademik-id` belum terpasang saat fase dimulai | Skill belum tersedia di mesin kerja | User memasang skill; `SKILL.md` dan `references/contoh-kalimat.md` dibaca sebelum menulis laporan |
| Nama atau NPM anggota tidak boleh dikarang | Identitas hanya ada pada `config/group.toml` | Sampul membaca `config/group.toml`; kolom kelas tidak tersedia dan ditulis `PERLU DIISI USER` |
| Dua diagram laporan belum ada berkasnya | Diagram topologi dan urutan pesan belum pernah dibuat | Keduanya ditulis sebagai placeholder tiga baris berisi instruksi pembuatan dan penyimpanan |
| `README.md` masih menyebut "Fase 0 selesai" | README ditulis pada fase 0 dan tidak diperbarui | Ditulis ulang dari kondisi repo Fase 9 |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. Dua diagram pada laporan (Gambar 3.1 topologi dan Gambar 3.3 urutan pesan) serta logo universitas
   masih berupa placeholder dan harus diisi user sebelum laporan dikumpulkan.
2. Kolom kelas pada sampul diisi `PERLU DIISI USER` karena `config/group.toml` tidak memuat kelas.
3. Tanggal akses tautan pada daftar pustaka belum tercatat di `ASSETS.md`; rujukan buku untuk rumus
   speedup dan efficiency masih ditandai `PERLU DIISI USER`.
4. Laporan DOCX tidak ikut commit karena `reports/` di-ignore. Berkas harus dibangun ulang dengan
   `python scripts/build_report.py` setelah repo di-clone.
5. E7 mengenai ukuran chunk tidak dijalankan sehingga pengaruh ukuran chunk terhadap overhead
   jaringan belum terukur.
6. Seluruh pengukuran dilakukan pada sepuluh node virtual di satu laptop (ADR-015) dan memakai
   dataset sintetis, bukan korpus Silesia.

## 11. Catatan serah-terima ke fase berikutnya
1. Tidak ada fase berikutnya. Tag `phase-10-done` dan `v1.0.0` menutup rangkaian fase 0 sampai 10.
2. Bila laporan diserahkan, jalankan `python scripts/build_report.py`, isi dua diagram dan logo,
   isi kolom kelas, lalu lengkapi tanggal akses daftar pustaka.
3. Bila rekaman video dibuat, ikuti `docs/DEMO_SCRIPT.md` bagian 1 sampai 3 dan pastikan kalimat
   "sepuluh node virtual pada satu laptop" diucapkan.
4. Paket sumber dibuat dengan `python scripts/pack_source.py` dan diperiksa dengan
   `python scripts/smoke_package.py`.
5. Angka laporan hanya boleh diperbarui bila `results/summary.csv` berubah melalui eksperimen baru.

## 12. Commit
Bagian A: `880bde4` (merge `c87a65b`), tanpa tag.
Bagian B: `<isi setelah commit>`  Tag: `phase-10-done` dan `v1.0.0`
