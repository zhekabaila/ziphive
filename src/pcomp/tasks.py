"""Model task dan state machine (ARCHITECTURE.md bagian 4)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TaskState(StrEnum):
    """Status satu task pada Master."""

    PENDING = "PENDING"
    ASSIGNED = "ASSIGNED"
    DONE = "DONE"
    FAILED = "FAILED"


@dataclass
class Task:
    """Satu chunk file yang harus dikompresi."""

    task_id: int
    file: str
    index: int
    offset: int
    length: int
    state: TaskState = TaskState.PENDING
    attempts: int = 0
    assigned_to: str | None = None
    assigned_at: float | None = None
    sha256: str | None = None
    comp_size: int | None = None
    done_at: float | None = None
