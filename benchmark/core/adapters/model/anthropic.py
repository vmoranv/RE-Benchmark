"""Anthropic Claude adapter."""

from __future__ import annotations

import os
from typing import ClassVar

from anthropic import AsyncAnthropic
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)

from benchmark.core.abstractions.model_adapter import ChatRequest, ModelAdapter, ModelCapabilities


def _split_system(messages: list[dict]) -> tuple[str | None, list[dict]]:
    """Extract system messages into a single string (Anthropic convention)."""
    system_text: str | None = None
    norm: list[dict] = []
    for m in messages:
        if m["role"] == "system":
            system_text = (
                m["content"] if system_text is None else system_text + "\n\n" + m["content"]
            )
        else:
            norm.append(m)
    return system_text, norm


def _parse_blocks(content: list) -> tuple[str, list[dict]]:
    """Normalize content blocks into text + tool_calls."""
    text = ""
    calls: list[dict] = []
    for block in content:
        if getattr(block, "type", None) == "text":
            text += block.text
        elif getattr(block, "type", None) == "tool_use":
            calls.append({"id": block.id, "name": block.name, "input": block.input})
    return text, calls


class AnthropicAdapter(ModelAdapter):
    """Anthropic Claude family adapter (Opus / Sonnet / Haiku)."""

    model_id: ClassVar[str] = "anthropic/claude-opus-4-7"
    capabilities: ClassVar[ModelCapabilities] = ModelCapabilities(
        seed_support=False,
        json_schema=True,
        tool_call=True,
        cache_control=True,
        rate_limit_rpm=4000,
        rate_limit_tpm=400_000,
        reasoning_budget=True,
        max_context_tokens=200_000,
        max_output_tokens=64_000,
    )

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        underlying_model: str = "claude-opus-4-7-20260101",
    ) -> None:
        self._client = AsyncAnthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"),
            base_url=base_url,
        )
        self._underlying_model = underlying_model

    async def send(self, request: ChatRequest) -> dict:
        system_text, norm_messages = _split_system(request.messages)

        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_random_exponential(multiplier=1, max=30),
            retry=retry_if_exception_type((TimeoutError, ConnectionError)),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.messages.create(
                    model=self._underlying_model,
                    messages=norm_messages,
                    system=system_text or "",
                    max_tokens=request.max_tokens or 4096,
                    temperature=request.temperature,
                    tools=request.tools or [],
                    timeout=request.timeout,
                )
                break

        content_text, tool_calls = _parse_blocks(resp.content)
        usage = {
            "input_tokens": resp.usage.input_tokens,
            "output_tokens": resp.usage.output_tokens,
            "cache_hit_tokens": getattr(resp.usage, "cache_read_input_tokens", 0) or 0,
            "cost_usd": None,
        }
        return {
            "content": content_text,
            "tool_calls": tool_calls,
            "usage": usage,
            "raw": resp.model_dump() if hasattr(resp, "model_dump") else {},
            "model_version": resp.model,
        }
