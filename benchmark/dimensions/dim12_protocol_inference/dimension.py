"""D12 — Protocol Pattern Inference & State Machine Reconstruction dimension."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim12_protocol_inference.challenge import ProtocolInferenceChallenge
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m7_protocol_automation import M7ProtocolAutomation


class ProtocolInferenceDimension(BaseDimension):
    code = "D12"
    name = "Protocol Pattern Inference & State Machine Reconstruction"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (ProtocolInferenceChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M7ProtocolAutomation(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
