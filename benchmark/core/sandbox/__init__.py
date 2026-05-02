"""Sandbox subsystem (Docker default + Node subprocess for dev/CI)."""

from benchmark.core.sandbox.docker_runner import DockerSandboxRunner
from benchmark.core.sandbox.node_runner import (
    NodeRunResult,
    NodeSubprocessRunner,
    TestCaseResult,
)

__all__ = [
    "DockerSandboxRunner",
    "NodeRunResult",
    "NodeSubprocessRunner",
    "TestCaseResult",
]
