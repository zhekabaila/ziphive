# FLOW.md — Alur Sistem dan Alur Kerja Agent

## 1. Startup dan pemrosesan normal
```mermaid
sequenceDiagram
    participant M as Master
    participant W as Worker
    W->>M: REGISTER (id, cores, procs, version)
    M-->>W: REGISTER_ACK (algo, level, heartbeat)
    Note over M: tunggu expect-workers lalu mulai timer
    W->>M: REQUEST credits = procs
    loop selama ada task PENDING dan credit tersisa
        M->>W: TASK (header + data chunk)
        W->>W: Pool.apply_async kompresi
        W->>M: RESULT (header + data terkompresi)
        M->>M: validasi, tulis chunk, task DONE
        W->>M: REQUEST credits = 1
    end
    M->>W: SHUTDOWN
    W->>M: BYE
    M->>M: tulis manifest, metrics, verifikasi
```

## 2. Worker gagal
```mermaid
sequenceDiagram
    participant M as Master
    participant A as Worker A
    participant B as Worker B
    M->>A: TASK 17
    A--xM: crash (tidak ada pesan)
    Note over M: monitor: last_seen lewat 6 s
    M->>M: A = DEAD, task 17 kembali PENDING (attempts+1)
    B->>M: REQUEST credits = 1
    M->>B: TASK 17
    B->>M: RESULT 17 ok
    Note over M: catat worker_dead, task_requeued, recovery selesai
```

## 3. Keputusan di Master saat menerima RESULT
```mermaid
flowchart TD
    R[RESULT diterima] --> S{task ASSIGNED ke pengirim?}
    S -- tidak --> I[abaikan, catat event late_or_duplicate]
    S -- ya --> O{ok dan sha256 cocok?}
    O -- ya --> D[tulis chunk, state DONE]
    O -- tidak --> A{attempts < 3?}
    A -- ya --> P[state PENDING, attempts+1]
    A -- tidak --> F[state FAILED, dead-letter]
```

## 4. Alur eksperimen
1. Siapkan dataset dan `config/*.toml`. 2. Jalankan `check_node.py` di semua node. 3. Start Master dengan `--expect-workers n`. 4. Start n Worker. 5. Master menjalankan, menulis `results/raw/<exp>/<run_id>/`. 6. Jalankan `tools/verify.py`. 7. Ulangi 3 kali. 8. `bench/report.py` membuat ringkasan dan grafik.

## 5. Alur kerja AI agent per fase
```mermaid
flowchart TD
    A[Baca AGENTS PLAN SDLC] --> B[Buat branch phase/NN]
    B --> C[Salin template phase log]
    C --> D[Tulis test dulu]
    D --> E[Implementasi]
    E --> F[Jalankan gate.py]
    F --> G{G1-G9 lulus?}
    G -- tidak --> H[Perbaiki akar masalah]
    H --> F
    G -- ya --> I[Update CHANGELOG, phase log, PLAN]
    I --> J[Commit, merge no-ff, tag]
    J --> K[Laporan fase, berhenti]
```
