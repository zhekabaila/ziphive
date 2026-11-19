# SUBMISSION.md — Paket Pengumpulan

## 1. Source code (ZIP atau RAR)
Dibuat oleh `python scripts/pack_source.py`. Isi: `src/`, `tests/`, `scripts/`, `config/`, dokumen `.md`, `pyproject.toml`, `requirements*.txt`, `results/` (ringkasan dan grafik), `docs/`. Tanpa `data/`, `output/`, `.venv`, `.git`. Periksa bahwa kode Master, Worker, komunikasi, load balancing, fault tolerance, dan pengukuran performa ada.

## 2. Laporan (DOCX, gaya skill `laporan-akademik-id`)
| Bagian | Isi | Sumber di repo |
|---|---|---|
| BAB I Pendahuluan | Latar belakang (komputasi paralel, kompresi data, alasan Master–Worker), Tujuan | ASSETS.md, README |
| BAB II Studi Pustaka | Komputasi paralel dan terdistribusi, Master–Worker, multiprocessing, load balancing, fault tolerance, algoritma kompresi, metrik (speedup, efficiency) | ASSETS.md |
| BAB III Metodologi | Rancangan percobaan (E1 sampai E7), arsitektur dan topologi, mekanisme kerja (task decomposition, protokol, scheduler, heartbeat), konfigurasi node dan jaringan | ARCHITECTURE, FLOW, PROTOCOL, EXPERIMENTS, DEPLOYMENT |
| BAB IV Hasil dan Pembahasan | Implementasi, hasil pengukuran (tabel dan grafik), analisis data tiap eksperimen | CODE_GUIDE, results/, ANALYSIS |
| Kesimpulan | Jawaban atas tujuan, keterbatasan, saran | ANALYSIS |

Aturan: bahasa formal mahasiswa, tanpa simbol khas AI, setiap gambar diberi nomor, keterangan, dan placeholder dengan instruksi pengambilan gambar. Daftar gambar yang perlu diambil manual: topologi fisik 10 node (foto), terminal Master dan 9 Worker berjalan, dashboard atau grafik hasil, bukti Worker dimatikan lalu pulih. Sertakan sumber aset sesuai ASSETS.md. Isi identitas kelompok dari `config/group.toml`.

## 3. Video demo (maks 5 menit, MP4)
| Menit | Isi |
|---|---|
| 0:00-0:30 | Perkenalan kelompok, tema, foto 10 node fisik |
| 0:30-1:00 | Arsitektur singkat |
| 1:00-2:30 | Jalankan Master dan 9 Worker, tunjukkan progres dan distribusi task per Worker |
| 2:30-3:30 | Matikan satu Worker, tunjukkan deteksi dan requeue, run tetap selesai |
| 3:30-4:30 | Ringkasan hasil: speedup dan scalability, `VERIFY OK` |
| 4:30-5:00 | Penutup |
Bukti 10 node fisik harus terlihat jelas (kamera atau daftar IP dan hostname di layar masing-masing).

## 4. Checklist akhir
- [ ] Gate penuh lulus di `main`, tag `v1.0.0`
- [ ] Uji clone bersih berhasil
- [ ] Laporan lengkap, nomor gambar dan tabel konsisten
- [ ] Angka di laporan sama dengan `results/summary.csv`
- [ ] ZIP terbuat dan isinya diperiksa
- [ ] Video MP4 maksimal 5 menit
