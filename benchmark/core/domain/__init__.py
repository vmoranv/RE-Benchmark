"""Pydantic domain models. Single source of truth for in-memory data shape."""

from benchmark.core.domain.artifact import Artifact, ArtifactKind, ArtifactRef
from benchmark.core.domain.evidence import EvidenceEdge, EvidenceRelation
from benchmark.core.domain.metric import MetricGrade, MetricResult
from benchmark.core.domain.run import RunRecord, RunRoundRecord, RunSpec, RunState
from benchmark.core.domain.sample import (
    ObfuscationLevel,
    SampleFamily,
    SampleSource,
    SampleVariant,
)

__all__ = [
    "Artifact",
    "ArtifactKind",
    "ArtifactRef",
    "EvidenceEdge",
    "EvidenceRelation",
    "MetricGrade",
    "MetricResult",
    "ObfuscationLevel",
    "RunRecord",
    "RunRoundRecord",
    "RunSpec",
    "RunState",
    "SampleFamily",
    "SampleSource",
    "SampleVariant",
]
