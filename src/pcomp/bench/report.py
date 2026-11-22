"""Laporan benchmark: agregasi rata-rata/simpangan baku dan grafik PNG (PLAN.md P7-T4)."""

from __future__ import annotations

import csv
import json
import statistics
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402 - backend harus diset sebelum pyplot

from pcomp.metrics.calc import recovery_stats  # noqa: E402
from pcomp.metrics.events import read_events  # noqa: E402

GROUP_KEYS = ("exp", "workers", "procs", "scheduler", "kill_workers")
METRIC_COLUMNS = (
    "time_s",
    "throughput_mbs",
    "speedup_seq",
    "speedup_rel",
    "efficiency",
    "imbalance",
    "cpu_avg_master",
    "cpu_avg_workers",
    "mem_avg_master",
    "mem_avg_workers",
    "detect_s",
    "recovery_s",
    "retried_tasks",
)


def _num(value: Any) -> float | None:
    """Ubah nilai CSV atau JSON menjadi float; None bila kosong atau bukan angka."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _axis_value(row: Mapping[str, Any]) -> int:
    """Nilai sumbu X: jumlah Worker, atau jumlah proses untuk mode local."""
    workers = _num(row.get("workers"))
    if workers is not None and workers > 0:
        return int(workers)
    procs = _num(row.get("procs"))
    return int(procs) if procs else 1


def aggregate(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str] = GROUP_KEYS
) -> list[dict[str, Any]]:
    """Rata-rata dan simpangan baku tiap metrik per kelompok konfigurasi."""
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(row.get(key) for key in keys), []).append(row)

    summary: list[dict[str, Any]] = []
    ordered = sorted(groups.items(), key=lambda pair: tuple(str(value) for value in pair[0]))
    for key, items in ordered:
        entry: dict[str, Any] = dict(zip(keys, key, strict=True))
        entry["reps"] = len(items)
        for column in METRIC_COLUMNS:
            values = [
                number
                for number in (_num(item.get(column)) for item in items)
                if number is not None
            ]
            entry[f"{column}_mean"] = statistics.fmean(values) if values else None
            if len(values) > 1:
                entry[f"{column}_std"] = statistics.stdev(values)
            else:
                entry[f"{column}_std"] = 0.0 if values else None
        summary.append(entry)
    return summary


def write_aggregate_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> Path:
    """Tulis tabel agregat ke CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(rows[0]) if rows else ["exp"]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: ("" if row.get(column) is None else row.get(column)) for column in columns}
            )
    return path


def _series(
    rows: Sequence[Mapping[str, Any]], column: str
) -> dict[tuple[str, str], list[tuple[int, float]]]:
    """Kelompokkan nilai metrik per (exp, scheduler) lalu per sumbu X (rata-rata rep)."""
    buckets: dict[tuple[str, str], dict[int, list[float]]] = {}
    for row in rows:
        value = _num(row.get(column))
        if value is None:
            continue
        key = (str(row.get("exp") or ""), str(row.get("scheduler") or "-"))
        buckets.setdefault(key, {}).setdefault(_axis_value(row), []).append(value)

    series: dict[tuple[str, str], list[tuple[int, float]]] = {}
    for key, points in buckets.items():
        series[key] = sorted((x, statistics.fmean(values)) for x, values in points.items())
    return series


def _line_chart(
    rows: Sequence[Mapping[str, Any]],
    specs: Sequence[tuple[str, str]],
    path: Path,
    *,
    xlabel: str,
    ylabel: str,
    title: str,
) -> Path | None:
    """Grafik garis satu atau beberapa metrik terhadap sumbu X."""
    written = False
    fig, ax = plt.subplots(figsize=(6.4, 4.2))
    for column, label in specs:
        for (exp, scheduler), points in sorted(_series(rows, column).items()):
            if scheduler in ("", "-", "none"):
                name = f"{label} {exp}"
            else:
                name = f"{label} {exp}/{scheduler}"
            ax.plot(
                [point[0] for point in points],
                [point[1] for point in points],
                marker="o",
                markersize=4,
                label=name,
            )
            written = True
    if not written:
        plt.close(fig)
        return None
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_time_vs_workers(rows: Sequence[Mapping[str, Any]], path: Path) -> Path | None:
    """Waktu eksekusi terhadap jumlah Worker/proses."""
    return _line_chart(
        rows,
        [("time_s", "waktu")],
        path,
        xlabel="jumlah worker/proses",
        ylabel="waktu (detik)",
        title="Waktu eksekusi",
    )


def plot_speedup(rows: Sequence[Mapping[str, Any]], path: Path) -> Path | None:
    """Speedup terhadap sequential dan terhadap 1 Worker."""
    return _line_chart(
        rows,
        [("speedup_seq", "S_seq"), ("speedup_rel", "S_rel")],
        path,
        xlabel="jumlah worker/proses",
        ylabel="speedup (x)",
        title="Speedup",
    )


def plot_efficiency(rows: Sequence[Mapping[str, Any]], path: Path) -> Path | None:
    """Efficiency S(n)/n."""
    return _line_chart(
        rows,
        [("efficiency", "E")],
        path,
        xlabel="jumlah worker/proses",
        ylabel="efficiency",
        title="Efficiency",
    )


def plot_throughput(rows: Sequence[Mapping[str, Any]], path: Path) -> Path | None:
    """Throughput MB/s."""
    return _line_chart(
        rows,
        [("throughput_mbs", "throughput")],
        path,
        xlabel="jumlah worker/proses",
        ylabel="MB/s",
        title="Throughput",
    )


def plot_cpu_mem(rows: Sequence[Mapping[str, Any]], path: Path) -> Path | None:
    """Rata-rata pemakaian CPU dan memori Master serta Worker."""
    return _line_chart(
        rows,
        [
            ("cpu_avg_master", "CPU master"),
            ("cpu_avg_workers", "CPU worker"),
            ("mem_avg_master", "mem master"),
            ("mem_avg_workers", "mem worker"),
        ],
        path,
        xlabel="jumlah worker/proses",
        ylabel="persen",
        title="CPU dan memori",
    )


def _read_worker_stats(run_dir: Path) -> list[tuple[str, float]]:
    path = run_dir / "metrics.json"
    if not path.is_file():
        return []
    metrics = json.loads(path.read_text(encoding="utf-8"))
    stats = metrics.get("worker_stats") or []
    return [(str(item["worker_id"]), float(item["busy_sec"])) for item in stats]


def plot_worker_load(run_dirs: Sequence[Path], path: Path) -> Path | None:
    """Waktu sibuk tiap Worker untuk beberapa run terdistribusi yang berbeda konfigurasi."""
    datasets: list[tuple[str, list[tuple[str, float]]]] = []
    seen: set[tuple[str, str]] = set()
    for run_dir in run_dirs:
        stats = _read_worker_stats(run_dir)
        if not stats:
            continue
        parts = run_dir.name.split("-")
        key = (parts[0], parts[3] if len(parts) > 3 else "")
        if key in seen:
            continue
        seen.add(key)
        datasets.append((run_dir.name, stats))
        if len(datasets) >= 4:
            break
    if not datasets:
        return None

    workers = sorted({worker for _, stats in datasets for worker, _ in stats})
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    width = 0.8 / max(len(datasets), 1)
    for index, (label, stats) in enumerate(datasets):
        mapping = dict(stats)
        positions = [
            workers.index(worker) + index * width for worker in workers if worker in mapping
        ]
        values = [mapping[worker] for worker in workers if worker in mapping]
        ax.bar(positions, values, width=width, label=label[:24])
    ax.set_xticks(range(len(workers)), workers)
    ax.set_xlabel("worker")
    ax.set_ylabel("waktu sibuk (detik)")
    ax.set_title("Beban per Worker")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def plot_recovery_timeline(run_dirs: Sequence[Path], path: Path) -> Path | None:
    """Timeline task selesai dengan penanda kill, deteksi, dan pemulihan."""
    figure: Any = None
    plotted = False
    for run_dir in run_dirs:
        events_path = run_dir / "events.jsonl"
        if not events_path.is_file():
            continue
        events = read_events(events_path)
        stats = recovery_stats(events)
        if stats.kill_ts is None:
            continue
        kill = stats.kill_ts
        done = sorted(float(row["ts"]) - kill for row in events if row.get("event") == "task_done")
        if not done:
            continue
        if figure is None:
            figure, axes = plt.subplots(figsize=(7.0, 4.2))
        x_values = [0.0, *done]
        y_values = list(range(len(x_values)))
        axes.step(x_values, y_values, where="post", label=run_dir.name[:24])
        axes.axvline(0.0, color="red", linestyle="--", linewidth=1, label="kill")
        if stats.detect_s is not None:
            axes.axvline(stats.detect_s, color="orange", linestyle=":", linewidth=1)
            axes.annotate(
                f"deteksi +{stats.detect_s:.2f} s",
                (stats.detect_s, 0.0),
                textcoords="offset points",
                xytext=(2, 6),
                fontsize=7,
            )
        if stats.recovery_s is not None:
            axes.axvline(stats.recovery_s, color="green", linestyle="-.", linewidth=1)
            axes.annotate(
                f"pulih +{stats.recovery_s:.2f} s",
                (stats.recovery_s, 0.0),
                textcoords="offset points",
                xytext=(2, -12),
                fontsize=7,
            )
        plotted = True

    if figure is None or not plotted:
        if figure is not None:
            plt.close(figure)
        return None
    figure.suptitle("Timeline pemulihan")
    axes.set_xlabel("detik sejak kill")
    axes.set_ylabel("jumlah task selesai")
    axes.grid(True, alpha=0.3)
    axes.legend(fontsize=7)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    plt.close(figure)
    return path


def plot_all(
    rows: Sequence[Mapping[str, Any]],
    *,
    run_dirs: Sequence[Path] = (),
    out_dir: Path,
) -> list[Path]:
    """Buat seluruh grafik yang datanya tersedia; kembalikan path yang tertulis."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plans: list[tuple[str, Callable[[Path], Path | None]]] = [
        ("time_vs_workers.png", lambda path: plot_time_vs_workers(rows, path)),
        ("speedup.png", lambda path: plot_speedup(rows, path)),
        ("efficiency.png", lambda path: plot_efficiency(rows, path)),
        ("throughput.png", lambda path: plot_throughput(rows, path)),
        ("cpu_mem.png", lambda path: plot_cpu_mem(rows, path)),
        ("worker_load.png", lambda path: plot_worker_load(run_dirs, path)),
        ("recovery_timeline.png", lambda path: plot_recovery_timeline(run_dirs, path)),
    ]
    written: list[Path] = []
    for name, builder in plans:
        path = builder(out_dir / name)
        if path is not None:
            written.append(path)
    return written
