"""D4 Dimension wrapper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim04_wasm_sourcemap.challenge import WasmSourceMapChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ComplexityReductionMetric,
    TokenConsumptionMetric,
)


class WasmSourceMapDimension(BaseDimension):
    code = "D04"
    name = "WASM / SourceMap / API Protocol Recovery"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (WasmSourceMapChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ComplexityReductionMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
