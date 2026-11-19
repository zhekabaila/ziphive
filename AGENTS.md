# AGENTS.md — Instruksi Wajib untuk AI Agent

Proyek : Distributed Data Compression (Tema 16), UAS Komputasi Paralel dan Sistem Terdistribusi, Informatika Unsil
Arsitektur : Master–Worker, TCP socket, Python 3.11+, multiprocessing di setiap Worker
Target : 1 Master + 9 Worker (10 node fisik). Seluruh pengembangan dan test berjalan di localhost.
Bahasa dokumen : Indonesia. Bahasa kode, nama variabel, commit message : Inggris.

## 1. Urutan baca (setiap sesi baru, wajib)
1. `AGENTS.md` (file ini)
2. `PLAN.md` — cari baris `CURRENT PHASE`
3. `SDLC.md` — alur kerja, gate, aturan commit, aturan pencatatan
4. `ARCHITECTURE.md`, `FLOW.md`, `PROTOCOL.md` — sesuai kebutuhan fase
5. `CHANGELOG.md` bagian `[Unreleased]` dan phase log terakhir di `docs/phase-logs/`
6. Jalankan `git status`, `git log --oneline -10`, `python scripts/gate.py --quick`. Jangan menebak keadaan repo.

## 2. Aturan keras
1. Kerjakan HANYA fase di `CURRENT PHASE`. Jangan menyentuh fase berikutnya sebelum gate lulus dan fase di-commit.
2. DILARANG commit sebelum Verification Gate (SDLC.md bagian 4) lulus 100%.
3. DILARANG: menghapus atau melemahkan test, `skip`/`xfail` untuk menutupi kegagalan, mengubah assert agar lolos, `git commit --no-verify`, `git push --force`, `git reset --hard` pada commit yang sudah ada, `git commit --amend` pada commit fase yang sudah selesai.
4. DILARANG `git push` kecuali user meminta eksplisit. Commit hanya lokal.
5. Setiap perubahan WAJIB dicatat di tiga tempat: commit message, `CHANGELOG.md`, phase log (SDLC.md bagian 6).
6. Test-first: tulis test dulu (merah), implementasi (hijau), rapikan. Setiap fitur wajib punya unit test, dan integration test bila menyentuh jaringan atau banyak proses.
7. Hanya stdlib + dependensi di `pyproject.toml`. Menambah dependensi harus dicatat di `DECISIONS.md`.
8. Lintas platform (macOS, Linux, Windows): semua kode multiprocessing harus spawn-safe (fungsi top-level, guard `if __name__ == "__main__"`, tanpa `fork` implisit, tanpa lambda yang dikirim ke Pool). Gunakan `pathlib`. Tanpa sinyal khusus POSIX untuk fungsi inti.
9. Tanpa IP, port, atau path hardcoded. Semua lewat argumen CLI atau file TOML di `config/`.
10. Semua socket punya timeout. Semua thread dapat dihentikan bersih. Tidak ada `while True` tanpa kondisi berhenti.
11. DILARANG mengarang angka. Angka performa di laporan hanya dari `results/raw/` hasil eksperimen nyata. Data hasil simulasi (algoritma `sim`) wajib ditandai dan tidak boleh masuk laporan.
12. Fase bertanda HUMAN-REQUIRED: berhenti di titik yang ditandai, serahkan checklist ke user, tunggu hasil.
13. Ada ambiguitas: pakai default di `PLAN.md` atau `DECISIONS.md`. Jika tidak ada, catat asumsi di phase log dan lanjut. Bertanya ke user hanya jika benar-benar menghalangi.

## 3. Identitas pada output
Setiap program CLI mencetak banner dari `config/group.toml` (nama kelompok, nama dan NPM anggota, tema). Nilai placeholder diisi user, jangan diisi oleh agent.

## 4. Gaya kode
- Sederhana dan mudah dipahami mahasiswa. Fungsi kecil, nama jelas, type hints, docstring satu sampai tiga baris.
- `ruff` line length 100. Logging pakai modul `logging`, bukan `print` (kecuali banner dan hasil akhir CLI).
- Konstanta di `src/pcomp/constants.py`. Tidak ada state global yang dapat diubah di luar class yang jelas.
- Komentar menjelaskan alasan, bukan mengulang kode.
- Teks laporan dan dokumentasi untuk dosen: bahasa Indonesia formal gaya mahasiswa, tanpa simbol khas AI. Gambar memakai placeholder beserta instruksi pengambilan gambar (gunakan skill `laporan-akademik-id`).

## 5. Struktur repo
```
AGENTS.md PLAN.md ARCHITECTURE.md FLOW.md PROTOCOL.md SDLC.md TESTING.md
EXPERIMENTS.md DEPLOYMENT.md ASSETS.md SUBMISSION.md DECISIONS.md CHANGELOG.md README.md
pyproject.toml requirements*.txt Makefile .gitignore
config/    group.toml master.toml worker.toml nodes.toml
src/pcomp/ constants.py config.py logging_setup.py banner.py protocol.py net.py
           tasks.py chunker.py compressor.py manifest.py sequential.py local_parallel.py
           master/ (server.py scheduler.py monitor.py collector.py cli.py __main__.py)
           worker/ (client.py executor.py heartbeat.py cli.py __main__.py)
           metrics/ (events.py system.py calc.py)
           bench/ (runner.py report.py)
           tools/ (make_dataset.py download_corpus.py verify.py inject_failure.py validate_results.py)
tests/     unit/ integration/ conftest.py
scripts/   gate.py e2e_local.py check_node.py launch_workers.py pack_source.py
docs/      phase-logs/ CODE_GUIDE.md ANALYSIS.md
data/ output/ reports/   (gitignored)
results/   raw/ summary.csv figures/
```

## 6. Perintah standar
| Perintah | Fungsi |
|---|---|
| `python scripts/gate.py` | Verification Gate penuh (wajib sebelum commit) |
| `python scripts/gate.py --quick` | lint + unit test saja (cek cepat) |
| `pytest -m "not integration and not perf and not slow"` | unit test |
| `pytest -m integration` | integration test |
| `python scripts/e2e_local.py --workers 3` | end-to-end di localhost |

## 7. Kapan berhenti dan lapor ke user
- Gate gagal 3 kali berturut-turut pada masalah yang sama.
- Perlu mengubah `ARCHITECTURE.md` atau `PROTOCOL.md` secara besar (catat usulan, minta persetujuan).
- Perlu perangkat fisik, akses jaringan lab, atau data yang tidak ada.
- Test flaky (gagal 1 dari 5 kali). Cari akar masalah, jangan diulang sampai lolos.

## 8. Format laporan akhir tiap fase (maks 15 baris)
Fase, status, ringkasan perubahan, hasil gate (angka), commit hash dan tag, deviasi, masalah terbuka, langkah berikutnya.
