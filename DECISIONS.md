# DECISIONS.md — Catatan Keputusan Desain

Format: Konteks, Keputusan, Konsekuensi. Tambah entri baru di bawah, jangan hapus entri lama (beri status `Superseded by ADR-xx`).

## ADR-001 Python dengan socket stdlib
- Konteks: soal tidak mewajibkan framework; tim butuh kode yang mudah dipahami dan dijelaskan di laporan.
- Keputusan: `socket`, `threading`, `multiprocessing`, `hashlib`, `lzma/bz2/gzip` dari stdlib. Dependensi runtime hanya `psutil`.
- Konsekuensi: instalasi di node lab minimal. Tidak memakai MPI atau Ray.

## ADR-002 Task = chunk file
- Konteks: Silesia hanya 12 file, ukuran sangat timpang. Satu file satu task membuat load balancing tidak terlihat.
- Keputusan: file dipecah menjadi chunk tetap (default 4 MiB), tiap chunk dikompresi mandiri.
- Konsekuensi: jumlah task cukup banyak. Rasio kompresi sedikit lebih buruk dibanding kompresi utuh (dicatat di laporan). Rekonstruksi lewat dekompresi tiap chunk berurutan.

## ADR-003 Dispatch berbasis credit (pull)
- Konteks: dynamic load balancing yang sederhana namun nyata.
- Keputusan: Worker meminta credit sebanyak jumlah proses bebasnya, Master mengirim task sesuai credit. Worker cepat atau punya banyak core otomatis menerima lebih banyak task.
- Konsekuensi: tidak perlu estimasi kecepatan Worker. Static scheduler disediakan hanya sebagai pembanding.

## ADR-004 Thread per koneksi, bukan asyncio
- Keputusan: thread handler per Worker di Master. Skala 9 Worker cukup.
- Konsekuensi: kode lebih mudah dibaca. State bersama dilindungi satu lock di `TaskTable`.

## ADR-005 Frame JSON header + payload biner
- Keputusan: lihat PROTOCOL.md. Header JSON mudah di-debug, payload biner efisien.

## ADR-006 Konfigurasi TOML
- Keputusan: `tomllib` (stdlib Python 3.11), tanpa PyYAML.

## ADR-007 Alur git
- Keputusan: branch per fase, commit oleh agent setelah gate lulus, merge `--no-ff`, tag `phase-NN-done`, tanpa push otomatis.
