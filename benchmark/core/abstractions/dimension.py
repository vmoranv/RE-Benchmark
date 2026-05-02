"""BaseDimension — the top-level contract for an evaluation dimension."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Sequence

    from benchmark.core.abstractions.challenge import BaseChallenge
    from benchmark.core.abstractions.metric import BaseMetric
    from benchmark.core.domain import SampleVariant


class BaseDimension(ABC):
    """One of the 18 evaluation dimensions defined in the proposal.

    Concrete subclasses live under `benchmark/dimensions/dimNN_*` and are
    discovered via entry points or explicit registration.
    """

    code: ClassVar[str]
    """Stable code, e.g. ``"D01"``, ``"D02"``."""

    name: ClassVar[str]
    """Human-readable name, e.g. ``"Deobfuscation"``."""

    paper_refs: ClassVar[list[str]] = []
    """Identifiers of the papers this dimension is grounded in."""

    @abstractmethod
    def list_challenges(self) -> Sequence[BaseChallenge]:
        """Return all challenges defined under this dimension.

        A dimension may host multiple challenges (e.g. D02 has known-opcode
        and unknown-opcode variants). The scheduler iterates over the
        returned sequence to enumerate evaluation tasks.
        """

    @abstractmethod
    def list_metrics(self) -> Sequence[BaseMetric]:
        """Return all metrics applicable to runs of this dimension.

        Includes both general metrics (completion-rate, token consumption)
        and dimension-specific metrics (e.g. M8 for D17, M9 for D18).
        """

    @abstractmethod
    def select_samples(self, filter_spec: dict) -> Sequence[SampleVariant]:
        """Pick samples matching ``filter_spec``.

        Filter keys typically include ``obfuscation_level``, ``obfuscator``,
        ``family_id``, and ``source``. Implementations should use the
        configured ``ArtifactStore`` and DB session to resolve samples.
        """
