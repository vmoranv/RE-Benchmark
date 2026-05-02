"""Lightweight scaffolding for placeholder dimensions.

Each placeholder dimension has its own subpackage that imports
``PlaceholderDimension`` and binds it to the right ``code`` / ``name``.
This file centralizes the boilerplate so the 13 placeholders stay tiny.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from benchmark.core.abstractions.challenge import BaseChallenge
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.metric import BaseMetric
from benchmark.core.domain import SampleVariant


class PlaceholderDimension(BaseDimension):
    """No-op dimension used as a structural placeholder."""

    code: ClassVar[str] = "Dxx"
    name: ClassVar[str] = "Placeholder"
    paper_refs: ClassVar[list[str]] = []

    def list_challenges(self) -> Sequence[BaseChallenge]:
        return ()

    def list_metrics(self) -> Sequence[BaseMetric]:
        return ()

    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        return ()
