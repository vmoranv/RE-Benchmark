"""Abstract base classes — the contract layer of the benchmark engine."""

from benchmark.core.abstractions.artifact_store import ArtifactStore
from benchmark.core.abstractions.challenge import BaseChallenge, ChallengeResult
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.evaluator import BaseEvaluator
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.abstractions.model_adapter import ModelAdapter, ModelCapabilities
from benchmark.core.abstractions.quota_policy import QuotaPolicy
from benchmark.core.abstractions.sandbox_adapter import SandboxAdapter, SandboxResult

__all__ = [
    "ArtifactStore",
    "BaseChallenge",
    "BaseDimension",
    "BaseEvaluator",
    "BaseMetric",
    "ChallengeResult",
    "ModelAdapter",
    "ModelCapabilities",
    "QuotaPolicy",
    "SandboxAdapter",
    "SandboxResult",
]
