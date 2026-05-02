"""SandboxAdapter — isolation boundary for executing untrusted JS."""

from __future__ import annotations

from abc import abstractmethod

from pydantic import BaseModel, Field


class SandboxResult(BaseModel):
    """Result of a sandbox execution."""

    exit_code: int
    duration_ms: int
    stdout_artifact_id: str | None = None
    stderr_artifact_id: str | None = None
    artifacts_produced: list[str] = Field(default_factory=list)
    timed_out: bool = False
    oom: bool = False
    metadata: dict = Field(default_factory=dict)


class SandboxConfig(BaseModel):
    """Configuration for a sandbox execution."""

    timeout_seconds: int = 60
    memory_mb: int = 512
    seed: int | None = None
    env: dict | None = None


class SandboxAdapter:
    """Runs untrusted code in an isolated environment.

    Default implementation (``DockerRunner``) launches an ephemeral Docker
    container with a pinned image, ``--network none``, read-only root,
    seccomp, capability drops, and resource limits. Tests may stub this
    with an in-process executor.
    """

    @abstractmethod
    async def run(
        self,
        profile: str,
        artifact_id: str,
        config: SandboxConfig | None = None,
    ) -> SandboxResult:
        """Execute the artifact under ``profile``.

        ``profile`` is a logical name like ``"jsvmp_node"`` or
        ``"browser_anti_debug"``; the adapter resolves it to a concrete
        runner image + arguments.
        """
