# -*- coding: utf-8 -*-
"""In-memory job store for async analysis (v6.0).

Statuses:
  queued  -- job created, not started
  running -- pipeline in progress
  done    -- completed, result available
  failed  -- error occurred, see error field
"""
import uuid
from datetime import datetime, UTC
from threading import Lock
from typing import Any


_jobs: dict[str, dict] = {}
_lock = Lock()


def create_job(filename: str = "unknown") -> str:
    """Create a new job, return job_id."""
    job_id = f"job-{uuid.uuid4().hex[:12]}"
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "filename": filename,
            "created_at": datetime.now(UTC).isoformat(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }
    return job_id


def get_job(job_id: str) -> dict | None:
    """Get job by id, or None."""
    with _lock:
        job = _jobs.get(job_id)
        return dict(job) if job else None


def update_job(job_id: str, **kwargs) -> bool:
    """Update job fields. Returns True if job existed."""
    with _lock:
        if job_id not in _jobs:
            return False
        _jobs[job_id].update(kwargs)
        return True


def delete_job(job_id: str) -> bool:
    """Delete job. Returns True if existed."""
    with _lock:
        if job_id in _jobs:
            del _jobs[job_id]
            return True
        return False


def list_jobs(limit: int = 50) -> list[dict]:
    """List jobs (newest last), up to limit."""
    with _lock:
        items = list(_jobs.values())
    return items[-limit:]


def clear_jobs() -> int:
    """Clear all jobs, return count removed."""
    with _lock:
        n = len(_jobs)
        _jobs.clear()
    return n


def job_count() -> int:
    """Current number of jobs."""
    with _lock:
        return len(_jobs)
