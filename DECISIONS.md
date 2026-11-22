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

## ADR-008 Scheduler static dan dynamic di lapisan Master
- Konteks: Fase 5 membutuhkan pembanding sebelum dan sesudah mekanisme dynamic load balancing, tanpa mengubah protokol.
- Keputusan: `Scheduler` menjadi antarmuka di `master/scheduler.py`. `DynamicScheduler` memilih task terbesar (LPT) setiap kali ada credit, sehingga kapasitas Worker tercermin dari credit. `StaticScheduler` mempartisi task round-robin menurut urutan `task_id` saat barrier terpenuhi dan tidak memindahkan task setelahnya; Worker yang mendaftar setelah barrier tidak mendapat jatah.
- Konsekuensi: protokol dan Worker tidak berubah. Perbandingan static vs dynamic memakai dataset dan algoritma yang sama. Static tetap memakai credit, sehingga Worker yang lebih cepat menganggur saat jatahnya habis. Metrik pembeda `imbalance` dihitung dari `compute_sec` yang dilaporkan Worker.

## ADR-009 Throttle Worker untuk simulasi beban tidak seimbang
- Konteks: perbandingan static vs dynamic perlu Worker lambat yang deterministik tanpa injeksi kegagalan (Fase 6).
- Keputusan: `--throttle` menambah jeda tidur di dalam proses pool sebelum kompresi dan menghitungnya sebagai `compute_sec`.
- Konsekuensi: Worker lambat menghabiskan slot proses lebih lama dan menerima lebih sedikit task pada dynamic. Nilai `throttle` harus 0 pada eksperimen resmi agar tidak mencemari hasil.

## ADR-010 Semantik `attempts` dinaikkan saat penugasan
- Konteks: ARCHITECTURE.md bagian 4 menulis requeue menaikkan `attempts`, sedangkan implementasi `TaskTable` sejak Fase 4 menaikkannya saat task dikirim ke Worker. Bila requeue juga menaikkan, satu task dapat dikirim lebih dari 3 kali dan batas percobaan menjadi kabur.
- Keputusan: `attempts` dinaikkan tepat sekali saat task berubah PENDING ke ASSIGNED. Requeue tidak menaikkan lagi; task menjadi FAILED ketika `attempts >= max_attempts` pada saat requeue. Diagram ARCHITECTURE.md bagian 4 diperbaiki agar sesuai.
- Konsekuensi: jumlah kiriman task ke jaringan dibatasi `max_attempts` (default 3). `metrics.json` menghitung `tasks_retried` sebagai `sum(max(0, attempts - 1))`, yaitu jumlah pengiriman ulang.

## ADR-011 Dead-letter aditif pada manifest dan event `worker_rejoined`
- Konteks: Fase 6 membutuhkan bukti task yang gagal permanen dan bukti Worker yang bergabung ulang, tanpa merusak pembaca manifest versi lama.
- Keputusan: manifest tetap `MANIFEST_VERSION = 1` dengan larik `failed` opsional (default kosong); `manifest.json` dari run normal tidak berubah bentuk isinya. `MasterState.register` mencatat `worker_id` yang pernah terdaftar dan mengirim `worker_rejoined` alih-alih `worker_registered` pada pendaftaran berikutnya dengan id sama.
- Konsekuensi: `tools/verify.py` dan `read_manifest` tidak berubah. Pembaca lama yang tidak mengenal `failed` tetap dapat membaca manifest. Kegagalan task kini terlihat pada manifest, `metrics.json` (`failed_tasks`), dan exit code Master bukan nol.

## ADR-012 Matplotlib sebagai dependensi analisis (extra `analysis`)
- Konteks: PLAN.md P7-T4 mewajibkan grafik PNG dan PLAN.md bagian "Default dan asumsi" menyebut matplotlib sebagai pustaka analisis. Worker hanya diizinkan memakai psutil (PLAN.md P0-T2), sedangkan `bench/report.py` dijalankan pada mesin pengembang atau node Master saat eksperimen.
- Keputusan: matplotlib dicatat sebagai dependensi opsional `analysis` pada `pyproject.toml` dan baris tersendiri pada `requirements-dev.txt`, bukan pada `dependencies` inti maupun `requirements-worker.txt`. Seluruh modul grafik memakai backend `Agg` agar berjalan tanpa layar.
- Konsekuensi: Master, Worker, dan seluruh unit test inti tetap hanya membutuhkan psutil. Menjalankan `python -m pcomp.bench.runner` tanpa matplotlib terpasang akan gagal saat mengimpor `pcomp.bench.report`, sehingga instalasi memakai `pip install -e .[analysis]`. Backend `Agg` diset sebelum `pyplot` diimpor agar hasil deterministik pada mesin tanpa display.

## ADR-013 `check_node.py` hanya menguji keterjangkauan port Master
- Konteks: PLAN.md P8-T1 meminta pemeriksaan "koneksi ke Master, versi protokol". Protokol (PROTOCOL.md) tidak memiliki pesan khusus untuk bertanya versi sebelum REGISTER: satu-satunya pesan pertama dari Worker adalah `REGISTER`, yang langsung mengubah state Master dan mengalokasikan sesi Worker.
- Keputusan: `scripts/check_node.py` membuka koneksi TCP ke `host:port` Master lalu menutupnya, dan melaporkan `PROTOCOL_VERSION` serta versi paket yang dipakai node itu. Skrip tidak mengirim pesan protokol apa pun, sehingga tidak ada perubahan pada PROTOCOL.md atau state Master.
- Konsekuensi: kesamaan versi antar node diverifikasi dengan membandingkan baris `paket` dan `protokol` pada keluaran `check_node.py` di semua node, sedangkan penolakan versi yang tidak cocok tetap dilakukan Master saat REGISTER (`VERSION_MISMATCH`, risiko R2).

## ADR-014 P8-T5 `--data-mode local` ditunda sampai ada bukti R1
- Konteks: PLAN.md Fase 8 menandai P8-T5 "Opsional bila R1 terjadi", sedangkan R1 (bandwidth keluar Master menjadi bottleneck) hanya dapat dinilai dari dry-run pada 10 node fisik. Bagian agent Fase 8 belum memiliki data tersebut, dan implementasinya menuntut perubahan format `TASK` pada PROTOCOL.md.
- Keputusan: P8-T5 tidak diimplementasikan pada bagian agent. Opsi dievaluasi pada bagian user (Prompt 9B) setelah log dry-run tersedia; bila R1 terbukti, opsi ditambahkan sebagai fitur opt-in dengan ADR baru dan kenaikan `PROTOCOL_VERSION`.
- Konsekuensi: tidak ada perubahan protokol atau perilaku default pada Fase 8 bagian agent. DEPLOYMENT.md bagian 5 dan ARCHITECTURE.md bagian 11 mencatat bahwa opsi belum tersedia agar tidak dipakai pada eksperimen resmi.

## ADR-015 10 node virtual pada satu laptop
- Konteks: soal meminta minimal 10 node fisik (PLAN.md pemetaan kebutuhan), tetapi user hanya memiliki satu laptop (Apple M1, 8 core, 8 GB RAM, disk bebas sekitar 9,8 GB) dan deadline mepet. Sembilan VM penuh tidak layak dari sisi RAM dan disk, sedangkan container Linux dapat memberi 10 identitas jaringan terpisah di satu host.
- Keputusan: pelaksanaan Fase 8 dan 9 memakai 10 node virtual, yaitu 1 Master berjalan di host dan 9 Worker berjalan sebagai container Linux (Colima/Docker) pada laptop yang sama, masing-masing dengan hostname dan IP sendiri serta `procs = 1`. Keputusan diambil user pada 2026-11-22. Persetujuan dosen atas penggantian node fisik: TIDAK DIKETAHUI dan wajib dikonfirmasi sebelum pengumpulan.
- Konsekuensi: dokumen yang menyebut "10 node fisik" disesuaikan (AGENTS, PLAN, PROMPTS, SUBMISSION, DEPLOYMENT, ARCHITECTURE). Laporan dan video wajib menyatakan bahwa 10 node bersifat virtual pada satu host, bukan 10 perangkat fisik. Angka performa tidak mewakili LAN lab dan tidak boleh diklaim sebagai pengukuran jaringan fisik. Bila container tidak layak karena disk atau RAM, fallback ke 9 proses lokal dengan pengungkapan yang sama.
