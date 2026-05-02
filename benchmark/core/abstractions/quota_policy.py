"""QuotaPolicy — rate limit, budget, and cache policy for LLM calls."""

from __future__ import annotations

from abc import ABC, abstractmethod


class QuotaPolicy(ABC):
    """Gatekeeper for LLM consumption.

    Implementations typically wrap a Redis token bucket plus a budget
    ledger. Failures here should fail fast — letting an over-budget run
    consume real tokens defeats the purpose.
    """

    @abstractmethod
    async def check_and_reserve(
        self,
        model_id: str,
        est_tokens: int,
        *,
        scope: str = "global",
    ) -> bool:
        """Return True if ``est_tokens`` may be consumed for ``model_id``.

        On success the policy must atomically reserve the tokens (and any
        cost estimate) so concurrent calls see consistent state.
        """

    @abstractmethod
    async def commit(
        self,
        model_id: str,
        actual_tokens: int,
        cost_usd: float,
        *,
        scope: str = "global",
    ) -> None:
        """Commit the actual usage after a successful call.

        If actual_tokens differs from the reservation, the policy adjusts
        the underlying counters. Implementations must be idempotent on the
        ``(scope, period_key, request_id)`` triple.
        """

    @abstractmethod
    async def release(self, model_id: str, est_tokens: int, *, scope: str = "global") -> None:
        """Release a prior reservation when the call did not happen."""
