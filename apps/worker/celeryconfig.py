"""Celery configuration and app instance."""

from __future__ import annotations

import os

from celery import Celery

broker_url = os.environ.get("JSREBENCH_REDIS_URL", "redis://localhost:6379/0")
result_backend = os.environ.get("JSREBENCH_REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "js_re_bench",
    broker=broker_url,
    backend=result_backend,
    include=["apps.worker.tasks.run_pipeline"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "apps.worker.tasks.run_pipeline.precheck_run": {"queue": "control"},
        "apps.worker.tasks.run_pipeline.run_round": {"queue": "llm"},
        "apps.worker.tasks.run_pipeline.verify_round": {"queue": "metric"},
        "apps.worker.tasks.run_pipeline.judge_run": {"queue": "judge"},
        "apps.worker.tasks.run_pipeline.compute_metrics": {"queue": "metric"},
        "apps.worker.tasks.run_pipeline.finalize_run": {"queue": "control"},
    },
)
