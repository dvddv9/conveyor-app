# -*- coding: utf-8 -*-
"""Celery application (v6.1 queue).

Broker/backend come from env (CELERY_BROKER_URL / CELERY_RESULT_BACKEND).
The factory `_get_celery_app()` is exposed so tests can build an app from a
patched environment without reloading the module.
"""
import os
import socket
from urllib.parse import urlparse

from celery import Celery


def _get_celery_app() -> Celery:
    """Build a Celery app from the current environment."""
    return Celery(
        "vishap",
        broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
        backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
    )


celery_app = _get_celery_app()

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    # Fail fast when the broker is unreachable (the API falls back to an
    # in-process BackgroundTask in that case; retrying would hang the request).
    task_publish_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=1,
)


def broker_available(timeout: float = 0.5) -> bool:
    """Quick TCP check for the broker (avoids Celery's slow connection retry).

    Used by the API before `.delay()` so a down broker degrades to the
    in-process fallback instead of hanging the HTTP request.
    """
    try:
        u = urlparse(celery_app.conf.broker_url)
        host = u.hostname or "localhost"
        port = u.port or 6379
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, ValueError):
        return False
