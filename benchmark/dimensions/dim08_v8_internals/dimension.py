"""D8 Dimension wrapper — V8 Internal State Inspection."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim08_v8_internals.challenge import V8InternalsChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ComplexityReductionMetric,
    TokenConsumptionMetric,
)


class V8InternalsDimension(BaseDimension):
    code = "D08"
    name = "V8 Internal State Inspection"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (V8InternalsChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ComplexityReductionMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
