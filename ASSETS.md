# ASSETS.md — Sumber Resmi Aset Pendukung

Soal mewajibkan sumber resmi setiap aset (dataset, formula, file sample). Agent mengisi kolom tanggal akses, ukuran, dan SHA-256 saat mengunduh (fase 2 dan 10). Tautan harus dibuka dan diverifikasi sebelum dimasukkan ke laporan.

## Dataset
| Aset | Sumber resmi | Keterangan | Tanggal akses | SHA-256 |
|---|---|---|---|---|
| Silesia Corpus | https://sun.aei.polsl.pl/~sdeor/index.php?page=silesia | 12 file, sekitar 211 MB, benchmark kompresi (S. Deorowicz) | diisi user | diisi user |
| Canterbury Corpus (Large) | https://corpus.canterbury.ac.nz/ | file besar benchmark kompresi | diisi user | diisi user |
| Dataset sintetis | dibuat oleh `tools/make_dataset.py` | seed dicatat, tidak ada hak cipta pihak lain | diisi user | diisi user |

## Pustaka dan dokumentasi
| Aset | Sumber |
|---|---|
| Python multiprocessing | https://docs.python.org/3/library/multiprocessing.html |
| Python socket | https://docs.python.org/3/library/socket.html |
| Python lzma, bz2, gzip | https://docs.python.org/3/library/lzma.html, https://docs.python.org/3/library/bz2.html, https://docs.python.org/3/library/gzip.html |
| Python hashlib, tomllib | https://docs.python.org/3/library/hashlib.html, https://docs.python.org/3/library/tomllib.html |
| psutil | https://psutil.readthedocs.io |

## Formula
Speedup, efficiency, hukum Amdahl: cantumkan buku teks atau paper rujukan (mis. buku Parallel Programming atau Introduction to Parallel Computing) lengkap dengan penulis, tahun, dan halaman. Agent hanya mencantumkan rujukan yang benar-benar dapat diverifikasi, bila tidak yakin tulis `PERLU DIISI USER`.

## Lisensi
Catat lisensi atau ketentuan penggunaan tiap dataset. Dataset tidak ikut di repo (`data/` di-ignore), cukup skrip unduh dan checksum.
