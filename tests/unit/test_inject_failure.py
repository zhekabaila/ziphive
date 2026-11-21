"""UT-TOOL-03: `tools/inject_failure.py` mencatat event dan menghentikan proses Worker."""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

from pcomp.metrics.events import read_events
from pcomp.tools import inject_failure


def test_inject_failure_emits_event_and_terminates(tmp_path: Path) -> None:
    """UT-TOOL-03: event `worker_exit_injected` ditulis sebelum PID dihentikan."""
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    events_path = tmp_path / "events.jsonl"
    try:
        time.sleep(0.1)
        code = inject_failure.main(
            [
                "--events",
                str(events_path),
                "--pid",
                str(process.pid),
                "--worker-id",
                "w1",
            ]
        )

        assert code == 0
        assert process.wait(timeout=15) != 0
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=10)

    rows = read_events(events_path)
    assert rows[-1]["event"] == "worker_exit_injected"
    assert rows[-1]["pid"] == process.pid
    assert rows[-1]["worker_id"] == "w1"
    assert isinstance(rows[-1]["ts"], float)
