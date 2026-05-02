"""Run pipeline Celery tasks (skeletons matching the state machine)."""

from __future__ import annotations

from apps.worker.celeryconfig import celery_app


@celery_app.task(name="apps.worker.tasks.run_pipeline.precheck_run", bind=True)
def precheck_run(self, run_id: str) -> dict:
    """PLANNED -> PRECHECK transition.

    Validates sample existence, model availability, quota reservation, and
    sandbox image digest pinning before the LLM rounds begin.
    """
    return {"run_id": run_id, "ok": True}


@celery_app.task(name="apps.worker.tasks.run_pipeline.run_round", bind=True)
def run_round(self, ctx: dict, round_no: int) -> dict:
    return {"run_id": ctx.get("run_id"), "round_no": round_no, "ok": True}


@celery_app.task(name="apps.worker.tasks.run_pipeline.verify_round", bind=True)
def verify_round(self, ctx: dict, round_no: int) -> dict:
    return {"run_id": ctx.get("run_id"), "round_no": round_no, "ok": True}


@celery_app.task(name="apps.worker.tasks.run_pipeline.judge_run", bind=True)
def judge_run(self, ctx: dict) -> dict:
    return {"run_id": ctx.get("run_id"), "ok": True}


@celery_app.task(name="apps.worker.tasks.run_pipeline.compute_metrics", bind=True)
def compute_metrics(self, ctx: dict) -> dict:
    return {"run_id": ctx.get("run_id"), "ok": True}


@celery_app.task(name="apps.worker.tasks.run_pipeline.finalize_run", bind=True)
def finalize_run(self, ctx: dict) -> dict:
    return {"run_id": ctx.get("run_id"), "ok": True, "state": "FINALIZED"}
