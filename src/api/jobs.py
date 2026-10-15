# -*- coding: utf-8 -*-
"""Backward-compat shim for job store (v6.0.3).

Legacy module-level API now delegates to a JobStore instance.
Backend selected via JOB_STORE env (memory | postgres; postgres -> v6.1).
"""
import os
from datetime import datetime

from src.api.job_store import Job, JobStatus, JobStore
from src.api.job_store_memory import InMemoryJobStore


_store: JobStore | None = None


def get_store() -> JobStore:
    global _store
    if _store is None:
        backend = os.getenv("JOB_STORE", "memory").lower()
        if backend == "memory":
            _store = InMemoryJobStore()
        elif backend == "postgres":
            raise NotImplementedError("PostgresJobStore lands in v6.1")
        else:
            raise ValueError(f"Unknown JOB_STORE={backend!r}")
    return _store


def _job_to_dict(job: Job) -> dict:
    """Convert Job to legacy dict shape (status as str, ISO datetimes)."""
    return {
        "job_id": job.job_id,
        "status": job.status.value,  # legacy: str, НЕ JobStatus
        "filename": job.filename,
        "created_at": job.created_at.isoformat(),
        "started_at": job.started_at.isoformat() if job.started_at else None,
        "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        "result": job.result,
        "error": job.error,
        "tenant_id": job.tenant_id,  # новое поле, не мешает
    }


# --- Legacy API (сохраняем сигнатуры) ---

def create_job(filename: str = "unknown") -> str:
    return get_store().create(filename=filename).job_id


def get_job(job_id: str) -> dict | None:
    job = get_store().get(job_id)
    return _job_to_dict(job) if job else None


def update_job(job_id: str, **kwargs) -> bool:
    # Legacy: kwargs — dict-поля. Конвертируем status-строку в JobStatus.
    if "status" in kwargs and isinstance(kwargs["status"], str):
        kwargs["status"] = JobStatus(kwargs["status"])
    # v6.0.3-shim-fix: main.py passes started_at/finished_at as ISO strings.
    for dt_field in ("started_at", "finished_at"):
        if dt_field in kwargs and isinstance(kwargs[dt_field], str):
            kwargs[dt_field] = datetime.fromisoformat(kwargs[dt_field])
    return get_store().update(job_id, **kwargs) is not None


def delete_job(job_id: str) -> bool:
    return get_store().delete(job_id)


def list_jobs(limit: int = 50) -> list[dict]:
    return [_job_to_dict(j) for j in get_store().list_jobs(limit=limit)]


def clear_jobs() -> int:
    return get_store().clear()


def job_count() -> int:
    return get_store().count()
