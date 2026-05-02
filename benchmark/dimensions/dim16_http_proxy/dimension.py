"""D16 Dimension wrapper — HTTP Proxy & Traffic Interception."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim16_http_proxy.challenge import HttpProxyChallenge
from benchmark.metrics.common import CompletionRateMetric, ReadabilityMetric, TokenConsumptionMetric


class HttpProxyDimension(BaseDimension):
    code = "D16"
    name = "HTTP Proxy & Traffic Interception"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (HttpProxyChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ReadabilityMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
