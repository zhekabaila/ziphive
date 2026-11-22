# DEMO_SCRIPT.md — Naskah Video Demo ZipHive

Naskah ini disusun untuk video demo berdurasi maksimal 5 menit sesuai `SUBMISSION.md` bagian 3.
Seluruh angka yang disebut diambil dari `results/summary.csv`, `results/summary_agg.csv`, dan
`docs/ANALYSIS.md`. Perintah yang ditampilkan sudah diuji pada pelaksanaan 10 node virtual
(`docs/evidence/RUNBOOK.md`).

Kalimat dalam tanda kurung siku adalah arahan teknis untuk perekam, bukan untuk dibacakan.

## 1. Tabel adegan

| Menit | Adegan di layar | Narasi |
|---|---|---|
| 0:00-0:30 | Halaman judul bernarasi, lalu tangkapan layar `reports/img/10-node-virtual.png` (daftar sepuluh container beserta hostname dan IP) | Perkenalkan anggota kelompok dan tema 16 Distributed Data Compression. Sebutkan bahwa ZipHive memecah dataset menjadi chunk 4 MiB dan membagikannya ke sembilan Worker melalui TCP. Sebutkan dengan jelas bahwa sepuluh node pada demo ini adalah node virtual pada satu laptop, satu Master di host dan sembilan Worker berupa container, sesuai ADR-015. |
| 0:30-1:00 | Diagram arsitektur Master-Worker (boleh memakai gambar dari laporan, `results/figures/` tidak memuat diagram) | Jelaskan peran Master (chunker, task table, scheduler, monitor, collector) dan peran Worker (klien TCP, `multiprocessing.Pool`, heartbeat). Sebutkan bahwa Worker tidak saling berkomunikasi dan seluruh komunikasi melewati Master. |
| 1:00-2:30 | Terminal Master dan terminal Worker, lalu progres distribusi task | Tunjukkan perintah Master `python -m pcomp.master --input data/bench --out output/demo --expect-workers 9 --scheduler dynamic --host 0.0.0.0 --port 5050` dan perintah satu Worker sebagai contoh (`python3 -m pcomp.worker --master host.docker.internal:5050 --id w1 --procs 1`). Tunjukkan sembilan Worker mendaftar, progres task berjalan, dan distribusi task per Worker. Sebutkan bahwa scheduler dynamic memberi task sesuai permintaan credit sehingga Worker cepat menerima lebih banyak task. |
| 2:30-3:30 | Terminal tempat satu container dimatikan, lalu event Master | Hentikan satu Worker dengan `docker kill ziphive-w9`. Tunjukkan event `worker_dead` dan `task_requeued` pada Master. Sebutkan angka nyata: detection latency 0,26 ± 0,09 detik dan recovery time 1,37 ± 0,70 detik pada skenario satu Worker mati, serta run tetap selesai dengan `VERIFY OK`. |
| 3:30-4:30 | Grafik `results/figures/speedup.png`, `time_vs_workers.png`, dan terminal `VERIFY OK` | Sebutkan angka utama: sequential 143,56 ± 6,79 detik, terdistribusi sembilan Worker 62,31 ± 5,84 detik dengan speedup 2,301 ± 0,205, dan w = 6 serta w = 9 praktis sama (79,28 dan 79,32 detik) karena VM hanya 6 vCPU. Sebutkan bahwa seluruh 45 run berakhir `VERIFY OK` dan hasil 45 run tervalidasi. |
| 4:30-5:00 | Halaman penutup bernarasi | Sampaikan kesimpulan singkat: sistem berjalan, load balancing dynamic menurunkan makespan 14,4 persen dibanding static, fault tolerance bekerja, dan batas performa berasal dari kapasitas CPU VM serta pemrosesan berurutan di Master. Sebutkan bahwa keterbatasan node virtual diungkap pada laporan. |

## 2. Perintah yang ditampilkan

Disiapkan sebelum merekam agar tidak ada waktu tunggu yang terbuang.

```bash
# 1. Master di host
PYTHONPATH=src python -m pcomp.master --input data/bench --out output/demo \
  --expect-workers 9 --scheduler dynamic --host 0.0.0.0 --port 5050

# 2. Sembilan Worker (satu perintah per container)
for i in $(seq 1 9); do
  docker run -d --name "ziphive-w$i" --hostname "w$i" \
    -v "$PWD":/app:ro -e PYTHONPATH=/app/src -w /app ziphive-node:min \
    python3 -m pcomp.worker --master host.docker.internal:5050 --id "w$i" --procs 1
done

# 3. Daftar node dan IP untuk adegan 0:00-0:30
docker ps --format '{{.Names}}\t{{.Ports}}' && docker inspect -f '{{.Name}} {{.NetworkSettings.IPAddress}}' $(docker ps -q)

# 4. Bukti fault tolerance
docker kill ziphive-w9

# 5. Verifikasi hasil setelah run selesai
python -m pcomp.tools.verify --manifest output/demo/manifest.json
```

Perintah nomor 2 hanya contoh pengulangan. Pada pelaksanaan nyata, sembilan Worker dijalankan
satu per satu mengikuti `DEPLOYMENT.md` bagian 0 agar log tiap container dapat diperiksa.

## 3. Checklist rekaman

- [ ] Resolusi 1920x1080, perekaman layar penuh tanpa notifikasi sistem.
- [ ] Ukuran huruf terminal minimal 14 pt agar terbaca setelah dikompresi ke MP4.
- [ ] Tangkapan layar sepuluh node virtual (`reports/img/10-node-virtual.png`) ditampilkan pada 30 detik pertama, termasuk hostname dan IP.
- [ ] Kalimat "sepuluh node virtual pada satu laptop" diucapkan minimal satu kali dan terbaca pada layar.
- [ ] Tidak ada angka yang disebut selain angka pada `docs/ANALYSIS.md`.
- [ ] Adegan 1:00-2:30 memperlihatkan sembilan Worker terdaftar, bukan tiga Worker.
- [ ] Adegan 2:30-3:30 memperlihatkan event `worker_dead` dan `task_requeued` pada keluaran Master.
- [ ] Adegan 3:30-4:30 memperlihatkan keluaran `VERIFY OK` dari terminal.
- [ ] Durasi total tidak melebihi 5 menit; potong bagian menunggu, jangan mempercepat rekaman hingga angka sulit dibaca.
- [ ] Berkas akhir disimpan sebagai MP4 (H.264, 1080p) dengan nama `ziphive-demo.mp4`.
- [ ] Audio dinormalisasi dan tidak ada bagian yang senyap tanpa keterangan.

## 4. Bahan yang harus disiapkan sebelum merekam

| Bahan | Lokasi | Catatan |
|---|---|---|
| Dataset sinkron 2048 MiB | `data/bench` | Dibuat dengan `python -m pcomp.tools.make_dataset --out data/bench --size-mb 2048 --seed 20261122 --files 8` |
| Image container Worker | `ziphive-node:min` | Dibangun sesuai `DEPLOYMENT.md` bagian 0 |
| Tangkapan layar sepuluh node | `reports/img/10-node-virtual.png` | Diambil 2026-11-22 pukul 18.45 |
| Grafik hasil | `results/figures/speedup.png`, `results/figures/time_vs_workers.png` | Dibuat oleh `python -m pcomp.bench.report` |
| Keluaran `VERIFY OK` | `results/raw/E3/<run_id>/verify.log` | Dapat ditampilkan sebagai bukti, bukan sebagai run demo baru |

Satu run demo 2048 MiB memerlukan waktu sekitar 62 detik pada sembilan Worker (angka E3). Bila
waktu perekaman terbatas, demo boleh memakai dataset 64 MiB seperti pada `DEPLOYMENT.md` bagian 0.
Pada kasus itu angka hasil eksperimen resmi tetap disebut sebagai angka laporan, bukan angka demo.
