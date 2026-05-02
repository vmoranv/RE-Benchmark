"""Q1 Headless Reproducibility — verifies docker-compose stack starts cleanly."""

from __future__ import annotations

import subprocess
from pathlib import Path

COMPOSE_FILE = Path(__file__).resolve().parents[3] / "infra" / "compose" / "docker-compose.yml"


def check_compose_file_exists() -> dict:
    """Static pre-flight: the canonical compose file must be present."""
    return {
        "exists": COMPOSE_FILE.exists(),
        "path": str(COMPOSE_FILE),
    }


def run_smoke_up(timeout_seconds: int = 600) -> dict:
    """Spin up the stack with ``--abort-on-container-exit`` and capture status.

    This is intentionally a thin wrapper. The CI workflow ``qualification.yml``
    invokes it under a job that already has Docker available.
    """
    if not COMPOSE_FILE.exists():
        return {"ok": False, "reason": "compose file missing"}
    try:
        proc = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(COMPOSE_FILE),
                "up",
                "--build",
                "--abort-on-container-exit",
                "--exit-code-from",
                "api",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return {"ok": False, "reason": "docker not on PATH"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "timeout"}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-2000:],
        "stderr_tail": proc.stderr[-2000:],
    }
