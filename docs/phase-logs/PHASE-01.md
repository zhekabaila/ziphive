# PHASE-01 — Protokol dan infrastruktur inti

- Branch: phase/01-core-protocol
- Mulai / selesai: 2026-11-20 / 2026-11-20
- Status: DONE

## 1. Tujuan
Komunikasi Master–Worker yang andal di level pesan (PLAN.md Fase 1). Lingkup hanya P1-T1 sampai
P1-T4: frame protokol, helper jaringan, pemuatan konfigurasi, logging, dan event log. Tidak ada
Master, Worker, chunker, compressor, atau scheduler pada fase ini.

## 2. Ringkasan hasil
Frame protokol kini diimplementasikan persis seperti PROTOCOL.md bagian 1: 4 byte panjang header
(`!I`), 8 byte panjang payload (`!Q`), header JSON UTF-8, lalu payload biner, dengan batas 64 KiB
dan 64 MiB. `net.py` menyediakan pembacaan tepat N byte, kirim/terima frame, dan connect dengan
retry serta backoff. `config.py` memuat `master.toml` dan `worker.toml` lalu menimpa nilainya dari
argumen CLI, lengkap dengan validasi tipe dan rentang. Logging terpusat dan event log JSONL
thread-safe sudah tersedia. Seluruh test ditulis lebih dulu (merah: 6 error koleksi
`ModuleNotFoundError`), lalu implementasi sampai hijau: 64 unit test dan 2 integration test lulus,
coverage 92,17%.

## 3. Task
| ID | Deskripsi | Status | Catatan |
|---|---|---|---|
| P1-T1 | `protocol.py`: encode/decode frame, tipe pesan, validasi field | DONE | Format tidak diubah dari PROTOCOL.md |
| P1-T2 | `net.py`: `send_msg`, `recv_msg`, connect dengan retry dan backoff | DONE | `recv_exact` membaca tepat N byte |
| P1-T3 | `config.py`: muat TOML, timpa dengan argumen CLI | DONE | Validasi port, level, scheduler, procs, dan lain-lain |
| P1-T4 | `logging_setup.py`, `metrics/events.py` | DONE | JSONL ber-`ts` float epoch, thread-safe |

## 4. File yang berubah
| Path | Aksi (add/mod/del) | Alasan |
|---|---|---|
| `src/pcomp/protocol.py` | add | P1-T1: frame, tipe pesan, kode error, validasi |
| `src/pcomp/net.py` | add | P1-T2: helper socket dan retry connect |
| `src/pcomp/config.py` | add | P1-T3: konfigurasi TOML + override CLI |
| `src/pcomp/logging_setup.py` | add | P1-T4: logging terpusat |
| `src/pcomp/metrics/events.py` | add | P1-T4: event log JSONL |
| `src/pcomp/constants.py` | mod | Batas frame dan default timeout protokol |
| `pyproject.toml` | mod | Versi `0.01.0` |
| `scripts/gate.py` | mod | Smoke Fase 1 dan penanda phase log |
| `TESTING.md` | mod | Baris UT-LOG-01 |
| `CHANGELOG.md` | mod | Entri `0.01.0` |
| `PLAN.md` | mod | Status fase 1 dan `CURRENT PHASE` |
| `docs/phase-logs/PHASE-01.md` | add | Phase log fase ini |
| `tests/unit/test_protocol.py` | add | UT-PRO-01..06 |
| `tests/unit/test_net.py` | add | UT-NET-01..03 |
| `tests/unit/test_config.py` | add | UT-CFG-01..02 |
| `tests/unit/test_events.py` | add | UT-EVT-01 |
| `tests/unit/test_logging.py` | add | UT-LOG-01 |
| `tests/unit/test_package.py` | mod | Test kesesuaian versi pyproject dan constants |
| `tests/integration/test_echo.py` | add | IT-ECHO-01 |

## 5. Test
| Jenis | Ditambah | Total lulus | Catatan |
|---|---|---|---|
| Unit | 42 | 64 | UT-PRO 15 test, UT-NET 7, UT-CFG 12, UT-EVT 4, UT-LOG 3, plus 1 test versi |
| Integration | 1 | 2 | IT-ECHO-01: payload 10 MiB, hash sama |

Coverage: 92,17% (`--cov=src/pcomp --cov-fail-under=80`).

## 6. Hasil Verification Gate
| Gate | Hasil | Bukti singkat |
|---|---|---|
| G1 Lint | PASS | `check=All checks passed!; format=45 files already formatted` |
| G2 Type | PASS | `Success: no issues found in 14 source files` |
| G3 Unit+cov | PASS | `Total coverage: 92.17% | 64 passed, 2 deselected` |
| G4 Integration | PASS | `2 passed, 64 deselected` |
| G5 Regresi | PASS | test fase 0 tetap dijalankan dan lulus |
| G6 Smoke | PASS | `pytest -m integration -k echo -q -> rc=0: 1 passed` |
| G7 Flaky x3 | SKIP | dilewati: berlaku fase 4 ke atas (SDLC.md G7) |
| G8 Dokumen | PASS | CHANGELOG `0.01.0`, PHASE-01 terisi, status PLAN `DONE` |
| G9 Repo | PASS | tidak ada file > 5 MB, `data/` dan `output/` tidak terlacak |

Keluaran lengkap: `reports/gate-latest.txt` (tidak di-commit karena `reports/` di-ignore).

## 7. Deviasi dari rencana
1. Ditambahkan UT-LOG-01 karena PLAN.md Fase 1 tidak menyebut test untuk `logging_setup.py`,
   sementara G3 menuntut coverage 80%. Test ini dicatat juga di TESTING.md bagian 4.
2. Ditambahkan test kesesuaian versi `pyproject.toml` dengan `constants.__version__` agar versi
   fase (`0.NN.0`) tidak menyimpang di dua tempat.
3. Nilai `task_id` dan `version` pada REGISTER divalidasi sebagai int atau string karena
   PROTOCOL.md tidak menetapkan tipenya. Keputusan ini dicatat di bagian 10.
4. `error` pada RESULT boleh `null` (kompresi berhasil) atau string, karena PROTOCOL.md tidak
   menyatakan apakah field selalu berisi string.
5. Kode error pada pesan ERROR divalidasi terhadap daftar PROTOCOL.md bagian 2; kode baru di luar
   daftar ditolak sampai `PROTOCOL_VERSION` dinaikkan.

## 8. Masalah ditemukan dan solusi
| Masalah | Akar masalah | Solusi |
|---|---|---|
| 6 error koleksi saat test merah | Modul `protocol`, `net`, `config`, `logging_setup`, `events` belum ada | Implementasi modul sesuai kontrak PROTOCOL.md |
| `SIM105` pada `close_quietly` | `try/except/pass` tidak disarankan ruff | Diganti `contextlib.suppress(OSError)` |
| G8 gagal pada run pertama | Phase log dan CHANGELOG belum diisi | Dokumentasi fase dilengkapi lalu gate penuh diulang |

## 9. Back-fix (bug fase lama)
Tidak ada.

## 10. Keterbatasan dan utang teknis
1. Tipe `task_id` (int atau string) dan field `version` pada REGISTER belum ditetapkan PROTOCOL.md;
   implementasi menerima keduanya. Perlu penegasan di dokumen sebelum Fase 4.
2. `error` pada RESULT menerima `null`; belum ada aturan eksplisit di PROTOCOL.md.
3. `recv_msg` tidak memasang timeout sendiri; pemanggil wajib memanggil `sock.settimeout()`
   (didokumentasikan lewat konstanta `DEFAULT_SOCKET_TIMEOUT`).
4. Belum ada validasi bahwa header TASK membawa payload sepanjang `orig_size`; pemeriksaan ukuran
   dan hash baru masuk Fase 4 (P4-T5).
5. `config.py` mengabaikan key TOML yang tidak dikenal agar kompatibel; salah ketik nama key akan
   terlewat tanpa peringatan.
6. G7 (cek flaky 3 kali) belum berlaku sampai Fase 4.

## 11. Catatan serah-terima ke fase berikutnya
1. Gunakan `pcomp.net.send_msg` / `recv_msg` dan `pcomp.protocol.build_frame`; jangan menyusun
   frame manual di modul lain.
2. Setiap socket baru wajib `settimeout(constants.DEFAULT_SOCKET_TIMEOUT)` sebelum `recv_msg`.
3. `EventLog` membuka file mode append dan menulis `ts` float epoch; dipakai untuk menghitung
   detection latency dan Recovery Time di Fase 6-7.
4. `config.load_master_config(overrides=...)` mengabaikan nilai `None`, sehingga argparse dapat
   langsung meneruskan namespace CLI.
5. Fase 2 perlu menambah `SMOKE_COMMANDS[2]` di `scripts/gate.py` agar G6 tidak gagal.

## 12. Commit
Hash: diisi pada commit akhir fase (lihat `git log`). Tag: phase-01-done
