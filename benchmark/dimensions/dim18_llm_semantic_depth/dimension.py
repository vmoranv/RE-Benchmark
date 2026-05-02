"""D18 Dimension wrapper — LLM Semantic Understanding Depth Probing."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant
from benchmark.dimensions.dim18_llm_semantic_depth.challenge import LLMSemanticDepthChallenge
from benchmark.metrics.common import CompletionRateMetric, TokenConsumptionMetric
from benchmark.metrics.specialized.m8_semantic_fidelity import M8SemanticFidelity
from benchmark.metrics.specialized.m9_reasoning_decay import M9ReasoningDecay


class LLMSemanticDepthDimension(BaseDimension):
    code = "D18"
    name = "LLM Semantic Understanding Depth Probing"
    paper_refs: ClassVar[list[str]] = ["The Code Barrier"]

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return (LLMSemanticDepthChallenge(),)

    def list_metrics(self) -> Sequence[BaseMetric]:
        return (
            CompletionRateMetric(),
            TokenConsumptionMetric(),
            M9ReasoningDecay(),
            M8SemanticFidelity(),
        )

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
