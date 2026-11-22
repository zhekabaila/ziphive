# ASSETS.md — Sumber Resmi Aset Pendukung

Soal mewajibkan sumber resmi setiap aset (dataset, formula, file sample). Berkas ini mencatat
tanggal akses, ukuran, dan SHA-256 dari data yang benar-benar ada. Nilai yang belum dapat
diverifikasi tetap ditandai `PERLU DIVERIFIKASI USER` atau `PERLU DIISI USER` dan tidak diisi
dengan tebakan.

Pembaruan terakhir: 2026-11-22 (Fase 10).

## 1. Dataset

| Aset | Sumber resmi | Keterangan | Tanggal akses | Ukuran | SHA-256 |
|---|---|---|---|---|---|
| Dataset sintetis `data/bench` | dibuat `python -m pcomp.tools.make_dataset` | 8 berkas, seed `20261122`, dibuat 2026-11-22T08:34:59+00:00 | 2026-11-22 | 2.147.483.648 byte (2048 MiB) | lihat tabel 1.1 |
| Silesia Corpus | https://sun.aei.polsl.pl/~sdeor/index.php?page=silesia — `PERLU DIVERIFIKASI USER` | 12 berkas, sekitar 211 MB, benchmark kompresi (S. Deorowicz) | TIDAK DIPAKAI | TIDAK ADA DATA | TIDAK ADA DATA |
| Canterbury Corpus (Large) | https://corpus.canterbury.ac.nz/ — `PERLU DIVERIFIKASI USER` | berkas besar untuk benchmark kompresi | TIDAK DIPAKAI | TIDAK ADA DATA | TIDAK ADA DATA |

Silesia dan Canterbury tidak diunduh pada pelaksanaan ini; seluruh eksperimen resmi memakai
dataset sintetis. Kedua tautan belum dibuka ulang oleh agent, sehingga status verifikasinya
diserahkan ke user.

### 1.1 Berkas dataset sintetis

Sumber nilai: `data/bench/dataset.json` (berkas ini ditulis oleh `make_dataset`). Ukuran setiap
berkas 268.435.456 byte (256 MiB).

| Berkas | Jenis | SHA-256 |
|---|---|---|
| `text_00.txt` | teks | `5a37dc2673a19f3db172203d03a675b0876cc0771b795ebfca99f125209cc726` |
| `random_01.bin` | acak | `2239ff7634690f8c7e3710f63983ab0ea203a3eba4c9cbc577b7423b5b826538` |
| `repeat_02.dat` | berulang | `6607b9d8e9c0d859c7d220d15db3cafeb7363e7d6e210c677b33fb7f9f9a2bc9` |
| `mixed_03.dat` | campuran | `6ce486ad5251272294ae1d83de73720d0254f35b212755987968e2ac6c88ac90` |
| `text_04.txt` | teks | `6fe46fe87393262fa8d7ce67bdc9f82d16b0ffba9fef37c5723a07fb6cab9966` |
| `random_05.bin` | acak | `860d2062b4162198c8ace6a57ec445ca53a9ed34fd640cf31123dffec39e2c06` |
| `repeat_06.dat` | berulang | `99434702876bd3e817265127e309dbde18d30e35a2d1b53d99dab745b1b8758d` |
| `mixed_07.dat` | campuran | `6979323e271e249cf41dd1e729f99a8b80a4ba939d757915caca87d0f439ff23` |

Dataset tidak ikut repo (`data/` masuk `.gitignore`). Berkas dapat dibuat ulang dengan seed dan
jumlah berkas yang sama; SHA-256 di atas dapat dipakai untuk memeriksa hasil pembuatan ulang.

## 2. Grafik hasil eksperimen

Berkas di `results/figures/`, dibangun oleh `python -m pcomp.bench.report` (dipanggil harness
`bench/runner.py`) dari `results/summary.csv`.

| Berkas | Ukuran (byte) | SHA-256 |
|---|---|---|
| `cpu_mem.png` | 70.140 | `cae52401b5818eb9f7a4382cdcafd5f9541b07628cd0c23bcd68813f16df3ccc` |
| `efficiency.png` | 45.610 | `5e79d31c83783d6c5e5e4fe4b1a485af1d48882e24a7793e816d68aaaae9ebfd` |
| `recovery_timeline.png` | 71.876 | `3ab0d476e19ba56e72ee980c9659da389f7a4dde1776a05cdecd77ab577f4d1d` |
| `speedup.png` | 48.215 | `649d4024318695095af3c2bf36677f7e7e1e488efee4e75312f77aed5620f977` |
| `throughput.png` | 43.709 | `590bd7098398237ab5f07112f646183afae666cd861c9fe647c05ecddc03ad20` |
| `time_vs_workers.png` | 44.736 | `3181c335592dc2dd5748850116653dc5707de8f9f83f96ef114ef65c0087e68e` |
| `worker_load.png` | 29.328 | `bc2a593d6a5a632edce99a064e1fa2ab8d284ade0d41415146f70c462df4d2d5` |

## 3. Tangkapan layar bukti

Diambil user pada 2026-11-22 sesuai `docs/evidence/RUNBOOK.md`. Berkas berada di `reports/`
yang masuk `.gitignore`, sehingga tidak ikut commit atau ZIP sumber.

| Berkas | Waktu | Ukuran (byte) | SHA-256 |
|---|---|---|---|
| `10-node-virtual.png` | 18.45 | 793.042 | `3bbdea3cd1bec23bee8c54c256d774aae72487e64e4fe600ab1d80c3b5b71a2b` |
| `master-terminal.png` | 18.49 | 273.690 | `dcae054df9de2950f9c14304f3d72477d8f26001d76c3e98e1693f0615f92751` |
| `worker-terminal.png` | 18.52 | 167.855 | `e5f94b0e05b10242d915d204419d163222f3554e6b2a799d0599802d8f63475a` |
| `e5-worker-mati.png` | 19.01 | 316.497 | `47d7597ab59d24172ac9117e9620fb6b17fc76dd2bd1b9d30e2da164377f0da1` |

Isi yang terverifikasi pada setiap gambar dicatat di `docs/evidence/README.md` bagian 3a. Angka
yang terlihat pada gambar berasal dari run bukti, bukan dari eksperimen resmi.

## 4. Pustaka dan dokumentasi

| Aset | Sumber resmi | Versi yang dipakai | Tanggal akses |
|---|---|---|---|
| Python | https://docs.python.org/3/ | 3.11+ (host uji 3.14.4, container Worker 3.12.13) | TIDAK DICATAT |
| `multiprocessing` | https://docs.python.org/3/library/multiprocessing.html | stdlib | TIDAK DICATAT |
| `socket` | https://docs.python.org/3/library/socket.html | stdlib | TIDAK DICATAT |
| `lzma`, `bz2`, `gzip` | https://docs.python.org/3/library/lzma.html, https://docs.python.org/3/library/bz2.html, https://docs.python.org/3/library/gzip.html | stdlib | TIDAK DICATAT |
| `hashlib`, `tomllib` | https://docs.python.org/3/library/hashlib.html, https://docs.python.org/3/library/tomllib.html | stdlib | TIDAK DICATAT |
| psutil | https://psutil.readthedocs.io | `psutil>=5.9` (host 7.2.2, container 5.9.8) | TIDAK DICATAT |
| matplotlib | https://matplotlib.org/stable/ | `matplotlib>=3.7` (host 3.11.2) | TIDAK DICATAT |
| pytest, pytest-cov, pytest-timeout, ruff, mypy, types-psutil | dokumentasi resmi masing-masing proyek | lihat `requirements-dev.txt` | TIDAK DICATAT |

Daftar dependensi resmi ada di `pyproject.toml`, `requirements.txt`, `requirements-worker.txt`,
dan `requirements-dev.txt`. Versi host/container di atas adalah versi yang tercatat pada
pelaksanaan 10 node virtual (`docs/phase-logs/PHASE-08.md` dan `PHASE-09.md`).

## 5. Formula

Rumus yang dipakai implementasi (lihat `src/pcomp/metrics/calc.py`):

| Metrik | Rumus | Implementasi |
|---|---|---|
| Speedup | `S(n) = T_base / T(n)` | `calc.speedup` |
| Efficiency | `E(n) = S(n) / n` | `calc.efficiency` |
| Throughput | `(total byte / MiB) / waktu detik` | `calc.throughput_mbs` |
| Imbalance factor | `max(busy_i) / mean(busy_i)` | `calc.imbalance_factor` |
| Detection latency | `t(worker_dead) - t(kill)` | `calc.detection_latency` |
| Recovery Time | `t(task_done terakhir dari task yang di-requeue) - t(kill)` | `calc.recovery_time` |

Rujukan buku atau paper untuk speedup, efficiency, dan hukum Amdahl: `PERLU DIISI USER` (penulis,
tahun, judul, halaman). Agent tidak mencantumkan rujukan yang belum dapat diverifikasi.

## 6. Lisensi dan ketentuan penggunaan

| Aset | Status |
|---|---|
| Kode ZipHive | Belum ada berkas lisensi di repo; status lisensi `PERLU DIPUTUSKAN USER` |
| Dataset sintetis | Dibuat sendiri oleh `tools/make_dataset.py`; tidak memuat karya pihak lain |
| Silesia Corpus | Ketentuan penggunaan `PERLU DIVERIFIKASI USER` (belum diunduh) |
| Canterbury Corpus | Ketentuan penggunaan `PERLU DIVERIFIKASI USER` (belum diunduh) |

Dataset tidak ikut repo (`data/` di-ignore). Yang disertakan hanya skrip pembuat/unduh dan
checksum, sehingga pemakai harus mengunduh sendiri dari sumber resmi.
