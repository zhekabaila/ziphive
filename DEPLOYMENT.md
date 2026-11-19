# DEPLOYMENT.md — Menjalankan di 10 Node

## 1. Inventaris node (isi user)
| Node | Peran | Hostname | IP | OS | CPU/core | RAM | Python | Check OK |
|---|---|---|---|---|---|---|---|---|
| n1 | Master | | | | | | | |
| n2..n10 | Worker | | | | | | | |

## 2. Persiapan tiap node
1. Python 3.11 atau lebih baru (versi sama di semua node bila memungkinkan).
2. Salin kode: `git clone` atau ekstrak ZIP dari `pack_source.py`.
3. `python -m venv .venv`, aktifkan, lalu `pip install -r requirements-worker.txt` (Worker) atau `requirements.txt` (Master).
4. Jalankan `python scripts/check_node.py --master <IP_MASTER>:5050`. Semua baris harus OK.

## 3. Jaringan
- Semua node satu subnet, IP statis atau dicatat. Utamakan kabel LAN. Bila wireless, catat kondisinya di laporan.
- Buka port 5050/TCP masuk di Master (firewall OS). Worker hanya butuh koneksi keluar.
- Uji dari Worker: `python scripts/check_node.py --ping-master`.

## 4. Menjalankan
Master (n1):
`python -m pcomp.master --host 0.0.0.0 --port 5050 --input data/silesia --expect-workers 9 --scheduler dynamic --algo lzma --out results/raw/E3/run1`
Worker (n2..n10):
`python -m pcomp.worker --master <IP_MASTER>:5050 --id w<N> --procs <jumlah core>`
Atau `python scripts/launch_workers.py --nodes config/nodes.toml` (mode ssh) atau `--print` untuk mencetak perintah per node.

## 5. Dataset
Dataset ada di Master saja pada mode `transfer`. Pada mode `local` (bila jaringan bottleneck), salin dataset ke path yang sama di setiap Worker.

## 6. Checklist pra-eksperimen
- [ ] Semua node lulus `check_node.py`
- [ ] Mode hemat daya dimatikan, laptop dicolok listrik
- [ ] Aplikasi berat lain ditutup
- [ ] Versi kode sama di semua node (`python -m pcomp --version`, hash commit sama)
- [ ] Ruang disk Master cukup untuk output
- [ ] Dry-run dataset kecil berhasil `VERIFY OK`

## 7. Troubleshooting
| Gejala | Penyebab umum | Tindakan |
|---|---|---|
| Worker tidak bisa connect | Firewall Master, IP salah | Buka port, cek IP dan `check_node.py` |
| `VERSION_MISMATCH` | Versi kode beda | Samakan commit |
| Error spawn di Windows | Kode di luar guard `__main__` | Periksa entry point, jalankan via `python -m` |
| Worker ditandai DEAD padahal hidup | Jaringan lambat atau CPU 100% | Naikkan `heartbeat_timeout`, kurangi `--procs` satu |
| Throughput rendah, CPU Worker rendah | Bandwidth Master bottleneck | Ukur transfer, pakai algoritma lebih berat atau mode `local` |
