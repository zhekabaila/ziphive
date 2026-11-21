"""UT-SYS-01..03: sampler psutil 1 Hz dan system.csv (PLAN.md P7-T1)."""

from __future__ import annotations

from pathlib import Path

from pcomp.metrics.system import (
    SYSTEM_CSV_COLUMNS,
    ProcessSampler,
    Sample,
    SystemLog,
    SystemSampler,
    read_system_csv,
)


def make_sample(ts: float = 1.0, role: str = "worker") -> Sample:
    return Sample(
        ts=ts,
        role=role,
        node="node-1",
        worker_id="w1",
        cpu_percent=12.5,
        mem_percent=3.25,
        rss_mb=48.0,
    )


def test_system_log_writes_header_and_round_trips(tmp_path: Path) -> None:
    """UT-SYS-01: SystemLog menulis header sekali dan baris dapat dibaca ulang."""
    path = tmp_path / "system.csv"
    log = SystemLog(path)
    log.write(make_sample(1.0))
    log.write(make_sample(2.0, role="master"))
    log.close()

    rows = path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == ",".join(SYSTEM_CSV_COLUMNS)
    assert len(rows) == 3

    samples = read_system_csv(path)
    assert [item.ts for item in samples] == [1.0, 2.0]
    assert samples[0].cpu_percent == 12.5
    assert samples[1].role == "master"


def test_sampler_builds_sample_with_injected_sources() -> None:
    """UT-SYS-02: SystemSampler memakai sampler dan clock yang disuntikkan."""
    collected: list[Sample] = []
    clock_values = iter([5.0, 6.0])
    sampler = SystemSampler(
        collected.append,
        role="worker",
        node="node-9",
        worker_id="w7",
        interval=1.0,
        sampler=lambda: (11.0, 2.5, 30.0),
        clock=lambda: next(clock_values),
    )

    sample = sampler.sample_once()
    assert sample.ts == 5.0
    assert sample.node == "node-9"
    assert sample.worker_id == "w7"
    assert sample.cpu_percent == 11.0
    assert sample.mem_percent == 2.5
    assert sample.rss_mb == 30.0
    assert collected == [sample]

    second = sampler.sample_once()
    assert second.ts == 6.0
    assert len(collected) == 2


def test_sampler_thread_samples_and_stops() -> None:
    """UT-SYS-03: thread sampler mengambil beberapa sampel lalu berhenti bersih."""
    collected: list[Sample] = []
    sampler = SystemSampler(
        collected.append,
        role="master",
        interval=0.01,
        sampler=lambda: (1.0, 1.0, 1.0),
    )
    sampler.start()
    try:
        deadline = 5.0
        import time

        started = time.monotonic()
        while len(collected) < 2 and time.monotonic() - started < deadline:
            time.sleep(0.01)
        assert len(collected) >= 2
    finally:
        sampler.stop()
    count = len(collected)
    assert count >= 2


def test_process_sampler_returns_non_negative_values() -> None:
    """UT-SYS-03b: ProcessSampler proses sendiri mengembalikan angka wajar."""
    sampler = ProcessSampler()
    cpu, mem, rss = sampler.snapshot()
    assert cpu >= 0.0
    assert mem >= 0.0
    assert rss > 0.0
