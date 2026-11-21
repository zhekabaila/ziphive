"""UT-CAL-01..04: rumus metrik sesuai EXPERIMENTS.md bagian 3 (PLAN.md P7-T2)."""

from __future__ import annotations

import pytest

from pcomp.metrics.calc import (
    detection_latency,
    efficiency,
    imbalance_factor,
    recovery_stats,
    recovery_time,
    speedup,
    throughput_mbs,
)


def test_speedup_and_efficiency_hand_values() -> None:
    """UT-CAL-01: speedup dan efficiency dengan nilai hitung tangan."""
    assert speedup(10.0, 5.0) == pytest.approx(2.0)
    assert speedup(10.0, 4.0) == pytest.approx(2.5)
    assert efficiency(2.0, 4) == pytest.approx(0.5)
    assert efficiency(3.0, 2) == pytest.approx(1.5)


def test_speedup_and_efficiency_guard_zero() -> None:
    """UT-CAL-01b: pembagi nol atau negatif menghasilkan 0.0, bukan error."""
    assert speedup(10.0, 0.0) == 0.0
    assert speedup(10.0, -1.0) == 0.0
    assert efficiency(2.0, 0) == 0.0


def test_throughput_and_imbalance_hand_values() -> None:
    """UT-CAL-02: throughput MB/s dan imbalance factor max/mean."""
    assert throughput_mbs(8 * 1024 * 1024, 2.0) == pytest.approx(4.0)
    assert throughput_mbs(1024 * 1024, 0.0) == 0.0
    assert imbalance_factor([1.0, 1.0, 1.0]) == pytest.approx(1.0)
    assert imbalance_factor([2.0, 1.0, 0.0]) == pytest.approx(2.0)
    assert imbalance_factor([]) == pytest.approx(1.0)
    assert imbalance_factor([0.0, 0.0]) == pytest.approx(1.0)


def synthetic_events() -> list[dict]:
    """Events sintetis satu siklus kegagalan Worker w1 (EXPERIMENTS.md bagian 3)."""
    return [
        {"ts": 90.0, "event": "run_started", "tasks": 4},
        {"ts": 99.0, "event": "task_done", "task_id": 0, "worker_id": "w2"},
        {"ts": 100.0, "event": "worker_exit_injected", "worker_id": "w1", "pid": 123},
        {"ts": 100.4, "event": "worker_dead", "worker_id": "w1", "reason": "koneksi putus"},
        {"ts": 100.5, "event": "task_requeued", "task_id": 1, "worker_id": "w1"},
        {"ts": 101.0, "event": "task_requeued", "task_id": 2, "worker_id": "w1"},
        {"ts": 102.5, "event": "task_done", "task_id": 1, "worker_id": "w2"},
        {"ts": 104.0, "event": "task_done", "task_id": 2, "worker_id": "w2"},
        {"ts": 104.2, "event": "task_done", "task_id": 3, "worker_id": "w2"},
    ]


def test_detection_latency_and_recovery_time() -> None:
    """UT-CAL-03: detection latency dan Recovery Time dihitung dari events."""
    events = synthetic_events()
    assert detection_latency(events, 100.0) == pytest.approx(0.4)
    assert recovery_time(events, 100.0) == pytest.approx(4.0)

    stats = recovery_stats(events)
    assert stats.worker_id == "w1"
    assert stats.kill_ts == pytest.approx(100.0)
    assert stats.detect_s == pytest.approx(0.4)
    assert stats.recovery_s == pytest.approx(4.0)
    assert stats.retried_tasks == 2


def test_recovery_without_injection_or_unfinished_task() -> None:
    """UT-CAL-04: tanpa event injeksi detection/Recovery None; task belum selesai None."""
    no_kill = [
        {"ts": 1.0, "event": "worker_dead", "worker_id": "w1"},
        {"ts": 2.0, "event": "task_requeued", "task_id": 7, "worker_id": "w1"},
    ]
    stats = recovery_stats(no_kill)
    assert stats.worker_id == "w1"
    assert stats.kill_ts is None
    assert stats.detect_s is None
    assert stats.recovery_s is None
    assert stats.retried_tasks == 1

    unfinished = synthetic_events()[:-3]
    assert recovery_time(unfinished, 100.0) is None
    assert detection_latency(no_kill, 1.0) is None
    assert recovery_stats([]).retried_tasks == 0
    assert recovery_stats([]).worker_id is None
