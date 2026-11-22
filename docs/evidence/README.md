# Bukti 10 node virtual untuk laporan dan video

Node pada pelaksanaan 2026-11-22 bersifat virtual (ADR-015): 1 Master berjalan di host dan
9 Worker berjalan sebagai container `ziphive-node:min`. Tangkapan layar diambil manual oleh user
agar gambar pada laporan benar-benar berasal dari mesin yang dipakai. Langkah perintah yang sudah
diuji ada pada `docs/evidence/RUNBOOK.md`; bagian di bawah ini hanya mencatat berkas targetnya.

## 1. Tangkapan layar 10 node virtual

Jalankan Master dan sembilan Worker sesuai `DEPLOYMENT.md` bagian 0, lalu **selagi run berjalan**
buka terminal dan jalankan perintah berikut, kemudian tangkap layarnya:

```bash
docker ps --format 'table {{.Names}}\t{{.ID}}\t{{.Status}}'
docker inspect -f '{{.Name}} {{.Config.Hostname}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
  ziphive-w1 ziphive-w2 ziphive-w3 ziphive-w4 ziphive-w5 \
  ziphive-w6 ziphive-w7 ziphive-w8 ziphive-w9
```

Simpan sebagai `reports/img/10-node-virtual.png`.

## 2. Tangkapan layar terminal Master dan Worker

- Terminal 1: keluaran `python -m pcomp.master ...` sampai muncul `MASTER OK`.
- Terminal 2: salah satu Worker dengan keluaran `WORKER OK (w1)`.

Simpan sebagai `reports/img/master-terminal.png` dan `reports/img/worker-terminal.png`.

## 3. Tangkapan layar bukti fault tolerance (E5)

Selagi run E5 berjalan, jalankan `docker ps` untuk menunjukkan sembilan Worker, lalu setelah
satu Worker dimatikan jalankan kembali:

```bash
docker ps -a --filter name=ziphive-w --format 'table {{.Names}}\t{{.Status}}'
```

Simpan sebagai `reports/img/e5-worker-mati.png`. Bukti pendukung non-gambar ada pada
`results/raw/E5/<run_id>/events.jsonl` (event `worker_exit_injected`, `worker_dead`,
`task_requeued`) dan `results/raw/E5/<run_id>/verify.log` (`VERIFY OK`).

## 3a. Status pengambilan gambar (2026-11-22)

Keempat gambar sudah diambil dan diperiksa ulang isinya pada 2026-11-22.

| Berkas | Waktu | Isi yang terverifikasi |
|---|---|---|
| `reports/img/10-node-virtual.png` | 18.45 | `docker ps` sembilan container `Up`, `docker inspect` hostname w1-w9 dengan IP 172.17.0.2-172.17.0.10, `docker exec ziphive-w1 ps` menampilkan anak `multiprocessing.spawn`, `docker stats` sembilan container aktif |
| `reports/img/master-terminal.png` | 18.49 | banner kelompok, `Master mendengarkan di 0.0.0.0:5050`, `Mulai memproses 1539 task dengan 9 Worker`, blok metrik, `MASTER OK` |
| `reports/img/worker-terminal.png` | 18.52 | banner Worker, `SHUTDOWN diterima: semua task selesai`, `WORKER OK (w1)` |
| `reports/img/e5-worker-mati.png` | 19.01 | `docker ps` sembilan `Up`, setelah `docker kill` menjadi `ziphive-w1  Exited (137)` dengan delapan Worker lain `Up` |

Angka yang terlihat pada gambar berasal dari run bukti (`output/demo-*`, sudah dihapus), bukan
eksperimen resmi. Angka laporan tetap hanya dari `results/summary.csv` dan `results/raw/`.
Run bukti E5 juga memberi bukti teks pendukung: 2565/2565 task selesai setelah w1 dimatikan, dengan
event `worker_dead` (w1, 1 task in-flight) dan `task_requeued` (task 138) pada `events.jsonl` run
tersebut.

Catatan teknis: percobaan pertama E5 gagal karena `docker kill` dijalankan setelah run selesai
(`is not running`, semua container `Exited (0)`), sehingga gambar itu diganti. Runbook sekarang
mewajibkan `docker ps` menunjukkan sembilan `Up` sebelum kill, tanpa `sleep` buta.

Gambar disimpan di `reports/` yang masuk `.gitignore`, jadi tidak ikut commit. Jika gambar perlu
masuk repo untuk lampiran, tambahkan pengecualian di `.gitignore`.


## 4. Bukti teks yang sudah tersedia di repo

| Berkas | Isi |
|---|---|
| `results/summary.csv` | seluruh run E1-E6, tiga ulangan, dengan `verify_ok` |
| `results/raw/<exp>/<run_id>/verify.log` | keluaran `verify.py` per run (`VERIFY OK`) |
| `results/raw/<exp>/<run_id>/metrics.json` | metrik per run, termasuk `worker_stats` |
| `results/raw/<exp>/<run_id>/events.jsonl` | jejak event per run |
| `results/raw/<exp>/<run_id>/worker-w*.log` | log tiap container Worker |
| `results/figures/*.png` | grafik hasil siap dipakai laporan |
