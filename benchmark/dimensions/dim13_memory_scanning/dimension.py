"""D13 — Memory Scanning & Structure Analysis dimension."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim13_memory_scanning.challenge import MemoryScanningChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ReadabilityMetric,
    TokenConsumptionMetric,
)


class MemoryScanningDimension(BaseDimension):
    code = "D13"
    name = "Memory Scanning & Structure Analysis"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (MemoryScanningChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
