# -*- coding: utf-8 -*-
"""In-memory JobStore implementation (v6.0.3)."""
import uuid
from dataclasses import replace
from datetime import datetime, UTC
from threading import RLock

from src.api.job_store import Job, JobStatus
from src.observability.logging import get_logger

log = get_logger(__name__)


class InMemoryJobStore:
    """Thread-safe in-memory job store."""

    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = RLock()

    def create(self, filename: str = "unknown", *,
               tenant_id: str | None = None) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        job = Job(
            job_id=job_id,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
            filename=filename,
            tenant_id=tenant_id,
        )
        with self._lock:
            self._jobs[job_id] = job
        log.info("job_created", job_id=job_id, filename=filename, backend="memory")
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def update(self, job_id: str, **kwargs) -> Job | None:
        with self._lock:
            old = self._jobs.get(job_id)
            if old is None:
                return None
            new = replace(old, updated_at=datetime.now(UTC), **kwargs)
            self._jobs[job_id] = new
            _status = new.status.value if isinstance(new.status, JobStatus) else new.status
            log.info("job_updated", job_id=job_id, status=_status, backend="memory")
            return new

    def delete(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                log.info("job_deleted", job_id=job_id, backend="memory")
                return True
            return False

    def list_jobs(self, limit: int = 50) -> list[Job]:
        with self._lock:
            items = list(self._jobs.values())
        return items[-limit:]

    def clear(self) -> int:
        with self._lock:
            n = len(self._jobs)
            self._jobs.clear()
        return n

    def count(self) -> int:
        with self._lock:
            return len(self._jobs)
