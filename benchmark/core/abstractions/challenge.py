"""BaseChallenge — single evaluation task within a dimension."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from pydantic import BaseModel, Field

from benchmark.core.domain import MetricGrade

if TYPE_CHECKING:
    from benchmark.core.domain import SampleVariant


class ChallengeResult(BaseModel):
    """Outcome of objective_check for a single round."""

    grade: MetricGrade
    score: float = Field(ge=0.0, le=1.0)
    details: dict = Field(default_factory=dict)
    rationale: str | None = None
    evidence_artifact_ids: list[str] = Field(default_factory=list)


class BaseChallenge(ABC):
    """A challenge encapsulates: prompt construction, response parsing,
    and objective verification of LLM output for a sample.
    """

    code: ClassVar[str]
    """Stable code, e.g. ``"D01.deobfuscate"``, ``"D02.jsvmp.known"``."""

    rounds: ClassVar[int] = 3
    """Number of rounds. Default per JsDeObsBench is 3."""

    early_terminate_on_pass: ClassVar[bool] = False
    """If true, scheduler may skip remaining rounds once grade=pass."""

    allow_retry: ClassVar[bool] = True
    """Whether failed verification advances to the next round vs aborts."""

    @abstractmethod
    def build_prompt(
        self,
        sample: SampleVariant,
        round_no: int,
        prior: list[dict],
    ) -> str:
        """Build the prompt for the given round.

        ``prior`` is the list of (prompt, response, grade, details) dicts
        from previous rounds. round_no is 1-indexed; ``99`` is reserved
        for the JUDGE round and should not be passed here.
        """

    @abstractmethod
    def parse_response(self, response: str, round_no: int) -> dict:
        """Extract a structured payload from the raw LLM response.

        Implementations should be lenient (regex / fenced blocks / JSON
        tolerant parsing) but must return a dict with at least ``ok: bool``
        and ``payload`` keys, so downstream verification can act uniformly.
        """

    @abstractmethod
    def objective_check(
        self,
        parsed: dict,
        sample: SampleVariant,
    ) -> ChallengeResult:
        """Verify the parsed payload against ground truth / test suite.

        This is the core of objective evaluation — it must be deterministic
        and side-effect-free aside from sandbox execution. The returned
        :class:`ChallengeResult` feeds both the state machine (for grade)
        and the metrics layer (for score).
        """
