"""End-to-end smoke tests covering D1 + RunService + MockModelAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from apps.api.container import (
    get_artifact_store,
)
from benchmark.core.adapters.model.mock import MockModelAdapter, MockResponseScript
from benchmark.core.domain import RunSpec, RunState
from benchmark.core.orchestration import RunService, compute_spec_digest
from benchmark.core.orchestration.default_evaluator import DefaultEvaluator
from benchmark.core.persistence.repositories.runs import InMemoryRunRepository
from benchmark.dimensions.dim01_deobfuscation.dimension import DeobfuscationDimension
from benchmark.samples.loader import SampleLoader

SEED_DIR = Path(__file__).resolve().parents[2] / "benchmark" / "samples" / "seed_samples"


_SUCCESS_SCRIPT = MockResponseScript(
    by_index=[
        # Round 1: first deobfuscation attempt
        "```javascript\n"
        "function calculateDiscount(price, isMember) {\n"
        "  const memberRate = 0.15;\n"
        "  const guestRate = 0.05;\n"
        "  if (isMember) return price * (1 - memberRate);\n"
        "  return price * (1 - guestRate);\n"
        "}\n"
        "module.exports = { calculateDiscount };\n"
        "```",
        # Round 2: refined version with names
        "```javascript\n"
        "function calculateDiscount(price, isMember) {\n"
        "  const MEMBER_RATE = 0.15;\n"
        "  const GUEST_RATE = 0.05;\n"
        "  return price * (1 - (isMember ? MEMBER_RATE : GUEST_RATE));\n"
        "}\n"
        "module.exports = { calculateDiscount };\n"
        "```",
        # Round 3: highly readable
        "```javascript\n"
        "/** Compute the discounted price for a customer. */\n"
        "function calculateDiscount(price, isMember) {\n"
        "  const MEMBER_DISCOUNT = 0.15;\n"
        "  const GUEST_DISCOUNT = 0.05;\n"
        "  const discount = isMember ? MEMBER_DISCOUNT : GUEST_DISCOUNT;\n"
        "  return price * (1 - discount);\n"
        "}\n"
        "module.exports = { calculateDiscount };\n"
        "```",
    ]
)


@pytest.fixture
def fresh_service() -> RunService:
    """Build a RunService with isolated in-memory state for each test."""
    return RunService(
        repository=InMemoryRunRepository(),
        artifact_store=get_artifact_store(),
        evaluator=DefaultEvaluator(),
    )


@pytest.fixture
def loader() -> SampleLoader:
    return SampleLoader(get_artifact_store())


async def _load_smoke_sample(loader: SampleLoader):
    pairs = await loader.load_dimension(SEED_DIR, "D01")
    assert pairs, "smoke_001 sample missing under seed_samples/D01"
    return pairs[0]


@pytest.mark.asyncio
async def test_sample_loader_smoke(loader):
    family, variant = await _load_smoke_sample(loader)
    assert family.name == "smoke_001"
    assert variant.obfuscation_level.value == "L2"
    assert variant.metadata["semantic_test_cases"]


@pytest.mark.asyncio
async def test_run_service_finalizes_under_mock(fresh_service, loader):
    _family, variant = await _load_smoke_sample(loader)
    spec = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D01",
        model_id="mock/echo-v1",
        seed=42,
    )
    record = await fresh_service.submit(spec)
    final = await fresh_service.execute(
        record.id,
        dimension=DeobfuscationDimension(),
        sample=variant,
        model=MockModelAdapter(_SUCCESS_SCRIPT),
    )
    assert final.state == RunState.FINALIZED
    assert final.error is None
    # 3 LLM rounds + 1 judge round
    assert len(final.rounds) == 4
    assert {r.round_no for r in final.rounds} == {1, 2, 3, 99}
    # All rounds succeeded
    assert all(r.state == "SUCCESS" for r in final.rounds)
    # Metric snapshot was recorded
    assert "metric_results" in final.metadata


@pytest.mark.asyncio
async def test_run_service_records_token_usage(fresh_service, loader):
    _family, variant = await _load_smoke_sample(loader)
    spec = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D01",
        model_id="mock/echo-v1",
        seed=99,
    )
    record = await fresh_service.submit(spec)
    final = await fresh_service.execute(
        record.id,
        dimension=DeobfuscationDimension(),
        sample=variant,
        model=MockModelAdapter(_SUCCESS_SCRIPT),
    )
    main_rounds = [r for r in final.rounds if r.round_no in (1, 2, 3)]
    total_input = sum(r.input_tokens for r in main_rounds)
    total_output = sum(r.output_tokens for r in main_rounds)
    assert total_input > 0
    assert total_output > 0


@pytest.mark.asyncio
async def test_spec_digest_is_deterministic(loader):
    _family, variant = await _load_smoke_sample(loader)
    spec_a = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D01",
        model_id="mock/echo-v1",
        seed=7,
    )
    spec_b = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D01",
        model_id="mock/echo-v1",
        seed=7,
    )
    assert compute_spec_digest(spec_a) == compute_spec_digest(spec_b)
    spec_c = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D01",
        model_id="mock/echo-v1",
        seed=8,
    )
    assert compute_spec_digest(spec_a) != compute_spec_digest(spec_c)


@pytest.mark.asyncio
async def test_unknown_dimension_fails_gracefully(fresh_service, loader):
    _family, variant = await _load_smoke_sample(loader)
    spec = RunSpec(
        sample_variant_id=variant.id,
        dimension_code="D99",  # not registered
        model_id="mock/echo-v1",
        seed=1,
    )
    record = await fresh_service.submit(spec)

    class EmptyDimension(DeobfuscationDimension):
        def list_challenges(self):
            return ()

    final = await fresh_service.execute(
        record.id,
        dimension=EmptyDimension(),
        sample=variant,
        model=MockModelAdapter(),
    )
    assert final.state == RunState.FAILED
    assert final.error == "dimension has no challenges"
