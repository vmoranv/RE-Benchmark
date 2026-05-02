"""D11 — Syscall Monitoring & JS Correlation dimension."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim11_syscall_monitor.challenge import SyscallMonitorChallenge
from benchmark.metrics.common import (
    CompletionRateMetric,
    ComplexityReductionMetric,
    TokenConsumptionMetric,
)


class SyscallMonitorDimension(BaseDimension):
    code = "D11"
    name = "Syscall Monitoring & JS Correlation"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (SyscallMonitorChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            ComplexityReductionMetric(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
