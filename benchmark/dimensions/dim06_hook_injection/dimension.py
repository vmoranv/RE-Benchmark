"""D6 Dimension wrapper — Runtime Hook Injection Quality."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim06_hook_injection.challenge import HookInjectionChallenge
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m2_hook_stealth import M2HookStealthScore


class HookInjectionDimension(BaseDimension):
    code = "D06"
    name = "Runtime Hook Injection Quality"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (HookInjectionChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M2HookStealthScore(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
