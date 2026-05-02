"""Application-wide DI container.

Centralises construction of in-memory components used by the API router.
Supports multi-model selection (Anthropic, OpenAI, Mock) and auto-discovery
of all 18 evaluation dimensions.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from benchmark.core.abstractions.artifact_store import ArtifactStore
from benchmark.core.abstractions.dimension import BaseDimension
from benchmark.core.abstractions.model_adapter import ModelAdapter
from benchmark.core.adapters.artifact.filesystem import FilesystemArtifactStore
from benchmark.core.adapters.model.anthropic import AnthropicAdapter
from benchmark.core.adapters.model.mock import MockModelAdapter
from benchmark.core.adapters.model.openai import OpenAIAdapter
from benchmark.core.orchestration import DefaultEvaluator, RunService
from benchmark.core.persistence.repositories.runs import (
    InMemoryRunRepository,
    RunRepository,
)
from benchmark.core.sandbox.node_runner import NodeSubprocessRunner

# ---------------------------------------------------------------------------
# Repositories & stores
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_repository() -> RunRepository:
    return InMemoryRunRepository()


@lru_cache(maxsize=1)
def get_artifact_store() -> ArtifactStore:
    root = Path("./artifacts").resolve()
    root.mkdir(parents=True, exist_ok=True)
    return FilesystemArtifactStore(root)


@lru_cache(maxsize=1)
def get_run_service() -> RunService:
    return RunService(
        repository=get_repository(),
        artifact_store=get_artifact_store(),
        evaluator=DefaultEvaluator(),
    )


# ---------------------------------------------------------------------------
# Model adapters
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_default_model() -> MockModelAdapter:
    """Default model used when no API key is configured. Deterministic."""
    return MockModelAdapter()


def get_model(model_id: str) -> ModelAdapter:
    """Resolve a model adapter by id string.

    Supported prefixes:
      - ``mock/*``         → MockModelAdapter (deterministic)
      - ``anthropic/*``    → AnthropicAdapter (requires ANTHROPIC_API_KEY)
      - ``openai/*``       → OpenAIAdapter (requires OPENAI_API_KEY)
    """
    if model_id.startswith("mock/"):
        return get_default_model()

    if model_id.startswith("anthropic/"):
        underlying = model_id.removeprefix("anthropic/")
        return AnthropicAdapter(underlying_model=underlying)

    if model_id.startswith("openai/"):
        underlying = model_id.removeprefix("openai/")
        return OpenAIAdapter(underlying_model=underlying)

    return get_default_model()


# ---------------------------------------------------------------------------
# Sandbox
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def get_node_runner() -> NodeSubprocessRunner | None:
    """Return a shared Node subprocess runner, or ``None`` if Node is unavailable."""
    try:
        return NodeSubprocessRunner()
    except FileNotFoundError:
        return None


# ---------------------------------------------------------------------------
# Dimension registry
# ---------------------------------------------------------------------------


def _import_dimensions() -> dict[str, type[BaseDimension]]:
    """Lazily import and index all dimension classes by code."""
    from benchmark.dimensions.dim01_deobfuscation.dimension import DeobfuscationDimension
    from benchmark.dimensions.dim02_jsvmp.dimension import JSVMPDimension
    from benchmark.dimensions.dim03_tls_fingerprint.dimension import TLSFingerprintDimension
    from benchmark.dimensions.dim04_wasm_sourcemap.dimension import WasmSourceMapDimension
    from benchmark.dimensions.dim05_anti_debug.dimension import AntiDebugDimension
    from benchmark.dimensions.dim06_hook_injection.dimension import HookInjectionDimension
    from benchmark.dimensions.dim07_canvas_webgl.dimension import CanvasWebGLDimension
    from benchmark.dimensions.dim08_v8_internals.dimension import V8InternalsDimension
    from benchmark.dimensions.dim09_native_binary.dimension import NativeBinaryDimension
    from benchmark.dimensions.dim10_android_webview.dimension import AndroidWebViewDimension
    from benchmark.dimensions.dim11_syscall_monitor.dimension import SyscallMonitorDimension
    from benchmark.dimensions.dim12_protocol_inference.dimension import ProtocolInferenceDimension
    from benchmark.dimensions.dim13_memory_scanning.dimension import MemoryScanningDimension
    from benchmark.dimensions.dim14_execution_trace.dimension import ExecutionTraceDimension
    from benchmark.dimensions.dim15_cross_domain.dimension import CrossDomainDimension
    from benchmark.dimensions.dim16_http_proxy.dimension import HttpProxyDimension
    from benchmark.dimensions.dim17_obfuscator_correctness.dimension import (
        ObfuscatorCorrectnessDimension,
    )
    from benchmark.dimensions.dim18_llm_semantic_depth.dimension import LLMSemanticDepthDimension

    dims: list[type[BaseDimension]] = [
        DeobfuscationDimension,
        JSVMPDimension,
        TLSFingerprintDimension,
        WasmSourceMapDimension,
        AntiDebugDimension,
        HookInjectionDimension,
        CanvasWebGLDimension,
        V8InternalsDimension,
        NativeBinaryDimension,
        AndroidWebViewDimension,
        SyscallMonitorDimension,
        ProtocolInferenceDimension,
        MemoryScanningDimension,
        ExecutionTraceDimension,
        CrossDomainDimension,
        HttpProxyDimension,
        ObfuscatorCorrectnessDimension,
        LLMSemanticDepthDimension,
    ]
    result: dict[str, type[BaseDimension]] = {}
    for d in dims:
        result[d.code] = d
    return result


@lru_cache(maxsize=1)
def get_dimension_registry() -> dict[str, type[BaseDimension]]:
    return _import_dimensions()


def build_dimension(code: str) -> BaseDimension | None:
    """Instantiate a dimension by code, injecting common dependencies."""
    registry = get_dimension_registry()
    cls = registry.get(code)
    if cls is None:
        return None

    # D01 needs NodeRunner
    if code == "D01":
        from benchmark.dimensions.dim01_deobfuscation.dimension import DeobfuscationDimension

        node_runner = get_node_runner()
        return DeobfuscationDimension(node_runner=node_runner)

    return cls()
