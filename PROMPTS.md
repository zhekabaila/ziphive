# PROMPTS.md - Prompt Berurutan untuk AI Agent (Proyek ZipHive)

Nama proyek: **ZipHive** (zip = kompresi, hive = kawanan Worker dengan satu Master). Nama paket Python tetap `pcomp` agar sesuai seluruh dokumen. Alternatif: PackGrid, ZipSwarm.

## Cara pakai
1. Buat folder repo `ziphive/`, salin 14 file dokumen (termasuk PROMPTS.md ini) ke dalamnya. Buka AI agent di folder itu.
2. Tempel prompt UTUH sesuai urutan. Satu prompt satu sesi. Jangan memendekkan blok KONTEKS WAJIB, itu yang membuat agent membaca dokumen dulu dan tidak keluar dari rencana.
3. Setelah tiap fase di-commit, disarankan jalankan Prompt U3 (audit) di sesi baru sebelum lanjut.
4. Agent selalu berhenti di akhir fase. Fase berikutnya hanya dimulai setelah Anda menempel prompt berikutnya.
5. Fase HUMAN-REQUIRED (8 dan 9) membutuhkan Anda. Urutannya: 9A, checklist node, 9B, langkah manual eksperimen, Prompt 10.

## Urutan
| Urutan | Prompt | Pelaku |
|---|---|---|
| 1 | Prompt 0 Orientasi | Agent (baca saja) |
| 2 | Prompt 1 sampai 8 (Fase 0 sampai 7) | Agent |
| 3 | Prompt 9A (Fase 8 bagian agent) | Agent |
| 4 | Checklist node fisik | Anda |
| 5 | Prompt 9B (catat hasil) | Agent |
| 6 | Langkah manual eksperimen resmi | Anda |
| 7 | Prompt 10 (Fase 9) | Agent |
| 8 | Prompt 11A lalu 11B (Fase 10) | Agent |
| 9 | Prompt U6 audit final | Agent |
| kapan saja | U1 lanjut, U2 gate gagal, U3 audit, U4 back-fix, U5 usulan desain | Agent |


---

## PROMPT 0 - Orientasi (tanpa mengubah file)
Kapan: Sekali, di awal, setelah semua dokumen ada di repo.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: SESI ORIENTASI, TANPA MENGUBAH FILE
1. Baca SEMUA dokumen: AGENTS.md, PLAN.md, SDLC.md, ARCHITECTURE.md, FLOW.md, PROTOCOL.md, TESTING.md, EXPERIMENTS.md, DEPLOYMENT.md, ASSETS.md, SUBMISSION.md, DECISIONS.md, CHANGELOG.md, docs/phase-logs/_TEMPLATE.md.
2. Jangan membuat, mengubah, atau menghapus file. Jangan menjalankan git commit.
3. Balas dengan: (a) ringkasan proyek dengan kata-katamu sendiri (maks 10 baris); (b) 11 fase beserta pelakunya; (c) aturan keras paling penting dari AGENTS.md; (d) isi Verification Gate G1 sampai G9; (e) alur branch, commit, merge, tag; (f) daftar ketidakkonsistenan, celah, atau hal ambigu antar dokumen (sebut nama file dan bagian), tulis "tidak ada" bila memang tidak ada; (g) pertanyaan yang menghalangi pekerjaan, bila ada.
4. Berhenti. Tunggu perintah "lanjut ke Fase 0".
```


---

## PROMPT 1 - Fase 0: Bootstrap
Kapan: Setelah Prompt 0 dijawab dan Anda setuju.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 0 - Bootstrap repo dan tooling
Dokumen WAJIB dibaca untuk fase ini: AGENTS.md; PLAN.md (Fase 0 dan bagian Default dan asumsi); SDLC.md (seluruh, terutama bagian 4 dan 5); TESTING.md bagian 1 sampai 3; ARCHITECTURE.md bagian 10; PROTOCOL.md (hanya untuk nilai PROTOCOL_VERSION = 1)
Lingkup: HANYA task P0-T1 sampai P0-T7 pada bagian "FASE 0" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: protokol, chunker, compressor, Master, Worker, atau logika aplikasi apa pun.

INSTRUKSI KHUSUS FASE INI
- Dokumen perencanaan sudah ada di root. Ikut di-commit pada fase ini.
- Buat `scripts/gate.py` lebih dulu, lalu pakai untuk memverifikasi fase ini. Gate mengikuti tabel SDLC.md bagian 4 dan menulis reports/gate-latest.txt.
- `config/group.toml` hanya berisi placeholder dan `project_name = "ZipHive"`. Jangan mengisi nama anggota atau NPM sendiri.
- Jalankan `git init` dan buat branch main dulu bila repo belum ada, lalu commit dokumen perencanaan sebagai commit awal sebelum membuat branch phase/00-bootstrap.
- Setelah selesai, ingatkan saya mengisi config/group.toml.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: tidak ada fase sebelumnya. Pastikan folder berisi 14 dokumen perencanaan (cek dengan `ls`). scripts/gate.py belum ada, dibuat di fase ini. Jika ada dokumen hilang, berhenti dan lapor.
2. Buat branch `phase/00-bootstrap`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-00.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `python -m pcomp --version` mencetak versi dan `python scripts/gate.py` seluruhnya PASS. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-00.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 1. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-00-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 2 - Fase 1: Protokol dan infrastruktur inti
Kapan: Setelah Fase 0 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 1 - Protokol dan infrastruktur inti
Dokumen WAJIB dibaca untuk fase ini: PROTOCOL.md (seluruh, ini kontrak format); ARCHITECTURE.md bagian 10; TESTING.md bagian 3 sampai 5; AGENTS.md aturan 8 sampai 10
Lingkup: HANYA task P1-T1 sampai P1-T4 pada bagian "FASE 1" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: Master, Worker, chunker, compressor, scheduler, dan apa pun di luar protocol, net, config, logging_setup, metrics/events beserta test-nya.

INSTRUKSI KHUSUS FASE INI
Implementasikan frame TEPAT sesuai PROTOCOL.md bagian 1 (header !I 4 byte, panjang payload !Q 8 byte, batas 64 KiB dan 64 MiB). Jangan mengubah format. Jika menurutmu ada masalah di PROTOCOL.md, jangan diubah sendiri, tulis usulan dan tanyakan ke saya.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-00-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/01-core-protocol`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-01.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `pytest -m integration -k echo` lulus. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-01.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 2. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-01-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 3 - Fase 2: Kompresi, task decomposition, baseline sequential
Kapan: Setelah Fase 1 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 2 - Mesin kompresi, task decomposition, baseline sequential
Dokumen WAJIB dibaca untuk fase ini: ARCHITECTURE.md bagian 4, 5, 8; EXPERIMENTS.md bagian 1 dan 7; ASSETS.md; TESTING.md bagian 3 dan 4
Lingkup: HANYA task P2-T1 sampai P2-T6 pada bagian "FASE 2" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: jaringan, Master, Worker, multiprocessing (itu Fase 3 dan 4).

INSTRUKSI KHUSUS FASE INI
- `tools/download_corpus.py` boleh dibuat, tetapi JANGAN dijalankan otomatis dan test TIDAK boleh memakai internet.
- Jangan mengarang SHA-256 atau tanggal akses di ASSETS.md. Kolom itu diisi hanya dari unduhan nyata, kalau belum ada tulis "diisi user".
- Algoritma `sim` hanya untuk test dan harus tercatat di metadata keluaran.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-01-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/02-compression-sequential`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-02.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: jalankan make_dataset (20 MB sintetis), sequential, lalu verify; harus tercetak `VERIFY OK`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-02.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 3. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-02-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 4 - Fase 3: Local parallel
Kapan: Setelah Fase 2 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 3 - Local parallel
Dokumen WAJIB dibaca untuk fase ini: ARCHITECTURE.md bagian 3 dan 5; AGENTS.md aturan 8 (spawn-safe); TESTING.md; PLAN.md Fase 3
Lingkup: HANYA task P3-T1 sampai P3-T3 pada bagian "FASE 3" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: socket atau jaringan, Master, Worker, scheduler.

INSTRUKSI KHUSUS FASE INI
Rancang fungsi kompresi satu task (`compress_task`) di modul netral (mis. compressor.py) agar dipakai ulang oleh Worker di Fase 4. Catat letak dan alasannya di phase log. Wajib ada test dengan `multiprocessing.get_context("spawn")`.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-02-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/03-local-parallel`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-03.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: bandingkan waktu sequential dan `--procs 4` pada dataset sintetis, keduanya harus `VERIFY OK`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-03.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 4. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-03-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 5 - Fase 4: Master-Worker inti
Kapan: Setelah Fase 3 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 4 - Master-Worker inti
Dokumen WAJIB dibaca untuk fase ini: ARCHITECTURE.md bagian 2 sampai 5 dan 8 sampai 10; PROTOCOL.md (seluruh); FLOW.md bagian 1 dan 3; TESTING.md matriks IT-DIST
Lingkup: HANYA task P4-T1 sampai P4-T6 pada bagian "FASE 4" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: monitor heartbeat timeout, requeue, retry, static scheduler, injeksi kegagalan, sampler psutil (itu Fase 5 sampai 7). Dispatch cukup FIFO sederhana.

INSTRUKSI KHUSUS FASE INI
Pakai ulang modul protocol, net, events, compressor, manifest yang sudah ada, jangan menulis ulang. Integration test memakai port bebas, dataset kecil atau algoritma `sim`, dan selesai di bawah 60 detik per test. Setelah test, tidak boleh ada proses yatim.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-03-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/04-master-worker-core`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-04.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `python scripts/e2e_local.py --workers 3` mencetak `E2E OK`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-04.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 5. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-04-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 6 - Fase 5: Dynamic load balancing
Kapan: Setelah Fase 4 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 5 - Dynamic load balancing
Dokumen WAJIB dibaca untuk fase ini: ARCHITECTURE.md bagian 6; DECISIONS.md ADR-003; EXPERIMENTS.md E4 dan bagian 3 (imbalance factor); PROTOCOL.md bagian 3 (credit)
Lingkup: HANYA task P5-T1 sampai P5-T5 pada bagian "FASE 5" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: heartbeat monitor, requeue, retry (Fase 6), sampler psutil (Fase 7).

INSTRUKSI KHUSUS FASE INI
Perbandingan static vs dynamic di test harus deterministik (algoritma `sim`, margin toleransi), bukan perbandingan waktu nyata yang rapuh. `sim` tidak boleh dipakai untuk eksperimen resmi.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-04-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/05-load-balancing`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-05.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: jalankan e2e dengan scheduler static lalu dynamic, cetak ringkasan perbandingan. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-05.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 6. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-05-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 7 - Fase 6: Fault tolerance
Kapan: Setelah Fase 5 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 6 - Fault tolerance
Dokumen WAJIB dibaca untuk fase ini: ARCHITECTURE.md bagian 4 dan 7; PROTOCOL.md bagian 3 dan 4; FLOW.md bagian 2 dan 3; EXPERIMENTS.md bagian 3 (detection latency, Recovery Time); TESTING.md matriks IT-FT
Lingkup: HANYA task P6-T1 sampai P6-T7 pada bagian "FASE 6" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: sampler psutil, harness benchmark, skrip deployment node.

INSTRUKSI KHUSUS FASE INI
- Monitor harus bisa diuji dengan jam palsu (inject clock) agar unit test tidak menunggu 6 detik.
- Nama event persis: worker_dead, task_requeued, task_failed, worker_rejoined, late_or_duplicate, worker_exit_injected.
- Jalankan integration test fault tolerance berulang (G7) untuk memastikan tidak flaky.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-05-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/06-fault-tolerance`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-06.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: e2e dengan `--fail-after-tasks 3` pada satu Worker: hasil `E2E OK` dan ada event `worker_dead`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-06.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 7. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-06-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 8 - Fase 7: Metrik dan harness benchmark
Kapan: Setelah Fase 6 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 7 - Metrik dan harness benchmark
Dokumen WAJIB dibaca untuk fase ini: EXPERIMENTS.md (seluruh); ARCHITECTURE.md bagian 9; TESTING.md IT-BENCH; PLAN.md Fase 7
Lingkup: HANYA task P7-T1 sampai P7-T5 pada bagian "FASE 7" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: menjalankan eksperimen resmi, menulis analisis hasil, skrip deployment.

INSTRUKSI KHUSUS FASE INI
- Rumus HARUS sama dengan EXPERIMENTS.md bagian 3, nama kolom CSV persis sesuai bagian 4.
- Hasil dari algoritma `sim` disimpan di `results/dev/` (tambahkan ke .gitignore dan catat di CHANGELOG), tidak masuk `results/raw/`. Metadata `algo=sim` wajib tercatat agar validator Fase 9 dapat menolaknya.
- Matplotlib memakai backend Agg.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-06-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/07-metrics-bench`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-07.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `python -m pcomp.bench.runner --exp E6 --local --workers 1,2 --reps 2 --algo sim`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-07.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 8. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-07-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 9A - Fase 8: Kesiapan multi-node (bagian agent)
Kapan: Setelah Fase 7 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 8 - Kesiapan multi-node, bagian agent
Dokumen WAJIB dibaca untuk fase ini: DEPLOYMENT.md (seluruh); ARCHITECTURE.md bagian 11; PLAN.md risiko R1 sampai R3 dan Fase 8; SUBMISSION.md bagian 1
Lingkup: HANYA task P8-T1 sampai P8-T6 pada bagian "FASE 8" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: mengubah protokol atau algoritma inti; mengubah perilaku default. P8-T5 (`--data-mode local`) opsional, kerjakan hanya sebagai opsi tambahan.

INSTRUKSI KHUSUS FASE INI
Jangan mengklaim node fisik sudah teruji. Fase ini BELUM selesai sebelum saya mengirim hasil checklist (Prompt 9B).

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-07-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/08-multinode-ready`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-08.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `pytest -m slow` (9 Worker lokal) lulus. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-08.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md Fase 8 menjadi "IN PROGRESS (menunggu user)" dan CURRENT PHASE tetap 8. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-08a-done (pengecualian fase HUMAN-REQUIRED, lihat SDLC.md bagian 8). Jangan git push.
9. Berikan "Checklist untuk user" (salin bagian User dari PLAN.md Fase 8, lengkap dengan perintah persis). Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 9B - Fase 8: Hasil checklist user
Kapan: Setelah Anda menjalankan checklist di node fisik. Isi tiga bagian [TEMPEL].

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 8 BAGIAN 2, MENCATAT HASIL KESIAPAN NODE
Dokumen WAJIB dibaca: PLAN.md Fase 8, DEPLOYMENT.md, docs/phase-logs/PHASE-08.md.
Data dari saya (sumber kebenaran, jangan diubah atau ditambah):
[TEMPEL: inventaris node: host, IP, OS, CPU/core, RAM, versi Python]
[TEMPEL: keluaran check_node.py tiap node]
[TEMPEL: log dry-run 10 node dengan dataset kecil, termasuk hasil VERIFY]
LANGKAH
1. Pastikan tag phase-08a-done ada dan main bersih.
2. Isi inventaris di DEPLOYMENT.md dan bagian "Human checklist" di PHASE-08.md hanya dari data di atas. Data yang tidak saya berikan ditulis "TIDAK ADA DATA".
3. Analisis log: node yang gagal, penyebab, dan perbaikan. Jika perlu perbaikan kode, ikuti SDLC.md (test-first, gate penuh, commit `fix(phase-08)`), catat di CHANGELOG dan bagian Back-fix.
4. Evaluasi risiko R1: apakah ada tanda bandwidth Master jadi bottleneck pada dry-run? Jawab berdasar log, jangan menebak.
5. Jika semua node OK dan dry-run VERIFY OK: set Fase 8 DONE dan CURRENT PHASE = 9, jalankan `python scripts/gate.py`, commit, merge, tag phase-08-done, tanpa push. Jika belum OK: lapor apa yang kurang dan BERHENTI.
6. Laporan akhir sesuai AGENTS.md bagian 8.
```


---

## LANGKAH MANUAL USER - Eksperimen resmi (sebelum Prompt 10)
Kapan: Dikerjakan oleh Anda di 10 node. Agent tidak boleh melakukan ini.

```text
Ikuti EXPERIMENTS.md bagian 1, 2, dan 5 dan DEPLOYMENT.md bagian 6.
1. Kunci parameter (dataset, algoritma, chunk size, --repeat) sehingga T sequential 2 sampai 10 menit. Catat di docs/phase-logs/PHASE-09.md.
2. Jalankan E1 sampai E6 (E7 opsional), masing-masing 3 ulangan, jeda 30 detik, hanya algoritma asli (bukan sim).
3. Setiap run: jalankan tools/verify.py, pastikan metrics.json dan events.jsonl ada.
4. Salin seluruh hasil ke results/raw/<exp>/<run_id>/ di repo. Catat foto atau tangkapan layar bukti 10 node untuk laporan dan video.
5. Jangan menyunting file hasil secara manual.
```


---

## PROMPT 10 - Fase 9: Validasi hasil dan analisis
Kapan: Setelah results/raw/ berisi data eksperimen nyata.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 9 - Eksperimen resmi: validasi dan analisis
Dokumen WAJIB dibaca untuk fase ini: EXPERIMENTS.md (seluruh); PLAN.md Fase 9; SUBMISSION.md bagian 2; TESTING.md; docs/phase-logs/PHASE-08.md
Lingkup: HANYA task P9-T1 sampai P9-T3 pada bagian "FASE 9" di PLAN.md. Salin tujuan, task, test, smoke, dan pesan commit dari sana apa adanya.
DILARANG di fase ini: menjalankan atau membuat data eksperimen, mengubah file di results/raw/, memakai data algo=sim.

INSTRUKSI KHUSUS FASE INI
- Data eksperimen sudah saya salin ke results/raw/. Jika data kurang, rusak, atau tidak lengkap 3 ulangan, laporkan persis apa yang kurang dan berhenti. Jangan melengkapi dengan angka buatan.
- Setiap angka di docs/ANALYSIS.md harus menyebut file sumber atau baris CSV-nya.
- Hasil yang di bawah ideal (speedup rendah, efficiency turun) dibahas apa adanya. Penyebab hanya boleh ditulis sebagai fakta bila didukung data (mis. CPU Worker rendah dan throughput Master jenuh). Selain itu tulis sebagai hipotesis.
- Hapus atau jangan masukkan data simulasi dari summary dan grafik.

LANGKAH (ikuti SDLC.md bagian 1)
1. Definition of Ready: fase sebelumnya DONE dan bertag phase-08-done, branch main bersih, `python scripts/gate.py --quick` hijau. Jika tidak, berhenti dan lapor.
2. Buat branch `phase/09-official-results`. Salin docs/phase-logs/_TEMPLATE.md menjadi docs/phase-logs/PHASE-09.md, isi tujuan dan daftar task. Ubah status fase di PLAN.md menjadi IN PROGRESS.
3. Tampilkan rencana kerja (maks 15 baris): task, test yang akan ditulis (pakai ID dari TESTING.md bagian 4), file yang akan dibuat. Lanjut langsung kecuali ada konflik dengan dokumen.
4. Test-first: tulis test, jalankan, tunjukkan hasil merah. Lalu implementasi sampai hijau.
5. Jalankan `python scripts/gate.py` (G1 sampai G9). Kutip tabel hasilnya apa adanya. Jika gagal: perbaiki akar masalah di kode (bukan melemahkan test), ulangi gate PENUH. Gagal 3 kali pada masalah yang sama: berhenti dan lapor.
6. Smoke test: `python -m pcomp.tools.validate_results results/raw` mencetak `RESULTS VALID`. Kutip keluarannya.
7. Dokumentasi: lengkapi PHASE-09.md (semua bagian, tulis "Tidak ada" bila kosong), CHANGELOG.md, status PLAN.md menjadi DONE dan CURRENT PHASE menjadi 10. Bila desain berubah: perbarui ARCHITECTURE/PROTOCOL dan tambah entri DECISIONS (perubahan besar perlu persetujuan saya dulu).
8. Commit sesuai format SDLC.md bagian 5 (stage file secara eksplisit, cek `git diff --staged --stat`), merge --no-ff ke main, buat tag phase-09-done. Jangan git push.
9. Laporan akhir sesuai AGENTS.md bagian 8 (maks 15 baris), lalu BERHENTI. Jangan memulai fase berikutnya.
```


---

## PROMPT 11A - Fase 10 bagian A: Code guide, README, ASSETS
Kapan: Setelah Fase 9 selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 10 BAGIAN A (task P10-T1 dan P10-T4)
Dokumen WAJIB dibaca: PLAN.md Fase 10, SUBMISSION.md, ASSETS.md, seluruh kode di src/pcomp, ARCHITECTURE.md, PROTOCOL.md.
LANGKAH
1. Definition of Ready: tag phase-09-done ada, main bersih, gate hijau. Buat branch phase/10-final dan docs/phase-logs/PHASE-10.md.
2. docs/CODE_GUIDE.md: struktur direktori dan penjelasan setiap modul, class, dan fungsi penting berdasarkan kode NYATA (buka tiap file, jangan menebak). Sertakan alur pemanggilan antar modul dan cara menjalankan tiap perintah.
3. README.md final (setup, perintah, struktur, cara menjalankan di 10 node, cara menjalankan test).
4. ASSETS.md final: isi tanggal akses, ukuran, dan SHA-256 hanya dari data nyata. Tautan yang belum diverifikasi dibiarkan bertanda "PERLU DIVERIFIKASI USER". Rujukan buku atau paper hanya yang dapat diverifikasi, sisanya "PERLU DIISI USER".
5. Gate penuh, commit atomik `docs(phase-10): add code guide, readme, final assets`, merge ke main. JANGAN beri tag phase-10-done atau v1.0.0 dulu.
6. Laporan akhir (AGENTS.md bagian 8) dan berhenti.
```


---

## PROMPT 11B - Fase 10 bagian B: Laporan, naskah video, paket akhir
Kapan: Setelah 11A selesai.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: FASE 10 BAGIAN B (task P10-T2, P10-T3, P10-T5, P10-T6)
Dokumen WAJIB dibaca: SUBMISSION.md (seluruh), docs/ANALYSIS.md, results/summary.csv, ASSETS.md, EXPERIMENTS.md, ARCHITECTURE.md, FLOW.md, PROTOCOL.md, DEPLOYMENT.md, docs/CODE_GUIDE.md, config/group.toml, serta skill laporan-akademik-id (baca SKILL.md-nya dulu).
LANGKAH
1. Laporan DOCX memakai skill laporan-akademik-id: BAB I Pendahuluan, BAB II Studi Pustaka, BAB III Metodologi, BAB IV Hasil dan Pembahasan, Kesimpulan, sesuai tabel SUBMISSION.md bagian 2. Bahasa formal mahasiswa, tanpa simbol khas AI.
2. Aturan data: angka, tabel, dan grafik hanya dari results/summary.csv dan docs/ANALYSIS.md. Dilarang menambah angka baru. Bagian yang datanya tidak ada ditulis "PERLU DIISI USER". Identitas kelompok dari config/group.toml.
3. Setiap gambar diberi nomor, keterangan, dan placeholder beserta instruksi pengambilan gambar (foto 10 node, terminal Master dan 9 Worker, grafik hasil, bukti Worker dimatikan lalu pulih).
4. Naskah video demo (maks 5 menit) dan checklist rekaman di docs/DEMO_SCRIPT.md sesuai SUBMISSION.md bagian 3.
5. Uji reproduksi: clone repo ke folder sementara, setup dari README, jalankan `python scripts/gate.py`. Kutip hasilnya.
6. `python scripts/pack_source.py`, tampilkan daftar isi ZIP dan konfirmasi tidak ada data/, output/, .venv, .git.
7. Gate penuh, update CHANGELOG (versi 1.0.0), PHASE-10.md lengkap, commit, merge ke main, tag phase-10-done dan v1.0.0. Jangan push.
8. Laporan akhir dan daftar hal yang masih harus saya kerjakan manual (gambar, video, nama anggota).
```


---

## PROMPT U1 - Lanjut setelah sesi terputus
Kapan: Dipakai kapan saja saat membuka sesi agent baru di tengah fase.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: LANJUTKAN PEKERJAAN YANG TERPUTUS
1. Baca CURRENT PHASE di PLAN.md, phase log fase itu, CHANGELOG.md bagian [Unreleased]. Jalankan `git status`, `git diff --stat`, `git log --oneline -15`, `python scripts/gate.py --quick`.
2. Laporkan: task yang sudah selesai, yang belum, perubahan yang belum ter-commit, status test. Semua berdasar bukti perintah.
3. Jangan membuang, menimpa, atau mengulang pekerjaan yang sudah ada. Lanjutkan dari task pertama yang belum selesai mengikuti SDLC.md bagian 1 mulai dari langkah yang sesuai.
4. Selesaikan fase sesuai SDLC.md (gate penuh, dokumen, commit, tag) dan laporkan sesuai AGENTS.md bagian 8.
```


---

## PROMPT U2 - Gate gagal
Kapan: Bila agent macet atau gate gagal berulang.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: PERBAIKI KEGAGALAN GATE
1. Jalankan `python scripts/gate.py` dan tempel keluaran lengkap bagian yang gagal.
2. Untuk setiap kegagalan tulis: gejala, akar masalah (dibuktikan dengan output atau pembacaan kode), rencana perbaikan.
3. Perbaiki di kode. Dilarang menghapus atau melemahkan test, skip, xfail, atau mengubah assert agar lolos. Jika menurutmu test yang salah, jelaskan bukti dan minta persetujuan saya dulu.
4. Jalankan ulang gate PENUH. Catat masalah dan solusi di bagian "Masalah ditemukan dan solusi" pada phase log.
5. Gagal 3 kali pada masalah yang sama: berhenti, tulis analisis, dan tanyakan.
```


---

## PROMPT U3 - Audit independen setelah tiap fase
Kapan: Disarankan, di sesi baru setelah fase di-commit, sebelum lanjut fase berikutnya. Ganti NN.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: AUDIT FASE NN (HANYA MEMERIKSA, JANGAN MENGUBAH FILE)
1. Baca bagian "FASE NN" di PLAN.md, docs/phase-logs/PHASE-NN.md, CHANGELOG.md, dan commit fase tersebut (`git show --stat phase-NN-done`).
2. Periksa dan beri PASS atau FAIL disertai bukti: (a) setiap task PNN-T* ada dan sesuai PLAN.md; (b) tag phase-NN-done ada, merge --no-ff, tidak ada push; (c) format commit sesuai SDLC.md bagian 5; (d) CHANGELOG dan phase log lengkap dan cocok dengan diff nyata; (e) test ID di TESTING.md untuk fase ini ada dan lulus; (f) tidak ada file di luar lingkup fase, tidak ada test yang di-skip atau di-xfail (`grep`); (g) implementasi sesuai ARCHITECTURE.md dan PROTOCOL.md; (h) `python scripts/gate.py` hijau di main.
3. Keluaran: tabel PASS/FAIL, daftar temuan (berat, sedang, ringan), rekomendasi. Jangan memperbaiki apa pun.
```


---

## PROMPT U4 - Bug di fase lama (back-fix)
Kapan: Bila bug fase sebelumnya ditemukan belakangan.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: BACK-FIX
Bug: [TEMPEL: gejala, perintah untuk mereproduksi, keluaran error]
1. Reproduksi bug dan tulis test regresi yang gagal (merah) lebih dulu.
2. Perbaiki seminimal mungkin. Jangan menulis ulang sejarah git dan jangan amend commit lama.
3. Gate penuh. Commit `fix(phase-XX): ...` di branch fase aktif. Catat di CHANGELOG (Fixed) dan bagian "Back-fix" pada phase log fase aktif.
4. Bila perbaikan menyentuh ARCHITECTURE.md atau PROTOCOL.md, perbarui dan tambah entri DECISIONS. Laporkan.
```


---

## PROMPT U5 - Usulan perubahan desain
Kapan: Bila agent atau Anda menemukan desain yang perlu diubah. Agent hanya mengusulkan.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: USULAN PERUBAHAN DESAIN (TANPA IMPLEMENTASI)
Masalah atau ide: [TEMPEL]
1. Baca ARCHITECTURE.md, PROTOCOL.md, DECISIONS.md bagian terkait.
2. Tulis usulan: masalah, bukti, minimal 2 opsi, dampak ke fase lain, dampak ke test, dampak ke laporan, rekomendasi.
3. Tambahkan entri DECISIONS.md berstatus "Proposed". Jangan mengubah kode, ARCHITECTURE.md, atau PROTOCOL.md. Tunggu persetujuan saya.
```


---

## PROMPT U6 - Audit final sebelum kumpul
Kapan: Setelah Fase 10 selesai, sebelum mengumpulkan.

```text
KONTEKS WAJIB (baca sebelum melakukan apa pun)
Proyek ZipHive: kompresi data terdistribusi Master-Worker (Tema 16, UAS Komputasi Paralel dan Sistem Terdistribusi, Unsil). Seluruh aturan ada di file repo, bukan di ingatanmu.
1. Baca penuh dan berurutan: AGENTS.md, PLAN.md, SDLC.md, lalu dokumen yang disebut pada tugas di bawah.
2. Jalankan `git status`, `git log --oneline -10`, dan `ls`. Laporkan kondisi nyata repo (bukan asumsi).
ATURAN ANTI-HALUSINASI
- Sumber kebenaran adalah dokumen di repo. Jika permintaan ini bertentangan dengan dokumen, berhenti dan tanyakan. Jangan memilih sendiri.
- Jangan mengarang file, fungsi, hasil test, angka, URL, atau keluaran perintah. Jika tidak yakin, buka file atau jalankan perintah, lalu kutip hasilnya.
- Jangan mengerjakan apa pun di luar fase ini. Jangan menambah fitur, dependensi, atau mengubah desain di luar PLAN.md, ARCHITECTURE.md, PROTOCOL.md. Ide tambahan ditulis di phase log bagian "Keterbatasan dan utang teknis", tidak diimplementasikan.
- Informasi yang tidak ada: tulis "TIDAK DIKETAHUI" dan tanyakan ke saya.
- Setiap klaim "lulus" wajib disertai keluaran perintah yang nyata.

TUGAS: AUDIT FINAL (HANYA MEMERIKSA)
Dokumen WAJIB dibaca: soal UAS (ringkasannya ada di PLAN.md tabel pemetaan), SUBMISSION.md bagian 4, EXPERIMENTS.md, results/summary.csv, laporan DOCX, ZIP hasil pack_source.
Periksa dengan bukti: (a) tiap kebutuhan soal a sampai f terpenuhi dan ada di kode dan laporan; (b) enam jenis pengujian dan enam metrik ada di hasil dan laporan; (c) setiap angka di laporan identik dengan results/summary.csv (bandingkan satu per satu); (d) tidak ada data algo=sim; (e) sumber aset lengkap; (f) isi ZIP benar; (g) gate hijau di main, tag v1.0.0 ada; (h) sisa "PERLU DIISI USER" di seluruh dokumen. Keluarkan tabel PASS/FAIL dan daftar tindakan untuk saya.
```
