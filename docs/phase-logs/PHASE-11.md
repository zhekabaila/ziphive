# PHASE-11 — Kesiapan 10 perangkat fisik

- Branch: `phase/11-physical-nodes`
- Mulai / selesai: 2026-11-22 / 2026-11-22
- Status: DONE

## 1. Tujuan
Menyiapkan agar eksperimen resmi E1 sampai E6 dapat dijalankan pada 1 Master dan 9 Worker berupa
laptop fisik di satu jaringan (hotspot atau router), tanpa ssh dan tanpa Docker, pada macOS,
Windows, dan Linux. Pelaksanaan 10 node virtual (ADR-015) digantikan perangkat fisik (ADR-016),
sehingga harness perlu jalur Worker eksternal, launcher sekali-klik, dan injeksi kegagalan E5 dari
sisi Master.

## 2. Ringkasan hasil
Protokol naik ke versi 2 dengan pesan `KILL` (Master ke Worker) dan kode error `SERVER_FULL`.
Master menolak Worker di luar `--expect-workers` dan dapat mengirim `KILL` sendiri setelah fraksi
task tertentu selesai, sehingga lama deteksi dan lama pemulihan E5 terukur pada jam Master tanpa
sinyal OS maupun ssh. Harness `--lan` kini memvalidasi jumlah dan `procs` Worker yang benar-benar
terdaftar, mencetak instruksi operator per run, dan mendukung `--lan-wait`. Tiga launcher
(`setup-node`, `start-worker`, `start-master`) berjalan di macOS, Linux, dan Windows dengan venv di
dalam folder proyek, ditambah `scripts/node_common.py` sebagai helper lintas platform yang diuji
unit. `DEPLOYMENT-PHYSICAL.md` memuat runbook lengkap 10 perangkat. Seluruh unit test (266) dan
integration test (24) lulus, lint dan mypy bersih, dan gate penuh PASS.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P11-T1 | Protokol versi 2: `KILL`, `SERVER_FULL` | DONE | `constants.PROTOCOL_VERSION = 2`, `protocol.py`, `PROTOCOL.md`, `ARCHITECTURE.md` |
| P11-T2 | Master: tolak Worker berlebih dan injeksi `KILL` | DONE | `MasterState.expect_workers`/`_killed_ids`, `MasterServer._maybe_inject_kills`, `--inject-kills`, `--inject-kill-fraction` |
| P11-T3 | Worker menangani `KILL` | DONE | `os._exit(EXIT_KILLED)`, `EXIT_KILLED = 3` |
| P11-T4 | Harness `--lan` dengan validasi Worker | DONE | `wait_lan_workers`, `lan_instructions`, `--lan-wait` |
| P11-T5 | `scripts/node_common.py` | DONE | 8 unit test UT-NODE-01..08 |
| P11-T6 | `scripts/bootstrap_node.py` + wrapper | DONE | `SETUP OK`; 3 wrapper OS |
| P11-T7 | `scripts/start_worker.py` + wrapper | DONE | Ingatan `config/worker.local.toml`, loop reconnect, log `logs/worker-<id>.log` |
| P11-T8 | `scripts/start_master.py` + wrapper | DONE | Dataset otomatis 2048 MiB/8 berkas/seed 20261122, `PLAN OK` |
| P11-T9 | `run_experiments.py --worker-mode external` | DONE | Port tetap, `--lan-wait`, instruksi per run |
| P11-T10 | `DEPLOYMENT-PHYSICAL.md` | DONE | 10 bagian: alur, persiapan, jaringan, perintah, bandwidth, checklist, bukti, troubleshooting, rebuild laporan |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/constants.py` | mod | `PROTOCOL_VERSION = 2`, `__version__ = "1.1.0"`, `EXIT_KILLED` |
| `src/pcomp/protocol.py` | mod | `MessageType.KILL`, `ErrorCode.SERVER_FULL`, field wajib `KILL` |
| `src/pcomp/master/server.py` | mod | `should_inject_kills`, kuota `expect_workers`, `_killed_ids`/`mark_killed`, `_maybe_inject_kills` |
| `src/pcomp/master/cli.py` | mod | `--inject-kills`, `--inject-kill-fraction` |
| `src/pcomp/worker/client.py` | mod | Cabang `KILL` dan pesan `WORKER DITOLAK <code>` |
| `src/pcomp/bench/runner.py` | mod | `LAN_EXPECTED_PROCS`, `lan_instructions`, `registered_workers`, `wait_lan_workers`, `--lan-wait` |
| `scripts/node_common.py` | add | Helper lintas platform (venv, versi, IP, perintah, konfigurasi lokal) |
| `scripts/bootstrap_node.py` | add | Venv + `pip install -e .` + `check_node.py`, `--check-only` |
| `scripts/start_worker.py` | add | Launcher Worker dengan ingatan pengaturan dan loop reconnect |
| `scripts/start_master.py` | add | Launcher Master dengan dataset otomatis dan rencana Worker |
| `setup-node.{command,sh,bat}`, `start-worker.{command,sh,bat}`, `start-master.{command,sh,bat}` | add | Wrapper sekali-klik tiga sistem operasi |
| `scripts/run_experiments.py` | mod | `--worker-mode {docker,external}`, `--port`, `--lan-wait`, `lan_args` |
| `scripts/gate.py` | mod | `FINAL_PHASE = 11`, `FINAL_VERSION = "1.1.0"`, smoke fase 11 |
| `pyproject.toml` | mod | Versi `1.1.0` |
| `.gitignore` | mod | `config/worker.local.toml`, `logs/` |
| `PROTOCOL.md` | mod | Judul v2, baris `KILL`, kode `SERVER_FULL`, aturan 10–12 |
| `ARCHITECTURE.md` | mod | Komponen, tabel fault tolerance, catatan node fisik, dua batasan baru |
| `DEPLOYMENT-PHYSICAL.md` | add | Runbook 10 perangkat fisik |
| `tests/unit/test_node_common.py` | add | UT-NODE-01..08 |
| `tests/unit/test_launchers.py` | add | UT-LAUN-01..07 |
| `tests/unit/test_master_kill.py` | add | UT-KILL-01..06 |
| `tests/unit/test_bench.py` | mod | UT-BEN-08..09 |
| `tests/unit/test_run_experiments.py` | mod | UT-EXP-08 |
| `tests/unit/test_protocol.py` | mod | UT-PRO-07 dan penyesuaian v2 |
| `tests/unit/test_package.py` | mod | `PROTOCOL_VERSION` 2 |
| `tests/unit/test_master_cli.py` | mod | Fake server menerima argumen injeksi |
| `tests/integration/test_kill_injection.py` | add | IT-KILL-01..02 |
| `tests/integration/test_server_full.py` | add | IT-FULL-01 |
| `tests/integration/test_lan_external.py` | add | IT-LAN-01 |
| `CHANGELOG.md` | mod | Entri `1.1.0` |
| `DECISIONS.md` | mod | ADR-016 dan ADR-017 |
| `PLAN.md` | mod | Status fase 11 `DONE` |
| `README.md` | mod | Bagian launcher dan perintah fisik |
| `DEPLOYMENT.md` | mod | Pointer ke `DEPLOYMENT-PHYSICAL.md` |
| `docs/CODE_GUIDE.md` | mod | Skrip baru dan perintah launcher |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 22 | 266 | UT-NODE-01..08, UT-LAUN-01..07, UT-KILL-01..06, UT-BEN-08..09, UT-EXP-08, UT-PRO-07 |
| Integration | 4 | 23 (G4) / 24 (per direktori) | IT-KILL-01..02, IT-FULL-01, IT-LAN-01; satu test `slow` (9 Worker) berjalan terpisah |

Coverage: 84,4%

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `ruff check` All checks passed; `ruff format --check` 138 files already formatted |
| G2 Type | PASS | `mypy` Success: no issues found in 40 source files |
| G3 Unit+cov | PASS | 266 passed, coverage 84,4% (batas 80%) |
| G4 Integration | PASS | 23 passed (test `slow` 9 Worker berjalan terpisah) |
| G5 Regresi | PASS | seluruh test fase 0–10 ikut dijalankan G3 dan G4 |
| G6 Smoke | PASS | `bootstrap_node.py --check-only` → `SETUP OK`; `start_master.py --print-plan` → `PLAN OK` |
| G7 Flaky x3 | PASS | integration test 3 kali lulus |
| G8 Dokumen | PASS | CHANGELOG `1.1.0`, `PHASE-11.md`, status PLAN `DONE` sinkron |
| G9 Repo | PASS | tidak ada `data/`, `output/`, `.venv`, atau berkas runtime di commit |

## 7. Deviasi dari rencana
1. Injeksi `KILL` disertai daftar `_killed_ids` pada `MasterState`. Tanpa ini, launcher Worker yang
   otomatis menyambung ulang akan mendaftar kembali segera setelah di-`KILL`, sehingga jumlah
   Worker pada run E5 kembali penuh dan skenario kehilangan makna. Worker yang sudah di-`KILL`
   ditolak `SERVER_FULL` sampai run berakhir.
2. `start_worker.py` tetap mengulang Worker setelah `EXIT_KILLED` (bukan berhenti), karena penolakan
   di atas membuat pengulangan aman dan operator tidak perlu menyalakan launcher lagi. Rencana awal
   menyebut launcher berhenti pada kode itu.
3. `node_common.bootstrap_commands` tidak memuat langkah `pip install --upgrade pip`. Langkah itu
   tidak diperlukan karena `pip` bawaan venv Python 3.11+ sudah memadai, dan menghindari kegagalan
   pada mesin tanpa internet penuh.
4. Dataset otomatis `start_master.py` memakai 2048 MiB, 8 berkas, seed `20261122` sesuai
   `ASSETS.md`, bukan nilai default lama 8 MiB.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| Unit test injeksi `KILL` gagal `TimeoutError` | `MasterServer` dibuat tanpa `inject_kills`, sehingga `_kills_left` nol | Helper test meneruskan `inject_kills`/`inject_kill_fraction` |
| Task tidak dapat ditandai `DONE` di test | `mark_done` hanya berlaku untuk task `ASSIGNED` | Test memakai `table.take_next` lebih dulu |
| Integration `SERVER_FULL` gagal | Worker mencetak "balasan tak terduga ERROR", kode tidak terbaca | `client.py` mencetak `WORKER DITOLAK <code>: <message>` untuk ERROR pertama |
| Worker kedua mendaftar sebelum Worker pertama | Test membaca events terlalu cepat | Test menunggu event `worker_registered` sebelum menjalankan Worker kedua |
| `test_run_experiments` gagal `'120.0' != '120'` | `argparse` menyimpan `float` | Assertion memakai `"120.0"` |
| `ruff` E501 dan SIM102 pada skrip baru | Baris panjang dan `if` bersarang | Baris dipecah dan `if` digabung |

## 9. Back-fix (bug fase lama)
Tidak ada bug fase lama yang ditemukan; perubahan pada `tests/unit/test_master_cli.py`,
`tests/unit/test_package.py`, dan `tests/unit/test_protocol.py` hanya penyesuaian terhadap protokol
versi 2 dan tanda tangan `MasterServer` yang baru.

## 10. Keterbatasan dan utang teknis
1. Pengujian pada laptop fisik belum dilakukan; verifikasi saat ini hanya localhost (Worker sebagai
   proses terpisah) dan seluruh smoke launcher. Uji 1–2 laptop teman direncanakan 2026-11-23.
2. `throttle` Worker tidak dapat diperiksa dari Master, sehingga kesalahan pengaturan E4 pada laptop
   w9 hanya terdeteksi dari keluaran launcher. Sudah didokumentasikan di `DEPLOYMENT-PHYSICAL.md`
   bagian 5.1.
3. `run_experiments.py --worker-mode external` memakai port tetap 5050; bila port itu dipakai
   aplikasi lain di laptop Master, operator harus mengubah `--port` dan menyesuaikan launcher Worker.
4. Bandwidth: satu run 2048 MiB mengirim sekitar 2 GiB ke Worker; rangkaian 45 run sekitar 90 GiB.
   Hotspot 4G kemungkinan tidak memadai (didokumentasikan pada bagian 6 runbook).
5. Angka laporan BAB IV masih berasal dari 10 node virtual (ADR-015) sampai data fisik tersedia.
6. Wrapper `.bat` belum diuji pada Windows asli; hanya ditinjau dan diuji secara statis melalui
   unit test perintah yang dibangun `node_common`.

## 11. Catatan serah-terima ke fase berikutnya
1. Sebelum eksperimen fisik: jalankan `setup-node` di semua laptop, pastikan `check_node.py
   --ping-master <IP> --port 5050` OK, dan hapus/backup `results/raw` di laptop Master.
2. Urutan eksperimen yang disarankan: E1, E2 (tanpa Worker) lalu E6, E3, E4, E5, agar laptop teman
   cukup dinyalakan sekali.
3. E4 wajib mengatur `--throttle 0.25` pada w9 dan mengembalikannya ke `0` sesudahnya.
4. Setelah data fisik masuk: jalankan `validate_results`, bangun ulang `summary.csv`/grafik, lalu
   perbarui seluruh angka BAB IV dan ganti ADR-015 dengan ADR-016 pada laporan.
5. Jangan memakai `dist/ziphive-source-0.07.0.zip` yang lama; paket yang valid adalah
   `dist/ziphive-source-1.0.0.zip` dan paket 1.1.0 yang dibangun ulang setelah fase ini.

## 12. Commit
`5b5e26e` `feat(phase-11): support physical 10-node runs with launchers and kill injection`,
lalu commit catatan ini. Tag `phase-11-done` pada `main`. Versi paket `1.1.0`.
