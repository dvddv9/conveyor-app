# -*- coding: utf-8 -*-
"""Prometheus metrics (v6.1 Block 3).

Uses a single dedicated CollectorRegistry (not the default REGISTRY) so that
re-importing the module (importlib.reload) never raises "Duplicated timeseries",
and tests do not leak into the global registry.
"""
from prometheus_client import Counter, Histogram, CollectorRegistry, generate_latest

_REGISTRY = CollectorRegistry()

JOBS_CREATED = Counter(
    "vishap_jobs_created_total",
    "Total number of jobs created.",
    ["status"],
    registry=_REGISTRY,
)
JOBS_COMPLETED = Counter(
    "vishap_jobs_completed_total",
    "Total number of jobs that finished (done or failed).",
    ["status"],
    registry=_REGISTRY,
)
JOB_DURATION = Histogram(
    "vishap_job_duration_seconds",
    "Duration of jobs in seconds.",
    buckets=[1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
    registry=_REGISTRY,
)
HTTP_REQUESTS = Counter(
    "vishap_http_requests_total",
    "Total number of HTTP requests.",
    ["method", "endpoint", "status"],
    registry=_REGISTRY,
)


def observe_job_created(status: str) -> None:
    """Increment the jobs-created counter."""
    JOBS_CREATED.labels(status=status).inc()


def observe_job_finished(status: str, duration_seconds: float) -> None:
    """Increment the finished counter + observe duration for a finished job."""
    JOBS_COMPLETED.labels(status=status).inc()
    JOB_DURATION.observe(duration_seconds)


def observe_http_request(method: str, endpoint: str, status: int) -> None:
    """Increment the HTTP request counter."""
    HTTP_REQUESTS.labels(method=method, endpoint=endpoint, status=str(status)).inc()


def get_metrics_output() -> str:
    """Return metrics in Prometheus text format."""
    return generate_latest(_REGISTRY).decode("utf-8")


def get_sample_value(name: str, labels: dict) -> float:
    """Return a sample value (0.0 if missing) — helper for tests."""
    return _REGISTRY.get_sample_value(name, labels) or 0.0
