"""D5 Dimension wrapper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim05_anti_debug.challenge import AntiDebugChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    TokenConsumptionMetric,
)
from benchmark.metrics.specialized.m1_anti_debug_bypass import M1AntiDebugBypassRate


class AntiDebugDimension(BaseDimension):
    code = "D05"
    name = "Anti-Debug & Anti-Hook Bypass"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (AntiDebugChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M1AntiDebugBypassRate(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
