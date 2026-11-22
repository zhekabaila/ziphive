# DEPLOYMENT-PHYSICAL.md — Menjalankan di 10 Perangkat Fisik

Runbook ini dipakai untuk eksperimen resmi E1 sampai E6 pada **1 Master + 9 Worker berupa laptop
fisik** dalam satu jaringan (hotspot telepon genggam atau router), tanpa ssh dan tanpa Docker.
Sistem operasi campuran (macOS, Windows, Linux) didukung oleh launcher yang sama.

Berkas ini menggantikan mode 10 node virtual (ADR-015) dengan 10 perangkat fisik (ADR-016).
Panduan node virtual tetap ada di `DEPLOYMENT.md` untuk keperluan reproduksi hasil lama.

## 1. Ringkasan alur

```
Laptop Master (milik Anda)               9 laptop Worker (teman)
---------------------------              -----------------------
1. clone / ekstrak repo                  1. clone / ekstrak repo
2. setup-node  -> .venv + psutil         2. setup-node  -> .venv + psutil
3. start-worker? tidak perlu             3. start-worker (sekali, biarkan terbuka)
4. run_experiments --worker-mode external
   (Master + dataset + orkestrasi 45 run)
```

Master menjalankan harness `scripts/run_experiments.py`; setiap run menyalakan Master baru pada
port yang sama (5050). Worker di laptop teman berjalan terus dan otomatis menyambung ulang ke run
berikutnya, jadi operator tidak perlu menyentuh laptop Worker lagi.

## 2. Persiapan laptop Master (1 laptop)

Prasyarat: Python 3.11 atau lebih baru. Pada macOS, `python3` bawaan Xcode Command Line Tools
biasanya 3.9 sehingga harus diganti dengan Python dari python.org atau Homebrew.

1. Dapatkan kode:
   - `git clone https://github.com/zhekabaila/ziphive.git` lalu `cd ziphive`, atau
   - ekstrak `dist/ziphive-source-1.1.0.zip`.
2. Siapkan lingkungan (sekali saja):
   - macOS: klik dua kali `setup-node.command` (atau `./setup-node.command`)
   - Linux: `./setup-node.sh`
   - Windows: klik dua kali `setup-node.bat`
   Perintah ini membuat `.venv` **di dalam folder proyek** (Python sistem tidak diubah), memasang
   paket `pcomp` beserta `psutil`, lalu menjalankan `scripts/check_node.py`. Berhasil bila
   baris terakhir `SETUP OK`.
3. Periksa IP laptop Master: `python scripts/start_master.py --print-plan --workers 9`.
   Baris pertama menampilkan `Master : <IP>:5050`. IP ini yang dipakai semua laptop Worker.
4. Bila memakai Windows, izinkan Python pada firewall saat diminta (jaringan privat).

## 3. Persiapan 9 laptop Worker

Prasyarat sama: Python 3.11 atau lebih baru. Windows: saat memasang Python dari python.org,
centang **Add python.exe to PATH** dan hindari alias Microsoft Store.

1. Clone atau ekstrak repo yang sama (`main` versi 1.1.0). Semua node wajib memakai versi paket
   yang sama; versi berbeda ditolak saat REGISTER (`VERSION_MISMATCH`).
2. Jalankan `setup-node` (`.command`, `.sh`, atau `.bat`) sampai muncul `SETUP OK`.
3. Jalankan `start-worker`:
   - macOS: klik dua kali `start-worker.command`
   - Linux: `./start-worker.sh`
   - Windows: klik dua kali `start-worker.bat`

   Pada pemanggilan pertama launcher bertanya dua hal:
   ```
   IP Master (tanpa port, port 5050): 192.168.43.10
   ID Worker (mis. w1): w3
   ```
   Jawaban disimpan di `config/worker.local.toml`, sehingga pemanggilan berikutnya tidak bertanya
   lagi. Nomor ID harus unik: w1 sampai w9.
4. Biarkan jendela launcher terbuka. Keluaran yang benar saat run berjalan:
   ```
   WORKER OK (w3)          <- run selesai, menunggu run berikutnya
   ```
5. Tanpa dataset di laptop Worker: mode resmi hanya `transfer`, seluruh chunk dikirim Master.
   Dataset cukup ada di laptop Master.

Perintah yang sama dapat dijalankan langsung tanpa wrapper:

```bash
.venv/bin/python scripts/start_worker.py --master 192.168.43.10:5050 --id w3
# Windows: .venv\Scripts\python.exe scripts\start_worker.py --master 192.168.43.10:5050 --id w3
```

## 4. Jaringan

- Semua laptop pada hotspot/router yang sama. Port **5050/tcp** harus dapat dijangkau dari Worker
  ke Master; arah sebaliknya tidak dibutuhkan.
- Uji cepat dari laptop Worker sebelum eksperimen:
  ```bash
  .venv/bin/python scripts/check_node.py --ping-master 192.168.43.10 --port 5050
  ```
  Baris `master` harus `OK`.
- Hotspot telepon genggam sering memakai **client isolation** (klien tidak dapat saling
  menghubungi). Bila `check_node.py` gagal padahal IP benar, pindah ke router Wi-Fi biasa atau
  gunakan hotspot dengan opsi isolasi dimatikan.
- Nyalakan laptop dengan sumber listrik. Mode hemat daya macOS/Windows dapat memperlambat Worker
  dan mencemari hasil.

## 5. Menjalankan eksperimen resmi

Seluruh orkestrasi dijalankan **di laptop Master**:

```bash
.venv/bin/python scripts/run_experiments.py --worker-mode external --port 5050 --exps E6,E3,E4,E5
```

Perilaku tiap eksperimen:

| Eksperimen | Butuh Worker | Catatan |
|---|---|---|
| E1 | tidak | baseline sequential di laptop Master |
| E2 | tidak | local parallel di laptop Master (procs 1,2,4,8) |
| E3 | 9 | satu run 9 Worker, scheduler dynamic |
| E4 | 9 | dua run (static, dynamic); **w9 wajib `--throttle 0.25`** |
| E5 | 9 | dua skenario: 1 Worker dan 3 Worker dimatikan Master |
| E6 | 1 sampai 9 | jumlah Worker 1,2,4,6,9 |

Urutan yang disarankan: **E1, E2** (Master sendiri, laptop teman boleh menunggu) lalu
**E6, E3, E4, E5**. Dengan urutan ini laptop teman cukup dinyalakan sekali dan tidak perlu
dimatikan di tengah rangkaian.

### 5.1 E4 — Worker lambat

E4 membandingkan scheduler static dan dynamic dengan satu Worker sengaja diperlambat. Sebelum
menjalankan E4, di laptop **w9** hentikan launcher (Ctrl+C) lalu jalankan:

```bash
.venv/bin/python scripts/start_worker.py --throttle 0.25
# atau cukup tambahkan --throttle 0.25 pada wrapper start-worker
```

Nilai itu tersimpan, jadi cukup sekali. **Setelah E4 selesai**, kembalikan ke normal sebelum E5
dan E6:

```bash
.venv/bin/python scripts/start_worker.py --throttle 0
```

Harness mencetak pengingat ini pada awal setiap run E4. `procs` per Worker divalidasi otomatis
(harus 1); `throttle` tidak dapat diperiksa dari Master sehingga kesalahan di sini tidak terdeteksi
dan menjadi tanggung jawab operator.

### 5.2 E5 — Worker dimatikan

Master sendiri yang mematikan Worker lewat pesan `KILL` setelah sebagian task selesai
(`--inject-kills`). Tidak ada aksi manual dari laptop Worker.

- Worker yang dimatikan keluar tanpa `BYE`, Master mencatat `worker_exit_injected` lalu
  `worker_dead` pada jam Master, task yang sedang dikerjakan dikembalikan ke antrean.
- Launcher di laptop Worker otomatis mencoba menyambung lagi, tetapi Master menolak dengan
  `SERVER_FULL` sampai run itu selesai. Jadi jumlah Worker pada run tetap sesuai konfigurasi.
- Dua skenario dijalankan berurutan; `run_experiments.py` menangani keduanya otomatis.

Metrik yang dihasilkan per run: `detect_s` (lama deteksi) dan `recovery_s` (lama pemulihan) pada
`summary.csv`, serta `worker_exit_injected`, `worker_dead`, `task_requeued` pada `events.jsonl`.

### 5.3 Satu run manual (demo atau uji coba)

Untuk demonstrasi di depan kelas atau uji coba 1–2 laptop:

```bash
# laptop Master
.venv/bin/python scripts/start_master.py --workers 2 --input data/bench --port 5050

# laptop Worker 1 dan 2
.venv/bin/python scripts/start_worker.py --master 192.168.43.10:5050 --id w1
.venv/bin/python scripts/start_worker.py --master 192.168.43.10:5050 --id w2
```

`start_master.py` membuat dataset 2048 MiB (8 berkas, seed 20261122) bila belum ada, mencetak
perintah untuk setiap Worker, lalu menjalankan Master. Master keluar sendiri setelah semua task
selesai dan mencetak `MASTER OK`. Untuk mencetak rencana tanpa menjalankan Master, tambahkan
`--print-plan` (mencetak `PLAN OK`).

## 6. Perkiraan waktu dan bandwidth

- Dataset resmi 2048 MiB dengan chunk 4 MiB menghasilkan sekitar 512 task.
- Setiap run mengirim sekitar 2 GiB chunk dari Master ke Worker dan menerima kembali hasil
  terkompresi (kolom `total_comp_bytes` pada `metrics.json`). Rangkaian resmi 45 run berarti
  sekitar 90 GiB data keluar dari laptop Master.
- Hotspot 4G biasanya 5–20 Mbit/s untuk 9 klien; dengan kecepatan itu satu run dapat memakan
  waktu jauh lebih lama daripada batas `--timeout` (1800 detik) dan seluruh rangkaian menjadi
  tidak realistis. **Gunakan router Wi-Fi 5 GHz atau kabel LAN.**
- Bila jaringan tidak memadai, turunkan dataset (`--size-mb 512 --files 8`) dan catat perubahan
  itu di laporan; seluruh angka BAB IV harus dibangun ulang dari data baru.

## 7. Checklist sebelum menekan Enter

- [ ] Semua laptop memakai versi paket yang sama (`python -m pcomp --version`).
- [ ] `check_node.py --ping-master <IP_MASTER> --port 5050` OK di kesembilan laptop.
- [ ] Dataset 2048 MiB sudah ada di laptop Master (`data/bench`), atau biarkan
      `start_master.py` membuatnya sekali.
- [ ] Tidak ada aplikasi berat lain (browser puluhan tab, game, sinkronisasi cloud) di semua laptop.
- [ ] Semua laptop tersambung listrik dan mode hemat daya dimatikan.
- [ ] w9 memakai `--throttle 0.25` hanya untuk E4 dan `0` untuk eksperimen lain.
- [ ] Folder `results/raw` di laptop Master kosong atau sudah dibackup.
- [ ] Catat tanggal, jumlah core, RAM, dan sistem operasi setiap laptop untuk metadata laporan.

## 8. Mengumpulkan bukti dan data

1. Di laptop Master, seluruh hasil berada di `results/raw/<exp>/<run_id>/` ditambah
   `results/summary.csv`, `results/summary_agg.csv`, dan `results/figures/`.
2. Log Worker tersimpan di laptop masing-masing pada `logs/worker-<id>.log`. Untuk bukti E5,
   minta pemilik laptop w1 sampai w3 mengirim berkas log itu (berisi baris
   `WORKER DIMATIKAN MASTER`).
3. Tangkapan layar yang dibutuhkan laporan: sembilan jendela Worker aktif, terminal Master,
   dan momen satu Worker mati pada E5. Prosedur gambar ada di `docs/evidence/RUNBOOK.md`.
4. `scripts/pack_source.py` membuat ZIP sumber untuk dibagikan ke laptop lain bila tidak memakai
   git.

## 9. Troubleshooting

| Gejala | Penyebab umum | Tindakan |
|---|---|---|
| `SETUP GAGAL: butuh Python 3.11` | Python sistem terlalu lama (macOS Xcode 3.9, Debian 11) | Pasang Python 3.11+ dari python.org/Homebrew/backports, jalankan ulang `setup-node` |
| `WORKER GAGAL: --master dan --id wajib diisi` | launcher dijalankan non-interaktif | Berikan `--master` dan `--id` pada pemanggilan pertama |
| `WORKER DITOLAK SERVER_FULL` berulang | Worker berlebih, atau Worker yang baru dimatikan Master pada E5 | Normal; launcher mencoba lagi sampai run berganti. Bila terus terjadi, ada lebih dari 9 Worker menyala |
| `WORKER DITOLAK VERSION_MISMATCH` | Versi kode berbeda antar laptop | Samakan versi (clone/pull ulang), jalankan `setup-node` lagi |
| `MASTER GAGAL: hanya N dari 9 Worker terdaftar` | Laptop belum menyala, IP salah, atau hotspot mengisolasi klien | Cek `check_node.py --ping-master`, ganti jaringan, jalankan ulang |
| Worker tidak menemukan Master | IP Master berubah (hotspot memberi IP baru) | Lihat IP terbaru pada `start_master.py --print-plan`, perbarui `config/worker.local.toml` |
| Run sangat lambat | Wi-Fi 2,4 GHz, hemat daya, atau isolasi klien | Pindah ke 5 GHz/kabel, matikan hemat daya |
| `procs Worker harus 1` | `procs` di laptop Worker bukan 1 | `--procs 1` pada launcher Worker |
| Windows: `python` membuka Microsoft Store | Alias bawaan Windows | Matikan alias di Settings > Apps > App execution aliases, atau pakai `py -3` |

## 10. Setelah data fisik tersedia

Angka pada laporan lama berasal dari 10 node virtual (ADR-015). Setelah rangkaian fisik selesai:

1. Jalankan `python -m pcomp.tools.validate_results results/raw`.
2. Bangun ulang grafik dan agregat dari `summary.csv` baru.
3. Perbarui `docs/ANALYSIS.md` dan seluruh angka BAB IV dari `summary_agg.csv`.
4. Ganti ADR-015 dengan ADR-016, perbarui tabel node pada BAB III, dan isi tiga placeholder
   gambar dengan tangkapan layar asli.
5. Sebutkan pada laporan: jumlah node, sistem operasi tiap node, topologi jaringan, dan waktu
   pelaksanaan.
