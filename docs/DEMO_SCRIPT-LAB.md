# Naskah Video Demo ZipHive — 1 Master + 9 Worker Fisik (maks 5 menit)

Naskah ini dipakai untuk merekam video demo di lab dengan **10 perangkat fisik** (1 laptop Master +
9 laptop Worker) sesuai ADR-016. Durasi ketat **5 menit**. Tiga orang berbicara bergiliran, jadi
setiap orang hanya membaca bagiannya sendiri.

Aturan utama:

1. **Jangan menyebut angka yang tidak ada di berkas hasil.** Semua angka diisi pada bagian 4
   sebelum merekam.
2. Kalimat di dalam `[...]` adalah arahan teknis, **bukan** untuk dibacakan.
3. Bicara santai, tidak perlu hafal. Yang penting urutan dan angka benar.

## 1. Pembagian peran

| Peran | Tugas | Bagian |
|---|---|---|
| P1 — operator | menjalankan Master, memantau terminal, menyebut hasil eksperimen | 0:00–0:20, 1:30–1:45, 3:45–4:35 |
| P2 — arsitektur | menjelaskan rancangan dan cara kerja sistem | 0:20–0:55, 1:45–2:15, 3:15–3:45 |
| P3 — hasil | menjelaskan dataset, kegagalan Worker, dan kesimpulan | 0:55–1:30, 2:15–3:15, 4:35–5:00 |

Isi nama: P1 = ____________, P2 = ____________, P3 = ____________.

## 2. Alur waktu

| Waktu | Layar | Pembicara |
|---|---|---|
| 0:00–0:20 | sembilan jendela Worker + terminal Master | P1 |
| 0:20–0:55 | diagram arsitektur (gambar laporan atau `ARCHITECTURE.md`) | P2 |
| 0:55–1:30 | `data/demo` dan isi `dataset.json` | P3 |
| 1:30–1:45 | Master dijalankan | P1 |
| 1:45–2:15 | sembilan Worker mendaftar | P2 |
| 2:15–3:15 | log event berjalan, Worker dimatikan, requeue | P3 |
| 3:15–3:45 | `MASTER OK`, tabel task per Worker, `VERIFY OK` | P2 |
| 3:45–4:35 | grafik `results/figures/` | P1 |
| 4:35–5:00 | halaman penutup | P3 |

## 3. Naskah

### 0:00–0:20 — Pembuka (P1)

[Layar: sembilan jendela Worker di latar, terminal Master di depan.]

> Selamat pagi. Kami Kelompok 3, mata kuliah Komputasi Paralel dan Sistem Terdistribusi, tema enam
> belas, Distributed Data Compression. Sistem kami bernama ZipHive. Di depan kami ada satu laptop
> Master dan sembilan laptop Worker yang tersambung pada satu jaringan lab.

### 0:20–0:55 — Arsitektur (P2)

[Layar: diagram arsitektur Master–Worker dari laporan.]

> ZipHive memakai arsitektur Master–Worker. Master memecah dataset menjadi chunk, mencatat setiap
> chunk sebagai task, membagikan task sesuai permintaan credit, memantau heartbeat, lalu
> mengumpulkan hasil dan memverifikasi SHA-256. Worker hanya menerima task, mengompresinya dengan
> multiprocessing, dan mengirim hasil kembali. Worker tidak saling berkomunikasi. Sepuluh node ini
> perangkat fisik, bukan virtual.

### 0:55–1:30 — Dataset dan task (P3)

[Layar: `ls -lh data/demo` lalu isi `data/demo/dataset.json`.]

> Dataset demo berukuran 256 MiB dengan chunk 4 MiB, sehingga terbentuk enam puluh lima task.
> Setiap task punya hash sendiri agar hasilnya bisa diverifikasi. Scheduler dynamic memilih task
> terbesar lebih dulu, dan Worker yang lebih cepat otomatis menerima lebih banyak task.

### 1:30–1:45 — Master dijalankan (P1)

[Layar: jalankan perintah Master. Biarkan perintah terlihat diketik.]

> Kami nyalakan Master dengan sembilan Worker yang ditunggu, dan sekaligus mengaktifkan injeksi
> kegagalan satu Worker pada lima puluh persen progres.

### 1:45–2:15 — Sembilan Worker mendaftar (P2)

[Layar: sembilan jendela Worker, lalu log Master yang menampilkan Worker terdaftar.]

> Sembilan laptop Worker menyambung lewat TCP ke port lima ribu lima puluh. Setiap Worker memakai
> satu proses kompresi. Master menunggu sampai kesembilan Worker terdaftar sebelum mulai, supaya
> perbandingan antar konfigurasi tetap adil.

### 2:15–3:15 — Run berjalan dan satu Worker mati (P3)

[Layar: panel `tail -f output/demo/events.jsonl`. Saat Worker dimatikan, sorot baris
`worker_exit_injected`, `worker_dead`, dan `task_requeued`.]

> Run berjalan, dan log event menunjukkan task selesai satu per satu. Pada lima puluh persen
> progres, Master mengirim pesan KILL ke satu Worker. Worker itu keluar tanpa mengirim BYE, sama
> seperti proses yang mati mendadak. Master mencatat waktu injeksi, mendeteksi koneksi putus,
> mengembalikan task yang sedang dikerjakan ke antrean, lalu delapan Worker lain melanjutkan
> sampai seluruh task selesai.

### 3:15–3:45 — Hasil run (P2)

[Layar: `MASTER OK`, tabel task per Worker, lalu `VERIFY OK`.]

> Run selesai dengan MASTER OK. Seluruh task berhasil, tidak ada yang gagal, dan verifikasi manifest
> menghasilkan VERIFY OK. Tabel ini menunjukkan jumlah task per Worker, bukti bahwa beban terbagi
> dan task yang tertinggal tetap dikerjakan ulang.

### 3:45–4:35 — Hasil eksperimen E1–E6 (P1)

[Layar: `results/figures/speedup.png` dan `time_vs_workers.png`.]

> Untuk evaluasi, kami menjalankan eksperimen E1 sampai E6. Sequential butuh ⟨a⟩ detik, sedangkan
> sembilan Worker butuh ⟨b⟩ detik, dengan speedup ⟨c⟩ kali. Scheduler dynamic lebih cepat ⟨d⟩
> persen dibanding static. Deteksi kegagalan memerlukan ⟨e⟩ detik dan pemulihan ⟨f⟩ detik.
> Penambahan Worker dari enam ke sembilan tidak lagi menambah kecepatan karena kapasitas CPU tiap
> laptop sudah terpakai penuh.

### 4:35–5:00 — Penutup (P3)

[Layar: halaman penutup bernarasi.]

> Kesimpulan kami, ZipHive berjalan pada sepuluh perangkat fisik, load balancing bekerja, fault
> tolerance bekerja, dan seluruh hasil terverifikasi. Keterbatasannya, Master masih menjadi satu
> titik kegagalan dan pengukuran dilakukan pada jaringan lab. Terima kasih.

## 4. Angka yang wajib diisi sebelum merekam

Isi ⟨a⟩ sampai ⟨f⟩ dari hasil eksperimen yang benar-benar ada. Jalankan di laptop Master:

```bash
.venv/bin/python - <<'PY'
import csv
rows = list(csv.DictReader(open("results/summary_agg.csv")))
for r in rows:
    print(r["exp"], "w=" + r["workers"], r["scheduler"],
          "time", round(float(r["time_s_mean"]), 2),
          "speedup", round(float(r["speedup_seq_mean"]), 3),
          "detect", r["detect_s_mean"][:5], "recovery", r["recovery_s_mean"][:5])
PY
```

| Isi | Arti | Sumber kolom |
|---|---|---|
| ⟨a⟩ | waktu sequential (E1) | `time_s_mean` pada baris `E1` |
| ⟨b⟩ | waktu 9 Worker (E3) | `time_s_mean` pada baris `E3` `w=9` |
| ⟨c⟩ | speedup 9 Worker | `speedup_seq_mean` pada baris `E3` `w=9` |
| ⟨d⟩ | selisih static vs dynamic (E4) | hitung dari dua baris `E4` |
| ⟨e⟩ | lama deteksi E5 | `detect_s_mean` pada baris `E5` |
| ⟨f⟩ | lama pemulihan E5 | `recovery_s_mean` pada baris `E5` |

Bila hasil run fisik belum ada di `summary_agg.csv`, sebut angka yang tersedia dan **sebutkan
sumbernya** ("dari 45 run sebelumnya"). Jangan mencampur dua sumber tanpa keterangan.

## 5. Perintah yang disiapkan (jalankan sebelum merekam)

### 5.1 Laptop Master (macOS)

```bash
cd ~/ziphive

# dataset demo 256 MiB (sekali saja, deterministik: 65 task)
.venv/bin/python -m pcomp.tools.make_dataset --out data/demo --size-mb 256 --files 4 --seed 20261122

# IP Master untuk sembilan laptop Worker
.venv/bin/python scripts/start_master.py --print-plan --workers 9
```

### 5.2 Sembilan laptop Worker

| OS | Perintah |
|---|---|
| macOS | `./start-worker.command` |
| Linux | `./start-worker.sh` |
| Windows | `start-worker.bat` |

Isi `IP Master` (tanpa port) dan `id` `w1` sampai `w9` (satu ID per laptop, tidak boleh sama).

### 5.3 Master saat merekam

```bash
.venv/bin/python scripts/start_master.py --workers 9 --input data/demo --out output/demo \
  --inject-kills 1 --inject-kill-fraction 0.5
```

Panel kedua untuk memperlihatkan progres dan kegagalan:

```bash
tail -f output/demo/events.jsonl
```

### 5.4 Setelah run selesai (adegan 3:15–3:45)

```bash
# 1. verifikasi hasil
.venv/bin/python -m pcomp.tools.verify --manifest output/demo/manifest.json

# 2. tabel task per Worker
.venv/bin/python - <<'PY'
import json
m = json.load(open("output/demo/metrics.json"))
print(f'{"id":>3} {"hostname":<16} {"task":>4} {"busy_s":>7}')
for w in m["worker_stats"]:
    print(f'{w["worker_id"]:>3} {w["hostname"]:<16} {w["tasks_done"]:>4} {w["busy_sec"]:>7.1f}')
print("tasks_ok", m["tasks_ok"], "dari", m["tasks"], "| gagal", m["tasks_failed"])
print("ratio", round(m["ratio"], 2), "| waktu", round(m["time_s"], 1), "s",
      "| throughput", round(m["throughput_mbs"], 2), "MB/s")
PY

# 3. lama deteksi dan pemulihan (E5)
.venv/bin/python - <<'PY'
import json
rows = [json.loads(line) for line in open("output/demo/events.jsonl")]
inj = [r for r in rows if r["event"] == "worker_exit_injected"]
dead = [r for r in rows if r["event"] == "worker_dead"]
if inj and dead:
    print("deteksi =", round(dead[0]["ts"] - inj[0]["ts"], 2), "detik")
print("task dikembalikan ke antrean =",
      sum(1 for r in rows if r["event"] == "task_requeued"))
PY
```

## 6. Checklist

### H-15 menit sebelum merekam

- [ ] Semua laptop memakai versi sama: `.venv/bin/python -m pcomp --version` → `ZipHive 1.1.0`
      (Windows: `.venv\Scripts\python.exe -m pcomp --version`).
- [ ] Sembilan laptop pada jaringan yang sama, `check_node.py --ping-master <IP>:5050` → OK.
- [ ] Firewall Master mengizinkan Python menerima koneksi masuk.
- [ ] Dataset `data/demo` sudah ada dan berisi 65 task.
- [ ] Semua laptop tersambung listrik, mode hemat daya mati, notifikasi sistem dimatikan.
- [ ] Angka ⟨a⟩–⟨f⟩ sudah ditulis di kertas atau catatan, tidak dibaca dari layar.
- [ ] Satu kali gladi resik penuh sambil mengukur durasi; potong bagian yang terlalu panjang.

### Saat merekam

- [ ] Resolusi 1920x1080, ukuran huruf terminal minimal 14 pt.
- [ ] Sembilan jendela Worker benar-benar terlihat, bukan tiga.
- [ ] Kalimat "sepuluh node ini perangkat fisik" diucapkan satu kali (adegan 0:20–0:55).
- [ ] Event `worker_exit_injected`, `worker_dead`, dan `task_requeued` terlihat di layar.
- [ ] Keluaran `VERIFY OK` terlihat.
- [ ] Tidak ada angka yang disebut di luar tabel bagian 4.
- [ ] Durasi total ≤ 5 menit; berkas akhir MP4 H.264 1080p bernama `ziphive-demo.mp4`.

## 7. Rencana cadangan

| Kejadian | Tindakan |
|---|---|
| Satu Worker tidak mendaftar | Nyalakan ulang launcher di laptop itu; Master tetap menunggu sampai `--lan-wait` |
| Run terlalu lama (> 2 menit) | Hentikan, pakai `--size-mb 128 --files 4`, dan sebutkan ukuran dataset di narasi |
| Master gagal start | Pastikan port 5050 bebas: `lsof -nP -iTCP:5050 -sTCP:LISTEN` |
| Waktu rekaman mepet | Lewati adegan 3:45–4:35 (grafik), langsung ke penutup |
| Ada laptop mati saat run | Justru bagus untuk adegan 2:15–3:15; tetap sorot `worker_dead` dan `task_requeued` |
