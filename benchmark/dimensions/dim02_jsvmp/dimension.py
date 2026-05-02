"""D2 Dimension wrapper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim02_jsvmp.challenge import JSVMPChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ReadabilityMetric,
    TokenConsumptionMetric,
)


class JSVMPDimension(BaseDimension):
    code = "D02"
    name = "JSVMP / VM Unpacking"
    paper_refs: ClassVar[list[str]] = ["JSIMPLIFIER", "RSA 2025 Report"]

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (JSVMPChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
