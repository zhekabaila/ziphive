# Runbook pengambilan tangkapan layar bukti 10 node virtual

Runbook ini dipakai user untuk mengambil empat tangkapan layar bukti yang diminta laporan dan video:
bukti 10 node virtual, terminal Master, terminal Worker, dan bukti E5 (satu Worker mati).
Semua perintah di bawah sudah diuji pada skala kecil (1 Master + 2 container) sebelum diserahkan.

Penting: run pada runbook ini adalah **run bukti deployment**, bukan eksperimen. Angka performa
laporan tetap hanya berasal dari `results/raw/` (E1-E6). Jangan menyalin angka dari layar ke laporan.

## 1. Prasyarat

Jalankan di terminal mana pun di `/Users/zhekabaila/ziphive`:

```bash
colima status                                    # harus "colima is running"
docker images ziphive-node:min --format '{{.Repository}}:{{.Tag}} {{.Size}}'   # 77.8MB
du -sh data/bench                               # 2.0G
lsof -nP -iTCP:5050 -sTCP:LISTEN                # harus kosong (port 5050 bebas)
```

Jika `lsof` mengeluarkan baris, hentikan proses lama dulu: `pkill -f "pcomp.master"`.

Sebelum mulai: tutup Chrome, Discord, dan aplikasi berat lain agar mesin tenang dan run tidak
melambat drastis (bukan syarat benar-salah, tetapi membuat progres task terlihat wajar).
Siapkan juga folder gambar: `mkdir -p reports/img`.

## 2. Susunan terminal

| Terminal | Isi | Perintah |
|---|---|---|
| T1 | Master (harus terlihat) | `python -m pcomp.master ...` |
| T2 | Satu Worker terlihat | `docker logs -f ziphive-w1` |
| T3 | Peluncur 9 Worker (detached) | `for i in $(seq 1 9); do docker run -d ... done` |
| T4 | Terminal bukti | `docker ps`, `docker inspect`, `docker exec ... ps` |

## 3. Skenario A — bukti 10 node + terminal Master + terminal Worker

Perkiraan durasi: 5,5 menit (terukur 324 detik saat diuji) dengan `data/bench` 2048 MiB,
`--repeat 3`, yaitu 1539 task. Durasi ini sengaja dipilih agar ada waktu memotret layar T4.

### Langkah 1 (T1) — jalankan Master, biarkan terlihat

```bash
cd /Users/zhekabaila/ziphive
rm -rf output/demo-10node
PYTHONPATH=src venv/bin/python -m pcomp.master \
  --input data/bench --out output/demo-10node \
  --algo lzma --level 6 --chunk-mb 4 --repeat 3 \
  --expect-workers 9 --barrier-timeout 600
```

Tunggu sampai muncul baris `Master mendengarkan di 0.0.0.0:5050`. Master lalu menahan barrier
sampai sembilan Worker mendaftar.

### Langkah 2 (T3) — jalankan sembilan Worker sebagai container

```bash
cd /Users/zhekabaila/ziphive
for i in $(seq 1 9); do
  docker rm -f "ziphive-w$i" >/dev/null 2>&1
  docker run -d --name "ziphive-w$i" --hostname "w$i" \
    -v "$PWD":/app:ro -e PYTHONPATH=/app/src -w /app ziphive-node:min \
    python3 -m pcomp.worker --master host.docker.internal:5050 --id "w$i" --procs 1
done
```

Sembilan baris hash container tercetak. T1 akan menampilkan
`Mulai memproses 1539 task dengan 9 Worker`.

### Langkah 3 (T2) — tampilkan log satu Worker

```bash
docker logs -f ziphive-w1
```

Biarkan terminal ini terbuka. Baris `WORKER OK (w1)` baru muncul di akhir run.

### Langkah 4 (T4) — ambil bukti 10 node selagi run berjalan

```bash
cd /Users/zhekabaila/ziphive
docker ps --format 'table {{.Names}}\t{{.ID}}\t{{.Status}}'
docker inspect -f '{{.Name}} {{.Config.Hostname}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' \
  ziphive-w1 ziphive-w2 ziphive-w3 ziphive-w4 ziphive-w5 \
  ziphive-w6 ziphive-w7 ziphive-w8 ziphive-w9
docker exec ziphive-w1 ps -o pid,ppid,stat,time,args
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}'
```

Keluaran yang diharapkan:

- `docker ps` menampilkan sembilan baris `ziphive-w1` sampai `ziphive-w9` berstatus `Up`.
- `docker inspect` menampilkan sembilan baris `ziphive-wN wN 172.17.0.X` dengan X berurutan dari 2
  sampai 10 (urutan akhir tetap ditentukan Docker, yang penting setiap node punya IP berbeda).
- `docker exec ... ps` menampilkan tiga proses: induk `python3 -m pcomp.worker`, satu anak
  `multiprocessing.spawn`, dan proses `ps` itu sendiri. Baris anak inilah bukti multiprocessing
  di dalam Worker.
- `docker stats` menampilkan CPU tiap container di atas nol (beban tersebar ke sembilan Worker,
  nilai per container lebih rendah ketika VM Colima sudah jenuh).

**Screenshot #1**: `reports/img/10-node-virtual.png` — tangkap layar T4 yang memuat
`docker ps` dan `docker inspect` sekaligus (perbesar jendela, perkecil font bila perlu).

### Langkah 5 (T4) — screenshot #1 selesai, mundur ke T1/T2

Setelah run selesai (sekitar 5,5 menit) T1 mencetak ringkasan lalu `MASTER OK`, dan T2 mencetak
`WORKER OK (w1)`.

**Screenshot #2**: `reports/img/master-terminal.png` — T1, harus memuat banner kelompok, baris
`Mulai memproses 1539 task dengan 9 Worker`, blok metrik (`tasks`, `time_s`, `throughput`), dan
`MASTER OK`.

**Screenshot #3**: `reports/img/worker-terminal.png` — T2, harus memuat banner dan
`WORKER OK (w1)`.

### Langkah 6 — bersihkan

```bash
docker rm -f $(docker ps -aq --filter name=ziphive-w) 2>/dev/null
rm -rf output/demo-10node
```

## 4. Skenario B — bukti fault tolerance E5 (satu Worker mati)

Perkiraan durasi: 5,5 menit (terukur 324 detik saat diuji). Master dijalankan ulang dengan
konfigurasi sama, `--repeat 3` (1539 task), agar ada waktu mematikan Worker di tengah run.

### Langkah 1 (T1)

```bash
cd /Users/zhekabaila/ziphive
rm -rf output/demo-e5
PYTHONPATH=src venv/bin/python -m pcomp.master \
  --input data/bench --out output/demo-e5 \
  --algo lzma --level 6 --chunk-mb 4 --repeat 3 \
  --expect-workers 9 --barrier-timeout 600
```

### Langkah 2 (T3)

```bash
cd /Users/zhekabaila/ziphive
for i in $(seq 1 9); do
  docker rm -f "ziphive-w$i" >/dev/null 2>&1
  docker run -d --name "ziphive-w$i" --hostname "w$i" \
    -v "$PWD":/app:ro -e PYTHONPATH=/app/src -w /app ziphive-node:min \
    python3 -m pcomp.worker --master host.docker.internal:5050 --id "w$i" --procs 1
done
```

### Langkah 3 (T4) — matikan satu Worker selagi run berjalan

Syarat mutlak: Master masih berjalan (T1 **belum** menampilkan `MASTER OK`). Pastikan dulu sembilan
container hidup, baru matikan satu:

```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
docker kill ziphive-w1
sleep 5
docker ps -a --filter name=ziphive-w --format 'table {{.Names}}\t{{.Status}}'
```

Jangan memakai `sleep` sebelum `docker kill`. Jika `docker ps` sudah tidak menampilkan sembilan baris
`Up`, berarti run sudah selesai; hentikan langkah ini, jalankan ulang Master dan Worker, lalu ulangi.
`docker kill` pada container yang sudah mati akan gagal dengan pesan `is not running` dan bukti
fault-injection tidak terbentuk.

Keluaran yang diharapkan: `ziphive-w1` berstatus `Exited (137)`, delapan Worker lain `Up`.
Master tetap menyelesaikan seluruh task dan berakhir `MASTER OK` (task dari w1 dikerjakan ulang
oleh Worker lain).

**Screenshot #4**: `reports/img/e5-worker-mati.png` — T4 setelah `docker kill`, memuat baris
`Exited (137)` dan delapan `Up`.

### Langkah 4 — tunggu selesai lalu bersihkan

```bash
docker rm -f $(docker ps -aq --filter name=ziphive-w) 2>/dev/null
rm -rf output/demo-e5
```

Jika layar T4 juga ingin memuat `MASTER OK` pada skenario B, ambil screenshot kedua setelah run
selesai; simpan sebagai `reports/img/e5-master-ok.png`.

## 5. Daftar berkas gambar

| Berkas | Isi | Skenario |
|---|---|---|
| `reports/img/10-node-virtual.png` | `docker ps` + `docker inspect` sembilan Worker | A, langkah 4 |
| `reports/img/master-terminal.png` | T1 sampai `MASTER OK` | A, langkah 5 |
| `reports/img/worker-terminal.png` | T2 sampai `WORKER OK (w1)` | A, langkah 5 |
| `reports/img/e5-worker-mati.png` | T4 dengan `Exited (137)` | B, langkah 3 |

## 6. Jika ada masalah

| Gejala | Sebab | Tindakan |
|---|---|---|
| `bind: address already in use` | port 5050 dipakai proses lain | `pkill -f pcomp.master`, ulangi T1 |
| Barrier tidak selesai, task tidak mulai | Worker kurang dari 9 atau salah port | `docker ps`, pastikan sembilan `Up` dan `--master host.docker.internal:5050` |
| Container langsung `Exited (1)` | image atau mount salah | `docker logs ziphive-w1`, pastikan image `ziphive-node:min` dan perintah dijalankan dari root repo |
| `docker: Cannot connect` | Colima berhenti | `colima start`, ulangi |
| Run selesai terlalu cepat untuk screenshot | dataset kecil / repeat kecil | naikkan `--repeat` |

Node pada runbook ini virtual (ADR-015): satu Master di host macOS dan sembilan Worker berupa
container di VM Colima. Screenshot wajib disertai keterangan "10 node virtual" pada laporan.
