# PHASE-10 — Dokumentasi, laporan, paket pengumpulan

- Branch: phase/10-final
- Mulai / selesai: 2026-11-22 / belum selesai (Bagian A selesai)
- Status: IN PROGRESS

## 1. Tujuan
Menyiapkan seluruh deliverable akhir sesuai PLAN.md fase 10: panduan kode (`docs/CODE_GUIDE.md`),
`README.md` final, dan `ASSETS.md` final. Pelaksanaan dibagi dua bagian atas instruksi user
2026-11-22: Bagian A mengerjakan P10-T1 dan P10-T4; Bagian B (laporan DOCX, naskah video, uji
clone, ZIP) menyusul.

## 2. Ringkasan hasil
`docs/CODE_GUIDE.md` disusun dari pembacaan 40 berkas `src/pcomp` (5.712 baris), 6 skrip
`scripts/` (1.912 baris), dan struktur test (34 berkas unit, 9 berkas integration). Isinya
mencakup peta direktori, penjelasan setiap modul beserta class dan fungsi penting, lima alur
pemanggilan, daftar berkas keluaran, dan cara menjalankan setiap perintah. `README.md` ditulis
ulang dari status "Fase 0 selesai" menjadi status proyek sampai Fase 9 lengkap dengan setup,
tabel perintah, struktur repo, langkah 10 node virtual, serta perintah test dan gate.
`ASSETS.md` diisi dari data nyata: dataset sintetis 2048 MiB (delapan berkas, seed 20261122,
SHA-256 per berkas), tujuh grafik `results/figures/`, empat tangkapan layar bukti, versi pustaka,
dan tabel formula. Tautan Silesia/Canterbury serta rujukan buku tetap ditandai belum terverifikasi
sesuai aturan. Gate penuh dijalankan setelah dokumen selesai.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P10-T1 | `docs/CODE_GUIDE.md` | DONE | 40 berkas sumber dibaca; modul, class, fungsi, alur, dan perintah dijelaskan |
| P10-T4 | `README.md` final dan `ASSETS.md` final | DONE | README ditulis ulang; ASSETS diisi dari `data/bench/dataset.json`, `results/figures/`, dan `reports/img/` |
| P10-T2 | Draf laporan BAB I-IV + Kesimpulan (DOCX) | TODO | Bagian B |
| P10-T3 | Naskah video demo maks 5 menit | TODO | Bagian B |
| P10-T5 | Uji reproduksi clone bersih | TODO | Bagian B |
| P10-T6 | ZIP sumber dan pemeriksaan isi | TODO | Bagian B |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `docs/CODE_GUIDE.md` | add | P10-T1 |
| `README.md` | mod | P10-T4: status, setup, perintah, struktur, 10 node, test |
| `ASSETS.md` | mod | P10-T4: isi data nyata, tandai yang belum terverifikasi |
| `scripts/gate.py` | mod | Smoke fase 10 Bagian A: `pack_source.py --list` wajib memuat `docs/CODE_GUIDE.md` |
| `CHANGELOG.md` | mod | Catatan fase 10 Bagian A |
| `PLAN.md` | mod | Status fase 10 menjadi IN PROGRESS |
| `docs/phase-logs/PHASE-10.md` | add | Catatan fase ini |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 0 | 236 | Tidak ada kode produk baru; hanya dokumentasi dan konfigurasi smoke gate |
| Integration | 0 | 19 | Sama seperti fase 9 |

Coverage: 84,46 % (ambang 80 %).

## 6. Hasil Verification Gate
Gate penuh dijalankan 2026-11-22 pukul 19:59, hasil `PASS (seluruh gate wajib lulus)`.

| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!`; `format=121 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 40 source files` |
| G3 Unit+cov | PASS | `236 passed, 20 deselected`, coverage `84.46 %` |
| G4 Integration | PASS | `19 passed, 237 deselected` |
| G5 Regresi | PASS | seluruh test fase lama dijalankan G3 dan G4 |
| G6 Smoke | PASS | `pack_source.py --list` -> `PACK OK: 756 berkas`, `docs/CODE_GUIDE.md` ditemukan |
| G7 Flaky x3 | PASS | 3 kali lulus |
| G8 Dokumen | PASS | CHANGELOG, phase log, dan status PLAN sinkron |
| G9 Repo | PASS | `750 file terlacak, tidak ada pelanggaran` |

## 7. Deviasi dari rencana
1. Pengerjaan fase 10 dibagi dua bagian atas instruksi user. Bagian A hanya P10-T1 dan P10-T4;
   P10-T2, P10-T3, P10-T5, P10-T6 belum dikerjakan dan tidak diberi tag.
2. PLAN.md fase 10 menetapkan smoke berupa ZIP yang dapat dijalankan dari nol. Smoke itu
   membutuhkan P10-T5 dan P10-T6 (Bagian B), sehingga Bagian A memakai smoke sementara
   `pack_source.py --list` yang memeriksa dokumen final masuk daftar paket. Smoke ZIP utuh wajib
   dipulihkan pada Bagian B.
3. Data kuantitatif pada README dan ASSETS diambil dari hasil Fase 9 yang sudah bertag
   `phase-09-done`; tidak ada eksperimen ulang pada fase ini.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| Gate fase 10 gagal G6 karena smoke belum didefinisikan | `SMOKE_COMMANDS` hanya memuat fase 0-9 | Menambah smoke Bagian A berbasis `pack_source.py --list`; smoke ZIP utuh ditunda ke Bagian B dan dicatat pada bagian 7 |
| `README.md` masih menyebut "Fase 0 selesai" | README ditulis pada fase 0 dan tidak diperbarui | Ditulis ulang dari kondisi repo Fase 9 |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. `docs/CODE_GUIDE.md` menjelaskan kode versi `0.09.0`. Bila kode berubah pada Bagian B, panduan
   wajib diperbarui.
2. Smoke fase 10 masih sementara dan belum menguji ZIP dari nol.
3. Laporan DOCX, naskah video, uji clone, dan paket ZIP belum ada.
4. `ASSETS.md` belum memuat rujukan buku/paper untuk formula dan belum memuat lisensi resmi
   dataset Silesia/Canterbury karena keduanya belum diunduh.

## 11. Catatan serah-terima ke fase berikutnya
1. Bagian B melanjutkan P10-T2, P10-T3, P10-T5, P10-T6 pada branch baru dari `main` setelah
   merge Bagian A.
2. Ganti smoke fase 10 di `scripts/gate.py` dengan smoke ZIP sesuai PLAN.md saat P10-T6 selesai.
3. Gunakan `results/summary.csv` dan `results/summary_agg.csv` sebagai satu-satunya sumber angka
   laporan; jangan memakai angka run bukti pada `reports/img/`.
4. Uji clone harus memakai perintah README yang sudah diperbarui, termasuk
   `pip install -e ".[dev,analysis]"`.
5. Tag `phase-10-done` dan `v1.0.0` belum dibuat; jangan memberi tag sebelum seluruh task fase 10
   selesai.

## 12. Commit
Hash: diisi setelah commit  Tag: belum ada (menunggu Bagian B)
