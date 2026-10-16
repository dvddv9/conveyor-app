# -*- coding: utf-8 -*-
"""PostgreSQL JobStore implementation (v6.1) via SQLAlchemy 2.0 async."""
import uuid
from datetime import datetime, UTC

from sqlalchemy import DateTime, String, Text, delete, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.api.job_store import Job, JobStatus


class Base(DeclarativeBase):
    """Declarative base for SQLAlchemy models."""


class JobModel(Base):
    """SQLAlchemy model mapping to the ``jobs`` table."""

    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class PostgresJobStore:
    """Async PostgreSQL-backed JobStore (SQLAlchemy 2.0 async).

    Note: methods are async (unlike the sync InMemoryJobStore); the sync shim
    in src/api/jobs.py keeps a sync facade for the legacy module-level API.
    """

    def __init__(self, database_url: str) -> None:
        self._engine = create_async_engine(database_url)
        self._session_factory = async_sessionmaker(self._engine, expire_on_commit=False)

    @staticmethod
    def _to_job(model: "JobModel") -> Job:
        return Job(
            job_id=model.job_id,
            status=JobStatus(model.status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            filename=model.filename,
            tenant_id=model.tenant_id,
            result=model.result,
            error=model.error,
            started_at=model.started_at,
            finished_at=model.finished_at,
        )

    async def create(self, filename: str = "unknown", *,
                     tenant_id: str | None = None) -> Job:
        job_id = f"job-{uuid.uuid4().hex[:12]}"
        now = datetime.now(UTC)
        model = JobModel(
            job_id=job_id,
            status=JobStatus.QUEUED.value,
            filename=filename,
            created_at=now,
            updated_at=now,
            tenant_id=tenant_id,
            result=None,
            error=None,
            started_at=None,
            finished_at=None,
        )
        async with self._session_factory() as session:
            session.add(model)
            await session.commit()
        return self._to_job(model)

    async def get(self, job_id: str) -> Job | None:
        async with self._session_factory() as session:
            model = await session.get(JobModel, job_id)
        return self._to_job(model) if model else None

    async def update(self, job_id: str, **kwargs) -> Job | None:
        # Defensive: accept JobStatus enums and ISO-string datetimes.
        if "status" in kwargs and isinstance(kwargs["status"], JobStatus):
            kwargs["status"] = kwargs["status"].value
        for dt_field in ("started_at", "finished_at"):
            if dt_field in kwargs and isinstance(kwargs[dt_field], str):
                kwargs[dt_field] = datetime.fromisoformat(kwargs[dt_field])
        async with self._session_factory() as session:
            model = await session.get(JobModel, job_id)
            if model is None:
                return None
            for field, value in kwargs.items():
                setattr(model, field, value)
            model.updated_at = datetime.now(UTC)
            await session.commit()
        return self._to_job(model)

    async def delete(self, job_id: str) -> bool:
        async with self._session_factory() as session:
            model = await session.get(JobModel, job_id)
            if model is None:
                return False
            await session.delete(model)
            await session.commit()
        return True

    async def list_jobs(self, limit: int = 50) -> list[Job]:
        async with self._session_factory() as session:
            result = await session.execute(
                select(JobModel).order_by(JobModel.created_at.desc()).limit(limit)
            )
            models = result.scalars().all()
        return [self._to_job(m) for m in models]

    async def clear(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(delete(JobModel))
            await session.commit()
        return result.rowcount or 0

    async def count(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(select(func.count()).select_from(JobModel))
            value = result.scalar()
        return value or 0
