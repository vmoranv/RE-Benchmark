"""D17 Dimension wrapper — Obfuscator Correctness Verification."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim17_obfuscator_correctness.challenge import (
    ObfuscatorCorrectnessChallenge,
)
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m8_semantic_fidelity import M8SemanticFidelity


class ObfuscatorCorrectnessDimension(BaseDimension):
    code = "D17"
    name = "Obfuscator Correctness Verification"
    paper_refs: ClassVar[list[str]] = ["OBsmith"]

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (ObfuscatorCorrectnessChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M8SemanticFidelity(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
