"""Mock LLM adapter — deterministic responses for testing and Q2 fixture mode.

The mock walks a configurable script of canned responses. When the script
is exhausted it returns a generic acknowledgement so the pipeline still
reaches a terminal state.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import ClassVar

from benchmark.core.abstractions.model_adapter import ChatRequest, ModelAdapter, ModelCapabilities


@dataclass
class MockResponseScript:
    """Pre-canned responses keyed by prompt hash or by sequential index."""

    by_index: list[str] = field(default_factory=list)
    by_prompt_sha: dict[str, str] = field(default_factory=dict)
    fallback: str = "```javascript\n// mock fallback response\n```\n"


class MockModelAdapter(ModelAdapter):
    """Deterministic adapter used in unit tests and Q2 replay fixtures."""

    model_id: ClassVar[str] = "mock/echo-v1"
    capabilities: ClassVar[ModelCapabilities] = ModelCapabilities(
        seed_support=True,
        json_schema=False,
        tool_call=False,
        cache_control=False,
        rate_limit_rpm=None,
        rate_limit_tpm=None,
        reasoning_budget=False,
        max_context_tokens=128_000,
        max_output_tokens=8_192,
    )

    def __init__(self, script: MockResponseScript | None = None) -> None:
        self._script = script or MockResponseScript()
        self._call_count = 0

    def _pick_response(self, messages: list[dict]) -> str:
        prompt_text = "\n".join(m.get("content", "") for m in messages)
        sha = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
        if sha in self._script.by_prompt_sha:
            return self._script.by_prompt_sha[sha]
        if self._call_count < len(self._script.by_index):
            return self._script.by_index[self._call_count]
        return self._script.fallback

    async def send(self, request: ChatRequest) -> dict:
        content = self._pick_response(request.messages)
        self._call_count += 1
        prompt_text = "\n".join(m.get("content", "") for m in request.messages)
        return {
            "content": content,
            "tool_calls": [],
            "usage": {
                "input_tokens": max(1, len(prompt_text) // 4),
                "output_tokens": max(1, len(content) // 4),
                "cache_hit_tokens": 0,
                "cost_usd": 0.0,
            },
            "raw": {"mock": True, "seed": request.seed, "call_index": self._call_count - 1},
            "model_version": "mock-2026-05-02",
        }

    @property
    def call_count(self) -> int:
        return self._call_count
