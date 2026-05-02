"""BaseMetric — pure-function metric calculator."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from benchmark.core.domain import MetricResult


class BaseMetric(ABC):
    """A metric computes a single :class:`MetricResult` from a run record.

    Implementations MUST be pure: no I/O, no global state, no clocks. The
    only inputs are the run record, its rounds, and a mapping of artifact
    bytes (lazily loaded via the ``artifacts`` resolver).
    """

    code: ClassVar[str]
    """Stable identifier, e.g. ``"completion_rate"`` or ``"M8"``."""

    name: ClassVar[str]
    """Human-readable label."""

    unit: ClassVar[str]
    """Unit string, e.g. ``"percent"``, ``"tokens"``, ``"ms"``."""

    higher_is_better: ClassVar[bool] = True
    """Direction for ranking. False for cost / latency / decay rate."""

    weight: ClassVar[float] = 1.0
    """Default weight when aggregated into a composite score."""

    @abstractmethod
    def compute(
        self,
        run_record: dict,
        rounds: list[dict],
        artifacts: dict,
    ) -> MetricResult:
        """Compute the metric.

        ``run_record`` is the serialized :class:`RunRecord`.
        ``rounds`` is the ordered list of round dicts (R1..R3..JUDGE).
        ``artifacts`` maps artifact_id -> bytes (only requested ones).
        """
