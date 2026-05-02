"""D9 Dimension wrapper — Native Binary Instrumentation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim09_native_binary.challenge import NativeBinaryChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ReadabilityMetric,
    TokenConsumptionMetric,
)


class NativeBinaryDimension(BaseDimension):
    code = "D09"
    name = "Native Binary Instrumentation"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (NativeBinaryChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
