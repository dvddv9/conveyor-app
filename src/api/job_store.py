# -*- coding: utf-8 -*-
"""JobStore contract for async analysis (v6.0.3).

Defines the Job dataclass, JobStatus enum, and the JobStore Protocol.
Concrete implementations (e.g. InMemoryJobStore) live in separate modules.
"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Protocol


class JobStatus(str, Enum):
    """Job lifecycle statuses. Values match legacy dict statuses."""
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@dataclass(frozen=True)
class Job:
    """Immutable job record."""
    job_id: str
    status: JobStatus
    created_at: datetime
    updated_at: datetime
    filename: str
    tenant_id: str | None = None
    result: dict | None = None
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class JobStore(Protocol):
    """Storage contract for async analysis jobs."""

    def create(self, filename: str = "unknown", *,
               tenant_id: str | None = None) -> Job: ...

    def get(self, job_id: str) -> Job | None: ...

    def update(self, job_id: str, **kwargs) -> Job | None: ...

    def delete(self, job_id: str) -> bool: ...

    def list_jobs(self, limit: int = 50) -> list[Job]: ...

    def clear(self) -> int: ...

    def count(self) -> int: ...
