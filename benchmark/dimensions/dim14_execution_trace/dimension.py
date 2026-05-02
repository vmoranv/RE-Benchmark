"""D14 — Execution Trace Recording & Time Travel dimension."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim14_execution_trace.challenge import ExecutionTraceChallenge
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m6_evidence_chain import M6EvidenceChain


class ExecutionTraceDimension(BaseDimension):
    code = "D14"
    name = "Execution Trace Recording & Time Travel"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (ExecutionTraceChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M6EvidenceChain(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
