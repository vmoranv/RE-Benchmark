"""Redis-backed token-bucket quota policy."""

from __future__ import annotations

import time

from redis.asyncio import Redis

from benchmark.core.abstractions.quota_policy import QuotaPolicy

_DEFAULT_REFILL_PER_SECOND = 1000.0  # tokens / second


class TokenBucketQuotaPolicy(QuotaPolicy):
    """Distributed token bucket using Redis EVAL.

    Each model has a bucket: capacity = burst tokens, refill rate per
    second. ``check_and_reserve`` atomically deducts ``est_tokens`` if
    available, otherwise returns False without side effects.
    """

    SCRIPT = """
    local bucket_key = KEYS[1]
    local now = tonumber(ARGV[1])
    local capacity = tonumber(ARGV[2])
    local refill_per_sec = tonumber(ARGV[3])
    local cost = tonumber(ARGV[4])

    local data = redis.call('HMGET', bucket_key, 'tokens', 'updated_at')
    local tokens = tonumber(data[1]) or capacity
    local updated_at = tonumber(data[2]) or now

    local elapsed = math.max(0, now - updated_at)
    tokens = math.min(capacity, tokens + elapsed * refill_per_sec)

    if tokens < cost then
        redis.call('HSET', bucket_key, 'tokens', tokens, 'updated_at', now)
        return 0
    end
    tokens = tokens - cost
    redis.call('HSET', bucket_key, 'tokens', tokens, 'updated_at', now)
    redis.call('EXPIRE', bucket_key, 3600)
    return 1
    """

    def __init__(
        self,
        redis: Redis,
        *,
        capacity_per_model: dict[str, int] | None = None,
        refill_per_second_per_model: dict[str, float] | None = None,
        default_capacity: int = 100_000,
    ) -> None:
        self._redis = redis
        self._capacity = capacity_per_model or {}
        self._refill = refill_per_second_per_model or {}
        self._default_capacity = default_capacity
        self._sha: str | None = None

    async def _ensure_loaded(self) -> str:
        if self._sha is None:
            self._sha = await self._redis.script_load(self.SCRIPT)
        return self._sha

    def _bucket_key(self, model_id: str, scope: str) -> str:
        return f"quota:{scope}:{model_id}"

    async def check_and_reserve(
        self,
        model_id: str,
        est_tokens: int,
        *,
        scope: str = "global",
    ) -> bool:
        sha = await self._ensure_loaded()
        cap = self._capacity.get(model_id, self._default_capacity)
        refill = self._refill.get(model_id, _DEFAULT_REFILL_PER_SECOND)
        result = await self._redis.evalsha(
            sha,
            1,
            self._bucket_key(model_id, scope),
            time.time(),
            cap,
            refill,
            est_tokens,
        )
        return bool(int(result))

    async def commit(
        self,
        model_id: str,
        actual_tokens: int,
        cost_usd: float,
        *,
        scope: str = "global",
    ) -> None:
        # Adjust the ledger; if actual > est the next call will see the
        # corrected balance, if actual < est release the excess.
        ledger_key = f"quota:ledger:{scope}:{model_id}"
        await self._redis.hincrby(ledger_key, "tokens_consumed", int(actual_tokens))
        # cost_usd as float string
        await self._redis.hincrbyfloat(ledger_key, "cost_usd", cost_usd)
        await self._redis.hincrby(ledger_key, "request_count", 1)

    async def release(self, model_id: str, est_tokens: int, *, scope: str = "global") -> None:
        # Refill the bucket by est_tokens (capped to capacity).
        bucket_key = self._bucket_key(model_id, scope)
        cap = self._capacity.get(model_id, self._default_capacity)
        async with self._redis.pipeline(transaction=True) as pipe:
            await pipe.hincrbyfloat(bucket_key, "tokens", est_tokens)
            await pipe.hset(bucket_key, "updated_at", time.time())
            await pipe.execute()
        # Cap the value
        cur = await self._redis.hget(bucket_key, "tokens")
        if cur and float(cur) > cap:
            await self._redis.hset(bucket_key, "tokens", cap)
