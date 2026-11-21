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
Commit bagian agent: `feat(phase-08): add node checks, launch scripts, packaging, deployment guide`
(hash `2789b9a`), digabung ke `main` dengan merge `00fcc68`.

Tag bagian agent `phase-08a-done` sudah ada dan menunjuk ke commit `00fcc68`, terverifikasi dengan
`git rev-parse phase-08a-done^{commit}` serta `git tag --points-at 00fcc68`. Tag fase 00 sampai 07
(`phase-00-done` sampai `phase-07-done`) juga tersedia. Tag `phase-08-done` baru dibuat pada
bagian user setelah seluruh node lulus.

Catatan: pada awal sesi 2026-11-21 pukul 11:26 tag belum ada di clone ini (`git tag -l` kosong
dan `git ls-remote --tags origin` kosong), lalu tag muncul pukul 12:17 setelah diambil dari
repo bersama. Pencatatan bagian agent tidak berubah karenanya; commit yang ditandai identik.


## 13. Human checklist (diisi dari hasil user)
Data yang tidak dikirim user ditulis "TIDAK ADA DATA". Pengisian pertama dilakukan 2026-11-21
memakai keluaran nyata dari mesin Master saja; sembilan Worker belum ada datanya.

| Item | Status | Catatan |
|---|---|---|
| Python dan dependensi terpasang di 9 Worker | TIDAK ADA DATA | belum ada laporan dari node Worker |
| `check_node.py` dijalankan di 10 node | SEBAGIAN (1 dari 10) | n1 `CHECK NODE OK` (exit 0); n2 sampai n10 belum dijalankan |
| Inventaris node (host, IP, CPU, core, RAM, OS) | SEBAGIAN (n1 saja) | lihat `DEPLOYMENT.md` bagian 1 dan bagian 13.1 |
| Dry-run dataset kecil di 10 node | TIDAK ADA DATA | belum ada log Master maupun Worker di 10 node fisik |
| Evaluasi risiko R1 | TIDAK DIKETAHUI | belum ada pengukuran pada jaringan lab; lihat batasan pada bagian 13.2 |

### 13.1 Bukti pemeriksaan node n1 (Master)
Keluaran apa adanya dari `python scripts/check_node.py` di mesin Master:

```
OK python: 3.14.4 (>= 3.11)
OK psutil: 7.2.2
OK paket: pcomp 0.07.0
OK protokol: PROTOCOL_VERSION=1
OK core: 8 core logis
OK ram: 8.0 GiB
CHECK NODE OK
```

Inventaris pendukung dari perintah sistem: `hostname` menghasilkan
`Zhekas-MacBook-Air.local`, `sysctl -n machdep.cpu.brand_string` menghasilkan `Apple M1`,
`sw_vers -productVersion` menghasilkan `26.6.2`, `sysctl -n hw.logicalcpu` menghasilkan `8`,
`sysctl -n hw.memsize` menghasilkan `8589934592`, dan `ipconfig getifaddr en0` menghasilkan
`192.168.0.105`.

Dua keterbatasan yang perlu dicatat:

1. Mesin n1 adalah laptop pengembangan berbasis macOS dengan 8 core logis dan RAM 8.0 GiB.
   Angka ini berbeda dari mesin pengembangan yang dipakai pada bagian agent fase ini
   (Windows, 4 core logis, RAM 7.7 GiB), sehingga hasil performa tidak dapat dibandingkan
   langsung dengan catatan bagian agent.
2. Pemeriksaan `--ping-master` belum dijalankan dan tidak dapat diuji dari node Master sendiri,
   sehingga baris `master` pada `check_node.py` masih menunggu pengujian dari sisi Worker.

### 13.2 Validasi teknis 2 mesin (VM pengembangan, bukan node fisik)
User belum memiliki 9 node fisik. Sebagai pengganti sementara, dijalankan uji 2 mesin nyata:
Master di laptop macOS (n1) dan Worker di VM UTM Debian pada alamat terpisah. Uji ini membuktikan
jalur jaringan, bukan jumlah node, dan hasilnya **tidak boleh dipakai** untuk eksperimen resmi
Fase 9 maupun untuk menilai R1.

Spesifikasi VM Worker:

```
OS    : Debian GNU/Linux 11 (bullseye), kernel 5.10.0-38-arm64
CPU   : 4 core (arm64)
RAM   : 3.8 GiB
Disk  : 28G, 18G bebas
IP    : 192.168.64.9/24, gateway 192.168.64.1 (host macOS, jaringan UTM shared)
Python: 3.9.2 bawaan; dijadikan 3.11.9 dari sumber karena syarat proyek
```

Pemeriksaan awal pada VM dengan Python bawaan gagal, dan ini perilaku yang benar:

```
FAIL python: 3.9.2 (butuh >= 3.11)
FAIL psutil: tidak terpasang (pip install -r requirements.txt)
OK paket: pcomp 0.07.0
OK protokol: PROTOCOL_VERSION=1
FAIL core: jumlah core tidak terbaca
FAIL ram: kapasitas RAM tidak terbaca
CHECK NODE GAGAL
```

Setelah CPython 3.11.9 dibangun di `/opt/python3.11`, paket sumber dari `pack_source.py`
diekstrak, lalu `pip install -e .` dan `requirements-worker.txt` dijalankan; hasilnya:

```
OK python: 3.11.9 (>= 3.11)
OK psutil: 7.2.2
OK paket: pcomp 0.07.0
OK protokol: PROTOCOL_VERSION=1
OK core: 4 core logis
OK ram: 3.8 GiB
CHECK NODE OK
```

Uji keterjangkauan Master dari VM (yang tidak mungkin diuji dari n1 sendiri):

```
OK master: 192.168.64.1:5050 menerima koneksi TCP
CHECK NODE OK
```

Dry-run 2 mesin memakai dataset sintetis 64 MiB, `lzma` level 6, chunk 4 MiB, 1 Worker dengan
4 proses, scheduler `dynamic`:

```
tasks        : 17
tasks_ok     : 17
tasks_failed : 0
workers      : 1
total_mb     : 64.000752
ratio        : 2.631605
time_s       : 4.04493
throughput   : 15.822462 MB/s
MASTER OK
```

`metrics.json` mencatat `"simulated": false`, `tasks_retried: 0`, `imbalance: 1.0`, dan
`busy_sec` Worker 13.46 detik. Verifikasi manifest menghasilkan:

```
chunks       : 17
VERIFY OK
```

Catatan pengamatan dari run ini:

1. Worker menerima `SHUTDOWN`, keluar dengan `WORKER OK (w1)` dan kode keluar 0.
2. Master mencatat satu peringatan `koneksi Worker berakhir: koneksi tertutup saat menunggu
   12 byte` yang berasal dari `check_node.py --master` (membuka TCP lalu menutup). Tidak ada
   event `worker_dead`, `task_requeued`, atau `task_failed`; `events.jsonl` hanya memuat
   `worker_registered` untuk `w1`. Perilaku ini sudah ditambahkan ke tabel troubleshooting
   `DEPLOYMENT.md`.
3. `hostname` VM kebetulan bernama `zhekabaila`, sama dengan nama host laptop. Ini hanya
   kebetulan penamaan image, bukan tanda Worker berjalan di mesin yang sama: Worker dieksekusi
   lewat ssh di `192.168.64.9` dan membawa Python 3.11.9 arm64 Linux.
4. Angka `time_s` 4.04 detik didominasi komputasi (`busy_sec` 13.46 detik dibagi 4 proses
   menghasilkan sekitar 3.37 detik), bukan transfer. Karena jaringan UTM shared bersifat
   host-internal, angka ini tidak menggambarkan bandwidth LAN lab dan tidak dapat dipakai
   menyimpulkan R1.


