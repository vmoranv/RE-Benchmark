"""OpenAI GPT family adapter."""

from __future__ import annotations

import os
from typing import ClassVar

from openai import AsyncOpenAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from benchmark.core.abstractions.model_adapter import ChatRequest, ModelAdapter, ModelCapabilities


def _build_kwargs(model: str, request: ChatRequest) -> dict:
    """Build OpenAI API kwargs from a ChatRequest."""
    kwargs: dict = {
        "model": model,
        "messages": request.messages,
        "max_tokens": request.max_tokens or 4096,
        "temperature": request.temperature,
    }
    if request.seed is not None:
        kwargs["seed"] = request.seed
    if request.json_schema is not None:
        kwargs["response_format"] = {"type": "json_object"}
    if request.tools:
        kwargs["tools"] = [{"type": "function", "function": t} for t in request.tools]
    return kwargs


def _parse_choice(choice) -> tuple[str, list[dict]]:
    """Extract text and tool calls from an OpenAI choice."""
    text = choice.message.content or ""
    calls: list[dict] = []
    if choice.message.tool_calls:
        for tc in choice.message.tool_calls:
            calls.append({"id": tc.id, "name": tc.function.name, "input": tc.function.arguments})
    return text, calls


class OpenAIAdapter(ModelAdapter):
    """OpenAI GPT-4o / GPT-4.1 / o-series adapter."""

    model_id: ClassVar[str] = "openai/gpt-4o"
    capabilities: ClassVar[ModelCapabilities] = ModelCapabilities(
        seed_support=True,
        json_schema=True,
        tool_call=True,
        cache_control=False,
        rate_limit_rpm=500,
        rate_limit_tpm=200_000,
        reasoning_budget=True,
        max_context_tokens=128_000,
        max_output_tokens=16_384,
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        underlying_model: str = "gpt-4o",
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=api_key or os.environ.get("OPENAI_API_KEY"),
            base_url=base_url,
        )
        self._underlying_model = underlying_model

    async def send(self, request: ChatRequest) -> dict:
        kwargs = _build_kwargs(self._underlying_model, request)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_random_exponential(multiplier=1, max=30),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.chat.completions.create(**kwargs)
                break

        content_text, tool_calls = _parse_choice(resp.choices[0])
        usage = {
            "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
            "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
            "cache_hit_tokens": (
                getattr(resp.usage, "prompt_tokens_details", None)
                and resp.usage.prompt_tokens_details.cached_tokens
            )
            or 0,
            "cost_usd": None,
        }
        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "usage": usage,
            "raw": resp.model_dump() if hasattr(resp, "model_dump") else {},
            "model_version": resp.model,
        }
