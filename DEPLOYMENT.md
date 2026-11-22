# DEPLOYMENT.md — Menjalankan di 10 Node Virtual

> Untuk 10 perangkat fisik (laptop Master + 9 laptop Worker, macOS/Windows/Linux, tanpa ssh dan
> tanpa Docker), pakai `DEPLOYMENT-PHYSICAL.md`. Berkas ini tetap berlaku untuk mereproduksi hasil
> node virtual (ADR-015).

## 0. Mode 10 node virtual (ADR-015)
Soal meminta 10 node fisik, tetapi pelaksanaan 2026-11-22 memakai 10 node virtual pada satu laptop:
1 Master berjalan di host dan 9 Worker berjalan sebagai container Linux, masing-masing dengan
hostname dan IP sendiri serta `procs = 1`. Laporan dan video wajib menyebut bahwa node bersifat
virtual, bukan 10 perangkat fisik.

Image paling ringan yang sudah divalidasi (77,8 MB, Python 3.12.13, psutil 5.9.8):

```bash
docker build -t ziphive-node:min - <<'EOF'
FROM alpine:3.20
RUN apk add --no-cache python3 py3-psutil
EOF
```

Menjalankan satu run (contoh port 5090, dataset 64 MiB):

```bash
mkdir -p output/virtual-10
PYTHONPATH=src python -m pcomp.master --input data/dryrun2node --out output/virtual-10 \
  --expect-workers 9 --scheduler dynamic --host 0.0.0.0 --port 5090 \
  --algo lzma --level 6 --chunk-mb 4 &

for i in $(seq 1 9); do
  docker run -d --name "ziphive-w$i" --hostname "w$i" \
    -v "$PWD":/app:ro -e PYTHONPATH=/app/src -w /app ziphive-node:min \
    python3 -m pcomp.worker --master host.docker.internal:5090 --id "w$i" --procs 1
done
```

`host.docker.internal` disediakan Colima dan menunjuk ke host macOS (192.168.5.2 pada mesin ini).
Periksa tiap node selagi container hidup dengan
`docker exec ziphive-w1 python3 scripts/check_node.py`.

## 1. Inventaris 10 node virtual (isi user)
Isi tabel ini dari hasil `python scripts/check_node.py` pada setiap node virtual, lalu salin nilainya ke
`config/nodes.toml` (kolom `IP` ke `host`, `user` ke `user`, `Python` ke `python`). Placeholder
`<...>` pada `config/nodes.toml` wajib diganti; `launch_workers.py` menolak berjalan selama masih
ada placeholder.

| Node | Peran | Hostname | IP | OS | CPU/core | RAM | Python | Check OK |
|---|---|---|---|---|---|---|---|---|
| n1 | Master | Zhekas-MacBook-Air.local | 192.168.0.105 | macOS 26.6.2 | Apple M1 / 8 core logis | 8.0 GiB | 3.14.4 | OK (lokal) |
| n2 | Worker | w1 (container) | 172.17.0.2 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n3 | Worker | w2 (container) | 172.17.0.3 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n4 | Worker | w3 (container) | 172.17.0.4 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n5 | Worker | w4 (container) | 172.17.0.5 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n6 | Worker | w5 (container) | 172.17.0.6 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n7 | Worker | w6 (container) | 172.17.0.7 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n8 | Worker | w7 (container) | 172.17.0.8 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n9 | Worker | w8 (container) | 172.17.0.9 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |
| n10 | Worker | w9 (container) | 172.17.0.10 | Alpine Linux 3.20 | 6 core logis (Colima) | 3.8 GiB | 3.12.13 | OK |

Catatan pengisian (per 2026-11-21):

1. Baris n1 diisi dari keluaran nyata `python scripts/check_node.py` di mesin Master, yaitu
   laptop pengembangan (macOS), bukan node lab. Rinciannya: `python 3.14.4`, `psutil 7.2.2`,
   `pcomp 0.07.0`, `PROTOCOL_VERSION=1`, `8 core logis`, `8.0 GiB`, `CHECK NODE OK` (exit 0).
   Nilai `core` dan `RAM` juga cocok dengan `sysctl -n hw.logicalcpu` (8) dan
   `sysctl -n hw.memsize` (8589934592 byte).
2. Kolom `Check OK` n1 hanya mencakup pemeriksaan lokal. Pemeriksaan `--ping-master` belum
   dijalankan karena Master belum dijalankan, dan itu tidak mungkin diuji dari node Master sendiri.
3. IP `192.168.0.105` adalah alamat DHCP yang terbaca dari antarmuka `en0` pada jaringan rumah
   (gateway `192.168.0.1`) saat pencatatan. Alamat ini dapat berubah dan bukan alamat subnet lab;
   perbarui sebelum eksperimen dan salin ke `config/nodes.toml`.
4. Baris n2 sampai n10 diisi 2026-11-22 dari 9 container `ziphive-node:min` (Alpine 3.20) yang
   dijalankan pada Colima. IP `172.17.0.2` sampai `172.17.0.10` adalah alamat Docker bridge yang
   bersifat dinamis; catat ulang setiap kali container dijalankan. CPU dan RAM mengikuti batas VM
   Colima (6 core, 4 GiB), bukan kapasitas penuh laptop.

## 2. Persiapan tiap node
1. Python 3.11 atau lebih baru (versi sama di semua node bila memungkinkan).
   Catatan Debian 11 (bullseye): paket `python3` bawaan adalah 3.9.2 sehingga `check_node.py`
   gagal pada baris `python`. Repositori `bullseye-backports` tidak lagi menyediakan
   `python3.11`, jadi bangun CPython dari sumber
   (`./configure --prefix=/opt/python3.11 --enable-shared`), daftarkan
   `/opt/python3.11/lib` pada `/etc/ld.so.conf.d/` lalu `ldconfig`, dan pakai
   `/opt/python3.11/bin/python3.11 -m venv .venv`. Debian 12 atau lebih baru sudah membawa
   Python 3.11 sehingga langkah ini tidak perlu.
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
| `FAIL python: 3.9.x (butuh >= 3.11)` di Debian 11 | Debian 11 hanya menyediakan Python 3.9.2 dan `bullseye-backports` tidak lagi tersedia | Bangun Python 3.11 dari sumber seperti catatan bagian 2 butir 1, atau pakai Debian 12 |
| Master mencatat `koneksi Worker berakhir: koneksi tertutup saat menunggu 12 byte` | `check_node.py --master` membuka TCP lalu langsung menutupnya sebagai uji keterjangkauan | Bukan kegagalan; tidak ada state Worker yang berubah. Uji `--ping-master` sebelum Master mulai agar log run bersih |

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

## 9. Perangkat fisik
Bila eksperimen dijalankan pada 10 laptop sungguhan (ADR-016), jangan memakai Docker maupun ssh.
Gunakan launcher `setup-node`, `start-worker`, dan `start-master`, lalu orkestrasi dengan
`python scripts/run_experiments.py --worker-mode external`. Seluruh prosedur, termasuk pengaturan
E4 (`--throttle 0.25` pada w9) dan E5 (injeksi `KILL` dari Master), ada di
`DEPLOYMENT-PHYSICAL.md`.
