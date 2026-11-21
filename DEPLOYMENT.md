# DEPLOYMENT.md — Menjalankan di 10 Node

## 1. Inventaris node (isi user)
Isi tabel ini dari hasil `python scripts/check_node.py` pada setiap node, lalu salin nilainya ke
`config/nodes.toml` (kolom `IP` ke `host`, `user` ke `user`, `Python` ke `python`). Placeholder
`<...>` pada `config/nodes.toml` wajib diganti; `launch_workers.py` menolak berjalan selama masih
ada placeholder.

| Node | Peran | Hostname | IP | OS | CPU/core | RAM | Python | Check OK |
|---|---|---|---|---|---|---|---|---|
| n1 | Master | | | | | | | |
| n2 | Worker | | | | | | | |
| n3 | Worker | | | | | | | |
| n4 | Worker | | | | | | | |
| n5 | Worker | | | | | | | |
| n6 | Worker | | | | | | | |
| n7 | Worker | | | | | | | |
| n8 | Worker | | | | | | | |
| n9 | Worker | | | | | | | |
| n10 | Worker | | | | | | | |

## 2. Persiapan tiap node
1. Python 3.11 atau lebih baru (versi sama di semua node bila memungkinkan).
2. Salin kode: `git clone <repo>` atau ekstrak ZIP dari `python scripts/pack_source.py` (bagian 8).
3. Dari folder proyek: `python -m venv .venv`, aktifkan, lalu `python -m pip install -e .` agar
   modul `pcomp` dapat diimpor oleh perintah `python -m pcomp`. Setelah itu pasang dependensi:
   `python -m pip install -r requirements-worker.txt` (Worker) atau
   `python -m pip install -r requirements.txt` (Master).
4. Jalankan `python scripts/check_node.py`. Semua baris harus `OK` dan diakhiri `CHECK NODE OK`.
5. Verifikasi versi kode: `python -m pcomp --version` harus sama di semua node.

Contoh keluaran `check_node.py` di mesin pengembangan (bukan node lab):

```
OK python: 3.14.4 (>= 3.11)
OK psutil: 7.2.2
OK paket: pcomp 0.07.0
OK protokol: PROTOCOL_VERSION=1
OK core: 4 core logis
OK ram: 7.7 GiB
CHECK NODE OK
```

Bila baris `paket` FAIL, jalankan `python -m pip install -e .`. Bila `psutil` FAIL, jalankan
`python -m pip install -r requirements.txt`. Bila nilai `protokol` berbeda antar node, samakan
commit kode sebelum eksperimen.

## 3. Jaringan
- Semua node satu subnet, IP statis atau dicatat. Utamakan kabel LAN. Bila wireless, catat kondisinya di laporan.
- Buka port 5050/TCP masuk di Master (firewall OS). Worker hanya butuh koneksi keluar (risiko R3).
- Uji dari tiap Worker:
  1. `python scripts/check_node.py --master <IP_MASTER>:5050` (seluruh pemeriksaan lokal + port Master).
  2. `python scripts/check_node.py --ping-master --master <IP_MASTER>:5050` (hanya koneksi ke Master).
  Tanpa `--master`, `--ping-master` memakai alamat pada `config/worker.toml`. Baris `master` harus
  `OK`; bila `FAIL ... tidak terjangkau`, periksa firewall dan IP Master.

## 4. Menjalankan
Master (n1):

```
python -m pcomp.master --host 0.0.0.0 --port 5050 --input data/silesia --expect-workers 9 --scheduler dynamic --algo lzma --out results/raw/E3/run1
```

Worker (n2..n10), satu per node:

```
python -m pcomp.worker --master <IP_MASTER>:5050 --id w<N> --procs <jumlah core>
```

Alternatif dari satu node (misalnya n1) memakai inventaris `config/nodes.toml`:

```
python scripts/launch_workers.py --print       # cetak perintah ssh tiap node, tanpa eksekusi
python scripts/launch_workers.py --ssh         # jalankan lewat ssh (kunci ssh sudah terpasang)
python scripts/launch_workers.py --ssh --dry-run
python scripts/launch_workers.py --procs 4 --dir ~/ziphive --ssh
```

`--procs` dipakai bila entri node pada `config/nodes.toml` tidak mengisi `procs`; nilai `procs`
pada entri node selalu menang agar node dengan core berbeda dapat disesuaikan. Skrip tidak
menyimpan kata sandi: ssh memakai kunci, dan `--id` Worker dibangkitkan berurutan `w1` sampai
`w9` mengikuti urutan entri Worker pada inventaris.

## 5. Dataset
Dataset ada di Master saja pada mode `transfer`. Bila pengukuran dry-run nanti menunjukkan
bandwidth keluar Master menjadi bottleneck (risiko R1), opsi `--data-mode local` disiapkan sebagai
cadangan pada Fase 8, tetapi belum tersedia pada versi ini (lihat `PLAN.md` risiko R1 dan
`docs/phase-logs/PHASE-08.md` bagian 10). Untuk sementara kurangi beban jaringan dengan algoritma
yang lebih berat (`lzma`) atau dataset yang lebih kecil.

## 6. Checklist pra-eksperimen
- [ ] Semua node lulus `check_node.py` (`CHECK NODE OK`)
- [ ] Port Master terjangkau dari semua Worker (`--ping-master` OK)
- [ ] `config/nodes.toml` sudah terisi dan `launch_workers.py --print` keluar `LAUNCH PLAN OK`
- [ ] Mode hemat daya dimatikan, laptop dicolok listrik
- [ ] Aplikasi berat lain ditutup
- [ ] Versi kode sama di semua node (`python -m pcomp --version`, hash commit sama)
- [ ] Ruang disk Master cukup untuk output
- [ ] Dry-run dataset kecil berhasil `VERIFY OK`
- [ ] `config/group.toml` sudah diisi nama kelompok dan anggota (banner tidak menampilkan peringatan)

## 7. Troubleshooting
| Gejala | Penyebab umum | Tindakan |
|---|---|---|
| Worker tidak bisa connect | Firewall Master, IP salah | Buka port, cek IP, jalankan `check_node.py --ping-master` |
| `VERSION_MISMATCH` | Versi kode beda | Samakan commit, cek baris `protokol` pada `check_node.py` |
| Error spawn di Windows | Kode di luar guard `__main__` | Periksa entry point, jalankan via `python -m` |
| Worker ditandai DEAD padahal hidup | Jaringan lambat atau CPU 100% | Naikkan `heartbeat_timeout`, kurangi `--procs` satu |
| Throughput rendah, CPU Worker rendah | Bandwidth Master bottleneck (R1) | Ukur transfer, pakai algoritma lebih berat, catat temuan untuk evaluasi `--data-mode local` |
| `ModuleNotFoundError: pcomp` | Paket belum dipasang | `python -m pip install -e .` di node tersebut |
| `LAUNCH GAGAL: lengkapi config/nodes.toml` | Masih ada placeholder `<...>` | Isi inventaris dari bagian 1 |

## 8. Paket sumber untuk node lain
Bila node tidak memakai `git clone`, paketkan repo menjadi ZIP:

```
python scripts/pack_source.py
python scripts/pack_source.py --list          # hanya daftar berkas
python scripts/pack_source.py --out D:/kirim/ziphive.zip
```

Arsip memuat `src/`, `tests/`, `scripts/`, `config/`, `docs/`, dokumen `.md`, `pyproject.toml`,
`requirements*.txt`, `Makefile`, dan `results/` (ringkasan dan grafik). `data/`, `output/`,
`.venv`, `.git`, cache Python, dan `results/dev/` (hasil algoritma `sim`) tidak ikut. Keluaran
akhir skrip adalah baris `PACK OK` beserta jumlah berkas dan ukuran arsip.
