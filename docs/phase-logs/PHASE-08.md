# PHASE-08 — Kesiapan multi-node (bagian agent)

- Branch: phase/08-multinode-ready
- Mulai / selesai: 2026-11-21 / bagian agent selesai 2026-11-21, bagian user menunggu
- Status: IN PROGRESS (menunggu user)

## 1. Tujuan
10 node siap menjalankan sistem (PLAN.md Fase 8). Bagian agent mencakup P8-T1 `scripts/check_node.py`
(versi Python, psutil, jumlah core, koneksi ke Master, versi protokol), P8-T2
`scripts/launch_workers.py` (baca `config/nodes.toml`, mode cetak perintah dan mode ssh), P8-T3
`scripts/pack_source.py` (ZIP tanpa `data/`, `output/`, `.venv`, `.git`), P8-T4 finalisasi
`DEPLOYMENT.md` beserta template inventaris node dan checklist pra-eksperimen, P8-T5 opsional
`--data-mode local`, dan P8-T6 uji lokal 9 Worker dengan marker `slow`. Pengujian pada node fisik
dilakukan user dan hasilnya dicatat pada bagian Human checklist fase ini.

## 2. Ringkasan hasil
Seluruh skrip kesiapan multi-node tersedia dan diuji tanpa menyentuh protokol maupun perilaku
default. `check_node.py` memeriksa versi Python, psutil, versi paket dan `PROTOCOL_VERSION`, jumlah
core, RAM, serta keterjangkauan port Master. `launch_workers.py` membaca `config/nodes.toml`,
menolak inventaris yang masih berisi placeholder, lalu membangkitkan perintah ssh per Worker dengan
mode `--print`, `--ssh`, dan `--ssh --dry-run`. `pack_source.py` membuat arsip sumber yang bersih
dari `data/`, `output/`, `.venv`, `.git`, cache, dan `results/dev/`. `DEPLOYMENT.md` dilengkapi
template inventaris 10 node, langkah `pip install -e .`, contoh keluaran nyata, dan checklist pra-
eksperimen. Uji 9 Worker lokal (SL-9W-01) lulus. Seluruh pengujian pada node fisik belum dilakukan
dan menunggu hasil checklist user.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P8-T1 | `scripts/check_node.py` (versi Python, psutil, jumlah core, koneksi ke Master, versi protokol) | DONE | Tanpa mengirim pesan protokol (ADR-013); exit code 0/1/2 |
| P8-T2 | `scripts/launch_workers.py` (baca `config/nodes.toml`; mode cetak perintah dan mode ssh) | DONE | Menolak placeholder; `procs` per node menang atas `--procs` |
| P8-T3 | `scripts/pack_source.py` (ZIP tanpa `data/`, `output/`, `.venv`, `.git`) | DONE | Juga tanpa cache dan `results/dev/`; keluaran bawaan `dist/` |
| P8-T4 | Finalisasi `DEPLOYMENT.md`, template inventaris node, checklist pra-eksperimen | DONE | Inventaris 10 baris, `pip install -e .`, contoh keluaran nyata |
| P8-T5 | Opsional bila R1 terjadi: `--data-mode local` | DITUNDA | Menunggu bukti R1 dari dry-run node fisik (ADR-014) |
| P8-T6 | Uji lokal 9 Worker di satu mesin (marker `slow`) | DONE | SL-9W-01, `1 passed` |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `scripts/check_node.py` | add | P8-T1: pemeriksaan kesiapan node |
| `scripts/launch_workers.py` | add | P8-T2: pembangkit perintah Worker dari inventaris |
| `scripts/pack_source.py` | add | P8-T3: paket ZIP sumber |
| `tests/unit/test_check_node.py` | add | UT-NODE-01..04 |
| `tests/unit/test_launch_workers.py` | add | UT-LAUNCH-01..04 |
| `tests/unit/test_pack_source.py` | add | UT-PACK-01..03 |
| `tests/integration/test_slow_9_workers.py` | add | SL-9W-01 (marker `slow`) |
| `tests/conftest.py` | mod | Fixture `load_script` untuk memuat skrip sebagai modul |
| `DEPLOYMENT.md` | mod | P8-T4: inventaris 10 node, instalasi, jaringan, launching, checklist, troubleshooting, paket sumber |
| `scripts/gate.py` | mod | Smoke Fase 8 = `pytest -m slow` dengan penanda `1 passed` |
| `TESTING.md` | mod | Baris UT-NODE, UT-LAUNCH, UT-PACK |
| `DECISIONS.md` | mod | ADR-013 dan ADR-014 |
| `ARCHITECTURE.md` | mod | Bagian 11 mencatat `--data-mode local` belum tersedia |
| `CHANGELOG.md` | mod | Entri `[Unreleased]` bagian agent Fase 8 |
| `PLAN.md` | mod | Status Fase 8 `IN PROGRESS (menunggu user)`, `CURRENT PHASE` tetap 8 |
| `docs/phase-logs/PHASE-08.md` | add | Catatan fase ini |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 12 | 218 | UT-NODE-01..04, UT-LAUNCH-01..04, UT-PACK-01..03 |
| Integration | 1 | 19 | SL-9W-01 bertanda `slow` sehingga tidak ikut `pytest -m integration` |
| Slow | 1 | 1 | SL-9W-01: Master + 9 Worker lokal, `VERIFY OK`, `worker_stats` berisi 9 entri |

Coverage: 83.13% sampai 83.20% (bervariasi sedikit antar run karena cabang bergantung waktu;
nilai pada run terakhir tercatat di `reports/gate-latest.txt`).

## 6. Hasil Verification Gate
Dijalankan dengan `python scripts/gate.py` (penuh) pada 2026-11-21. Tabel di bawah dikutip dari run
`2026-11-21T10:22:43`; dua run penuh sebelumnya (`10:11:55` dan `10:17:45`) juga berakhir
`HASIL: PASS`, dan gate penuh dijalankan sekali lagi setelah suntingan dokumen terakhir sebelum
commit. Ringkasan run terakhir ada di `reports/gate-latest.txt`.

| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=111 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 39 source files` |
| G3 Unit+cov | PASS | `Required test coverage of 80% reached. Total coverage: 83.20% \| 218 passed, 20 deselected` |
| G4 Integration | PASS | `19 passed, 219 deselected in 52.50s` |
| G5 Regresi | PASS | `seluruh test fase lama ikut dijalankan oleh G3 dan G4` |
| G6 Smoke | PASS | `python.exe -m pytest -m slow -q -> rc=0: 1 passed, 237 deselected in 4.73s` |
| G7 Flaky x3 | PASS | `3 kali lulus` |
| G8 Dokumen | PASS | `CHANGELOG, phase log, dan status PLAN sinkron` |
| G9 Repo | PASS | `113 file terlacak, tidak ada pelanggaran` |

Keluaran smoke apa adanya (`python -m pytest -m slow -q` dari root repo):

```
1 passed, 237 deselected in 5.85s
```

Keluaran `check_node.py` dan `pack_source.py` pada mesin pengembangan (bukan node lab):

```
OK python: 3.14.4 (>= 3.11)
OK psutil: 7.2.2
OK paket: pcomp 0.07.0
OK protokol: PROTOCOL_VERSION=1
OK core: 4 core logis
OK ram: 7.7 GiB
CHECK NODE OK
```

```
berkas : 125
arsip  : D:\ziphive\dist\ziphive-source-0.07.0.zip
ukuran : 221.4 KiB
PACK OK
```

`python scripts/launch_workers.py --print` pada `config/nodes.toml` yang masih template berhenti
dengan `LAUNCH GAGAL: lengkapi config/nodes.toml dari inventaris DEPLOYMENT.md bagian 1` (exit 1),
sesuai rancangan.

## 7. Deviasi dari rencana
1. P8-T5 `--data-mode local` tidak dikerjakan. PLAN.md menandainya "opsional bila R1 terjadi",
   sedangkan R1 hanya dapat dinilai dari dry-run 10 node fisik yang belum ada, dan opsi itu
   menuntut perubahan format `TASK` pada PROTOCOL.md. Keputusan dicatat pada ADR-014 dan dievaluasi
   pada bagian user (Prompt 9B).
2. P8-T1 tidak mengirim pesan protokol untuk membaca versi Master. Protokol tidak punya pesan
   khusus versi sebelum REGISTER, dan mengirim REGISTER akan mengubah state Master. Skrip hanya
   menguji keterjangkauan TCP dan melaporkan `PROTOCOL_VERSION` lokal (ADR-013).
3. SL-9W-01 hanya diberi marker `slow`, tidak `integration`, agar gate G4 dan G7 tidak menjalankan
   ulang 9 proses pada setiap percobaan; PLAN.md sendiri menetapkan `pytest -m slow` sebagai smoke,
   sehingga uji ini tetap dijalankan pada G6 gate penuh.
4. Dua ekspektasi test diperbaiki saat fase berjalan: `load_nodes` untuk berkas yang tidak ada
   diharapkan `FileNotFoundError` (bukan `ValueError`), dan helper test `write_toml` memakai nama
   berkas berbeda agar dua skenario tidak saling menimpa. Implementasi tidak dilonggarkan.
5. `DEPLOYMENT.md` tidak menambah bagian baru di tengah agar rujukan "DEPLOYMENT.md bagian 6"
   pada `PROMPTS.md` tetap menunjuk checklist pra-eksperimen; bagian paket sumber ditaruh di
   bagian 8.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| `LAUNCH GAGAL` pada `--ssh --dry-run` di test | Helper test menulis dua skenario ke berkas yang sama sehingga inventaris lengkap tertimpa template | Helper test diberi parameter nama berkas |
| `FileNotFoundError` lolos dari `pytest.raises(ValueError)` | `load_nodes` memakai `FileNotFoundError` untuk berkas yang tidak ada (konsisten dengan `pcomp.config.load_toml`) | Ekspektasi test diubah ke `FileNotFoundError`; isi TOML rusak tetap `ValueError` |
| G1 E501 pada empat berkas baru | Baris `argparse`, kondisi, dan tanda tangan test terlalu panjang | Baris dipecah, `ruff format` dijalankan |
| `DEPLOYMENT.md` menyuruh `pip install -r requirements*.txt` tanpa memasang paket | `requirements*.txt` tidak memasang `pcomp`, sehingga `python -m pcomp.worker` gagal | Langkah 3 menambahkan `python -m pip install -e .` dan troubleshooting menambahkan gejala `ModuleNotFoundError: pcomp` |

## 9. Back-fix (bug fase lama)
Tidak ada. Skrip fase ini tidak menyentuh `src/pcomp`, protokol, maupun perilaku default.

## 10. Keterbatasan dan utang teknis
1. Tidak ada satu pun klaim pengujian pada 10 node fisik; seluruh verifikasi bagian agent berjalan
   di satu mesin pengembangan. Hasil node fisik wajib dicatat pada bagian 13 sebelum Fase 8 selesai.
2. `check_node.py` hanya membandingkan versi protokol secara lokal; kecocokan versi antar node masih
   bergantung pada penolakan REGISTER di Master.
3. `launch_workers.py` menjalankan ssh secara berurutan dan tidak melacak proses yang sudah berjalan;
   Worker yang mati perlu dijalankan ulang manual.
4. Mode `--data-mode local` (P8-T5) belum ada; bila dry-run membuktikan R1, opsi ini menjadi
   pekerjaan tambahan yang menaikkan `PROTOCOL_VERSION`.
5. `pack_source.py` menyertakan seluruh `results/` kecuali `results/dev/`; bila hasil eksperimen
   membesar, arsip pengumpulan perlu disaring manual agar tidak melebihi batas ukuran pengumpulan.
6. `scripts/` tidak termasuk cakupan `mypy` (konfigurasi `files = ["src"]`), sehingga skrip hanya
   diperiksa `ruff` dan unit test.

## 11. Catatan serah-terima ke fase berikutnya
1. Fase 8 baru selesai setelah user mengirim inventaris, keluaran `check_node.py` tiap node, dan log
   dry-run 10 node (Prompt 9B). Setelah itu: isi DEPLOYMENT.md bagian 1 dan bagian 13 fase ini,
   evaluasi R1, lalu putuskan status Fase 8 dan `CURRENT PHASE`.
2. Bila dry-run menunjukkan bandwidth Master menjadi bottleneck (R1), P8-T5 `--data-mode local`
   perlu ADR baru dan kenaikan `PROTOCOL_VERSION`; jangan ditambahkan diam-diam sebagai perilaku
   default.
3. Eksperimen resmi (Fase 9) hanya boleh memakai algoritma nyata; `results/dev/` dari algoritma
   `sim` tidak boleh dipakai dan sudah dikecualikan dari arsip sumber.
4. Versi paket masih `0.07.0` karena bagian agent bukan commit akhir fase; kenaikan ke `0.08.0`
   dilakukan bersama `phase-08-done`.

## 12. Commit
Commit bagian agent: `feat(phase-08): add node checks, launch scripts, packaging, deployment guide`.
Hash dan tag bagian agent (`phase-08a-done`): lihat `git log --oneline` dan `git tag --list`.
Tag `phase-08-done` baru dibuat pada bagian user setelah seluruh node lulus.

## 13. Human checklist (diisi dari hasil user)
Menunggu hasil checklist user sesuai PLAN.md Fase 8 bagian User. Data yang tidak dikirim user
ditulis "TIDAK ADA DATA".

| Item | Status | Catatan |
|---|---|---|
| Python dan dependensi terpasang di 9 Worker | TIDAK ADA DATA | menunggu laporan user |
| `check_node.py` dijalankan di 10 node | TIDAK ADA DATA | menunggu keluaran per node |
| Inventaris node (host, IP, CPU, core, RAM, OS) | TIDAK ADA DATA | menunggu isian user |
| Dry-run dataset kecil di 10 node | TIDAK ADA DATA | menunggu log dan hasil `VERIFY` |
| Evaluasi risiko R1 | TIDAK ADA DATA | dinilai dari log dry-run |
