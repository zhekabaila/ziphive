"""Rumus metrik (PLAN.md P7-T2) sesuai EXPERIMENTS.md bagian 3."""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from pcomp import constants

Event = Mapping[str, Any]


def speedup(t_base: float, t_n: float) -> float:
    """S(n) = T_base / T_n; 0.0 bila pembagi tidak positif."""
    if t_n <= 0:
        return 0.0
    return t_base / t_n


def efficiency(speedup_value: float, n: int) -> float:
    """E(n) = S(n) / n; 0.0 bila n tidak positif."""
    if n <= 0:
        return 0.0
    return speedup_value / n


def throughput_mbs(total_bytes: int, time_s: float) -> float:
    """Throughput MB/s = ukuran asli (MiB) / waktu detik."""
    if time_s <= 0:
        return 0.0
    return (total_bytes / constants.MIB) / time_s


def imbalance_factor(busy: Sequence[float]) -> float:
    """max(busy_i) / mean(busy_i); 1.0 berarti seimbang."""
    values = list(busy)
    if not values:
        return 1.0
    mean = sum(values) / len(values)
    if mean <= 0:
        return 1.0
    return max(values) / mean


def _timestamp(event: Event) -> float:
    return float(event["ts"])


def _event_ts(events: Sequence[Event], name: str) -> float | None:
    for event in events:
        if event.get("event") == name:
            return _timestamp(event)
    return None


def detection_latency(events: Sequence[Event], kill_ts: float) -> float | None:
    """t_dead_detected - t_kill; None bila tidak ada `worker_dead` sesudah kill."""
    for event in events:
        if event.get("event") != "worker_dead":
            continue
        ts = _timestamp(event)
        if ts > kill_ts:
            return ts - kill_ts
    return None


def recovery_time(
    events: Sequence[Event], kill_ts: float, workers: Collection[str] | None = None
) -> float | None:
    """t_task_terakhir_requeue_selesai - t_kill; None bila belum selesai."""
    scope = set(workers) if workers else None
    requeued = {
        int(event["task_id"])
        for event in events
        if event.get("event") == "task_requeued"
        and _timestamp(event) >= kill_ts
        and (scope is None or str(event.get("worker_id")) in scope)
    }
    if not requeued:
        return None
    done = [
        _timestamp(event)
        for event in events
        if event.get("event") == "task_done" and int(event["task_id"]) in requeued
    ]
    if not done:
        return None
    return max(done) - kill_ts


@dataclass(frozen=True)
class RecoveryStats:
    """Ringkasan satu siklus kegagalan Worker."""

    worker_id: str | None
    kill_ts: float | None
    detect_s: float | None
    recovery_s: float | None
    retried_tasks: int


def _pick_worker(events: Sequence[Event], worker_id: str | None) -> str | None:
    if worker_id is not None:
        return worker_id
    for name in ("worker_exit_injected", "worker_dead"):
        for event in events:
            if event.get("event") == name and event.get("worker_id") is not None:
                return str(event["worker_id"])
    return None


def killed_workers(events: Sequence[Event]) -> list[str]:
    """Daftar Worker yang dihentikan lewat injeksi, sesuai urutan kemunculan."""
    names: list[str] = []
    for event in events:
        if event.get("event") != "worker_exit_injected":
            continue
        name = event.get("worker_id")
        if name is not None and str(name) not in names:
            names.append(str(name))
    return names


def recovery_stats(events: Sequence[Event], worker_id: str | None = None) -> RecoveryStats:
    """Hitung detection latency, Recovery Time, dan jumlah task diulang dari events.

    Bila satu run menghentikan beberapa Worker (E5 skenario tiga Worker), seluruh
    Worker yang diinjeksi ikut dihitung agar jumlah task yang diulang benar.
    """
    killed = killed_workers(events)
    scope: set[str] | None
    if worker_id is not None:
        scope = {worker_id}
        worker: str | None = worker_id
    elif killed:
        scope = set(killed)
        worker = killed[0]
    else:
        scope = None
        worker = _pick_worker(events, None)

    kills = [
        _timestamp(event)
        for event in events
        if event.get("event") == "worker_exit_injected"
        and (scope is None or str(event.get("worker_id")) in scope)
    ]
    kill_ts: float | None = min(kills) if kills else None

    retried = {
        int(event["task_id"])
        for event in events
        if event.get("event") == "task_requeued"
        and (scope is None or str(event.get("worker_id")) in scope)
    }

    detect_s: float | None = None
    recovery_s: float | None = None
    if kill_ts is not None:
        detect_s = detection_latency(events, kill_ts)
        recovery_s = recovery_time(events, kill_ts, scope)

    return RecoveryStats(
        worker_id=worker,
        kill_ts=kill_ts,
        detect_s=detect_s,
        recovery_s=recovery_s,
        retried_tasks=len(retried),
    )


def kill_timestamp(events: Sequence[Event], worker_id: str | None = None) -> float | None:
    """Timestamp injeksi terakhir; None bila tidak ada `worker_exit_injected`."""
    for event in events:
        if event.get("event") != "worker_exit_injected":
            continue
        if worker_id is not None and event.get("worker_id") != worker_id:
            continue
        return _timestamp(event)
    return None


def first_event_ts(events: Sequence[Event], name: str) -> float | None:
    """Timestamp event pertama dengan nama tertentu."""
    return _event_ts(events, name)
