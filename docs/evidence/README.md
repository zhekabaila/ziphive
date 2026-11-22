# Bukti 10 node virtual untuk laporan dan video

Node pada pelaksanaan 2026-11-22 bersifat virtual (ADR-015): 1 Master berjalan di host dan
9 Worker berjalan sebagai container `ziphive-node:min`. Tangkapan layar diambil manual oleh user
agar gambar pada laporan benar-benar berasal dari mesin yang dipakai.

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

## 4. Bukti teks yang sudah tersedia di repo

| Berkas | Isi |
|---|---|
| `results/summary.csv` | seluruh run E1-E6, tiga ulangan, dengan `verify_ok` |
| `results/raw/<exp>/<run_id>/verify.log` | keluaran `verify.py` per run (`VERIFY OK`) |
| `results/raw/<exp>/<run_id>/metrics.json` | metrik per run, termasuk `worker_stats` |
| `results/raw/<exp>/<run_id>/events.jsonl` | jejak event per run |
| `results/raw/<exp>/<run_id>/worker-w*.log` | log tiap container Worker |
| `results/figures/*.png` | grafik hasil siap dipakai laporan |
