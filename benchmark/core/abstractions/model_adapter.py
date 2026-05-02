"""ModelAdapter — unified contract over multi-vendor LLM APIs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel, Field


class ModelCapabilities(BaseModel):
    """Capability probe for a model. Drives feature selection at runtime."""

    seed_support: bool = False
    json_schema: bool = False
    tool_call: bool = False
    cache_control: bool = False
    rate_limit_rpm: int | None = None
    rate_limit_tpm: int | None = None
    reasoning_budget: bool = False
    max_context_tokens: int | None = None
    max_output_tokens: int | None = None
    metadata: dict = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Structured request payload for ModelAdapter.send."""

    messages: list[dict]
    seed: int | None = None
    max_tokens: int | None = None
    temperature: float = 0.0
    json_schema: dict | None = None
    tools: list[dict] | None = None
    cache_control: dict | None = None
    timeout: float | None = None


class ModelAdapter(ABC):
    """Adapter for a specific (vendor, model) tuple.

    The unified interface intentionally mirrors the union of features
    across Anthropic, OpenAI, Gemini, and vLLM. Adapters silently degrade
    unsupported features (recorded in ``capabilities``).
    """

    model_id: ClassVar[str]
    """Stable model identifier, e.g. ``"anthropic/claude-opus-4-7"``."""

    capabilities: ClassVar[ModelCapabilities]

    @abstractmethod
    async def send(self, request: ChatRequest) -> dict:
        """Send a chat completion request.

        Returns a dict with the following shape::

            {
                "content": str,                # primary text output
                "tool_calls": list[dict],      # may be empty
                "usage": {
                    "input_tokens": int,
                    "output_tokens": int,
                    "cache_hit_tokens": int,
                    "cost_usd": float | None,
                },
                "raw": dict,                   # vendor-native payload
                "model_version": str,          # for audit / replay
            }

        Implementations should retry on retryable errors (5xx, timeouts)
        with bounded exponential backoff and surface non-retryable
        failures by raising.
        """
