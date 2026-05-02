"""D1 Dimension wrapper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.core.sandbox.node_runner import NodeSubprocessRunner
from benchmark.dimensions.dim01_deobfuscation.challenge import DeobfuscationChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ComplexityReductionMetric,
    ReadabilityMetric,
    TokenConsumptionMetric,
)
from benchmark.metrics.specialized.m8_semantic_fidelity import M8SemanticFidelity


class DeobfuscationDimension(BaseDimension):
    code = "D01"
    name = "Deobfuscation"
    paper_refs: ClassVar[list[str]] = ["JsDeObsBench", "JSIMPLIFIER", "OBsmith"]

    def __init__(self, *, node_runner: NodeSubprocessRunner | None = None) -> None:
        # ``node_runner`` is optional: when None the challenge falls back to
        # the textual heuristic so unit tests stay offline. The API container
        # injects a shared NodeSubprocessRunner during normal startup.
        self._node_runner = node_runner

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (DeobfuscationChallenge(node_runner=self._node_runner),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
            ComplexityReductionMetric(),
            M8SemanticFidelity(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        # Real implementation queries the DB; the skeleton returns an empty
        # tuple so that consumers can still iterate without errors.
        return ()
