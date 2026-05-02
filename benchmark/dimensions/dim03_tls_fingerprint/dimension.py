"""D3 Dimension wrapper."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim03_tls_fingerprint.challenge import TLSFingerprintChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    TokenConsumptionMetric,
)


class TLSFingerprintDimension(BaseDimension):
    code = "D03"
    name = "TLS Fingerprint Spoofing"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (TLSFingerprintChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
