"""BaseEvaluator — orchestrates the 3-round Prompt evaluation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from benchmark.core.abstractions.challenge import BaseChallenge
    from benchmark.core.abstractions.model_adapter import ModelAdapter
    from benchmark.core.domain import SampleVariant


class BaseEvaluator(ABC):
    """Drives the per-run execution loop: R1 -> V1 -> R2 -> V2 -> R3 -> V3 -> JUDGE.

    Concrete subclasses customize prompt routing, retry policy, and the
    judge step. The default evaluator (provided in
    ``benchmark.core.orchestration.default_evaluator``) handles the common
    case for all dimensions.
    """

    @abstractmethod
    async def run_round(
        self,
        run_id: UUID,
        round_no: int,
        challenge: BaseChallenge,
        sample: SampleVariant,
        *,
        model: ModelAdapter,
        prior_rounds: list[dict],
    ) -> dict:
        """Execute a single round end-to-end.

        Steps:
            1. Build prompt via ``challenge.build_prompt``.
            2. Send to model (subject to ``QuotaPolicy.check_and_reserve``).
            3. Parse response via ``challenge.parse_response``.
            4. Persist a :class:`RunRoundRecord` with usage and artifacts.
            5. Run ``challenge.objective_check`` for verification.

        Returns a dict containing at least ``state``, ``grade``, ``parsed``,
        ``response_text`` and ``usage`` so callers can chain the next round.
        """

    @abstractmethod
    async def judge(self, run_id: UUID, all_rounds: list[dict]) -> dict:
        """Run the LLM-as-judge pass over all completed rounds.

        Produces subjective scores (readability, clarity) that complement
        the objective grade. Stored under ``round_no=99``.
        """
