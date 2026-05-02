"""Docker-backed sandbox runner.

Loads ``profile.yaml`` files describing how to launch an ephemeral
container, mounts the requested artifact read-only at ``/work/input``,
and captures stdout / stderr.

The implementation is intentionally minimal — a full production runner
would shell out to ``docker run`` with an audited argv. For unit tests
we ship a mock alternative under ``tests/_helpers``.
"""

from __future__ import annotations

import asyncio
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID

import yaml

from benchmark.core.abstractions.artifact_store import ArtifactStore
from benchmark.core.abstractions.sandbox_adapter import (
    SandboxAdapter,
    SandboxConfig,
    SandboxResult,
)


@dataclass(slots=True)
class SandboxProfile:
    image: str
    runtime_args: list[str]
    entrypoint: list[str] | None
    timeout_seconds: int


class DockerSandboxRunner(SandboxAdapter):
    """Launches Docker containers to execute untrusted JS."""

    def __init__(
        self,
        *,
        artifact_store: ArtifactStore,
        profiles_dir: str | Path,
        docker_binary: str = "docker",
    ) -> None:
        self._artifact_store = artifact_store
        self._profiles_dir = Path(profiles_dir)
        self._docker = docker_binary

    def _load_profile(self, profile: str) -> SandboxProfile:
        path = self._profiles_dir / f"{profile}.yaml"
        if not path.exists():
            msg = f"sandbox profile not found: {profile}"
            raise FileNotFoundError(msg)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return SandboxProfile(
            image=data["image"],
            runtime_args=data.get("runtime_args", []),
            entrypoint=data.get("entrypoint"),
            timeout_seconds=int(data.get("timeout_seconds", 60)),
        )

    async def run(
        self,
        profile: str,
        artifact_id: str,
        config: SandboxConfig | None = None,
    ) -> SandboxResult:
        cfg = config or SandboxConfig()
        prof = self._load_profile(profile)
        artifact_bytes = await self._artifact_store.get(UUID(artifact_id))

        # Stage input on a temp file mounted into the container.
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile(suffix=".js", delete=False) as tf:
            tf.write(artifact_bytes)
            input_host_path = tf.name

        try:
            argv: list[str] = [self._docker, "run"]
            argv.extend(prof.runtime_args)
            argv.extend(["--memory", f"{cfg.memory_mb}m"])
            argv.extend(["-v", f"{input_host_path}:/work/input.js:ro"])
            if cfg.env:
                for k, v in cfg.env.items():
                    argv.extend(["-e", f"{k}={v}"])
            if cfg.seed is not None:
                argv.extend(["-e", f"BENCH_SEED={cfg.seed}"])
            argv.append(prof.image)
            if prof.entrypoint:
                argv.extend(prof.entrypoint)

            t0 = time.monotonic()
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            timed_out = False
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=min(cfg.timeout_seconds, prof.timeout_seconds),
                )
            except TimeoutError:
                proc.kill()
                stdout, stderr = await proc.communicate()
                timed_out = True
            duration_ms = int((time.monotonic() - t0) * 1000)

            stdout_id = await self._artifact_store.put(stdout, mime_type="text/plain", kind="log")
            stderr_id = await self._artifact_store.put(stderr, mime_type="text/plain", kind="log")

            return SandboxResult(
                exit_code=-1 if timed_out else (proc.returncode or 0),
                duration_ms=duration_ms,
                stdout_artifact_id=str(stdout_id),
                stderr_artifact_id=str(stderr_id),
                artifacts_produced=[str(stdout_id), str(stderr_id)],
                timed_out=timed_out,
                metadata={"argv_redacted": shlex.join(argv)},
            )
        finally:
            Path(input_host_path).unlink(missing_ok=True)
