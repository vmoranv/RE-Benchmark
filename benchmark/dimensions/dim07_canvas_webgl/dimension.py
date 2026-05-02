"""D7 Dimension wrapper — Canvas/WebGL Fingerprint & Game Engine RE."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim07_canvas_webgl.challenge import CanvasWebGLChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ReadabilityMetric,
    TokenConsumptionMetric,
)


class CanvasWebGLDimension(BaseDimension):
    code = "D07"
    name = "Canvas/WebGL Fingerprint & Game Engine RE"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (CanvasWebGLChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
