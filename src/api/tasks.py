# -*- coding: utf-8 -*-
"""Celery tasks (v6.1 queue).

`run_analysis_task` replaces the in-process BackgroundTasks path: the API
enqueues the job, a separate Celery worker executes the pipeline and updates
the JobStore (memory or postgres).
"""
from src.api.celery_app import celery_app
from src.api.jobs import get_store
from src.observability.tracing import span
from src.pipeline.orchestrator import run_pipeline


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_analysis_task(self, job_id: str, material: str, filename: str):
    """Run the analysis pipeline for a queued job (Celery worker task)."""
    store = get_store()
    with span("celery.run_analysis", job_id=job_id, filename=filename):
        try:
            store.update(job_id, status="running")
            result = run_pipeline(material, filename)
            store.update(job_id, status="done", result=result)
            return job_id
        except Exception as e:
            store.update(job_id, status="failed", error=str(e))
            raise self.retry(exc=e)
