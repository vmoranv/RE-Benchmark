"""Q3 Blind Test Adaptation — load a private bundle and run subset of dimensions."""

from __future__ import annotations

import os
from pathlib import Path


def find_blind_bundle() -> Path | None:
    """Locate the blind bundle archive provided by CI secrets.

    The expected envvar is ``JS_RE_BENCH_BLIND_BUNDLE`` pointing at a
    decrypted ``.tar.gz``. Absent in dev environments.
    """
    env_path = os.environ.get("JS_RE_BENCH_BLIND_BUNDLE")
    if not env_path:
        return None
    p = Path(env_path)
    return p if p.exists() else None
