"""Sandbox integration tests — NodeSubprocessRunner + smoke_001 semantic cases."""

from __future__ import annotations

import pytest

from benchmark.core.sandbox.node_runner import NodeSubprocessRunner

# The known-good original.js for smoke_001 exports calculateDiscount.
_ORIGINAL_JS = (
    "function calculateDiscount(price, isMember) {\n"
    "  const memberRate = 0.15;\n"
    "  const guestRate = 0.05;\n"
    "  if (isMember) return price * (1 - memberRate);\n"
    "  return price * (1 - guestRate);\n"
    "}\n"
    "module.exports = { calculateDiscount };\n"
)

_TEST_CASES = [
    {"name": "member 100", "args": [100, True], "expected": 85},
    {"name": "guest 200", "args": [200, False], "expected": 190},
]


@pytest.fixture()
def runner() -> NodeSubprocessRunner:
    return NodeSubprocessRunner(timeout_seconds=10)


class TestNodeRunner:
    def test_all_cases_pass_with_correct_code(self, runner: NodeSubprocessRunner) -> None:
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            runner.run(
                candidate_code=_ORIGINAL_JS,
                export_name="calculateDiscount",
                test_cases=_TEST_CASES,
            )
        )
        assert result.passed == 2
        assert result.total == 2
        assert result.pass_ratio == 1.0
        assert not result.timed_out
        for c in result.cases:
            assert c.passed, f"{c.name}: expected {c.expected}, got {c.actual}"

    def test_wrong_logic_fails_cases(self, runner: NodeSubprocessRunner) -> None:
        import asyncio

        wrong_code = _ORIGINAL_JS.replace("0.15", "0.50").replace("0.05", "0.50")
        result = asyncio.get_event_loop().run_until_complete(
            runner.run(
                candidate_code=wrong_code,
                export_name="calculateDiscount",
                test_cases=_TEST_CASES,
            )
        )
        assert result.passed == 0
        assert result.total == 2
        assert result.pass_ratio == 0.0

    def test_missing_export_fails_gracefully(self, runner: NodeSubprocessRunner) -> None:
        import asyncio

        bad_code = "module.exports = { otherFunc: () => 42 };"
        result = asyncio.get_event_loop().run_until_complete(
            runner.run(
                candidate_code=bad_code,
                export_name="calculateDiscount",
                test_cases=_TEST_CASES,
            )
        )
        assert result.total == 2
        assert result.passed == 0
        assert all(not c.passed for c in result.cases)
        assert all(c.error for c in result.cases)

    def test_empty_cases_returns_zero(self, runner: NodeSubprocessRunner) -> None:
        import asyncio

        result = asyncio.get_event_loop().run_until_complete(
            runner.run(
                candidate_code="module.exports = { calculateDiscount: () => 0 };",
                export_name="calculateDiscount",
                test_cases=[],
            )
        )
        assert result.passed == 0
        assert result.total == 0
        assert result.pass_ratio == 0.0
