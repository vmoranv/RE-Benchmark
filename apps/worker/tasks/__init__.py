"""Celery tasks."""

from apps.worker.tasks import run_pipeline

__all__ = ["run_pipeline"]
