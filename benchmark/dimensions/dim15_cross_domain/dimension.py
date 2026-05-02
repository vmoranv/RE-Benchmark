"""D15 Dimension wrapper — Cross-Domain Evidence Correlation."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim15_cross_domain.challenge import CrossDomainChallenge
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m3_cross_domain import M3CrossDomainAccuracy
from benchmark.metrics.specialized.m6_evidence_chain import M6EvidenceChain


class CrossDomainDimension(BaseDimension):
    code = "D15"
    name = "Cross-Domain Evidence Correlation"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (CrossDomainChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M3CrossDomainAccuracy(),
            M6EvidenceChain(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
