"""Tests for the D1 deobfuscation challenge prompt building."""

from __future__ import annotations

from uuid import uuid4

from benchmark.core.domain import (
    ObfuscationLevel,
    SampleVariant,
)
from benchmark.dimensions.dim01_deobfuscation.challenge import DeobfuscationChallenge


def _sample(level: ObfuscationLevel = ObfuscationLevel.L2) -> SampleVariant:
    return SampleVariant(
        id=uuid4(),
        family_id=uuid4(),
        obfuscation_level=level,
        original_artifact_id=uuid4(),
        obfuscated_artifact_id=uuid4(),
        metadata={"obfuscated_size": 200},
    )


def test_build_round1_renders_template():
    ch = DeobfuscationChallenge()
    out = ch.build_prompt(_sample(), 1, prior=[])
    assert "deobfuscate" in out.lower()
    assert "{{ obfuscated_code_inline }}" not in out


def test_parse_response_extracts_fenced_code():
    ch = DeobfuscationChallenge()
    parsed = ch.parse_response(
        "Here is the cleaned version:\n```javascript\nfunction f() { return 1; }\n```\nThanks.",
        round_no=1,
    )
    assert parsed["ok"] is True
    assert "function f" in parsed["payload"]


def test_objective_check_assigns_grade():
    ch = DeobfuscationChallenge()
    sample = _sample()
    parsed = {"ok": True, "round_no": 1, "payload": "function add(a, b) { return a + b; }"}
    result = ch.objective_check(parsed, sample)
    assert result.grade.value in {"pass", "partial", "fail"}
    assert 0.0 <= result.score <= 1.0


def test_objective_check_empty_payload_fails():
    ch = DeobfuscationChallenge()
    parsed = {"ok": False, "round_no": 1, "payload": ""}
    result = ch.objective_check(parsed, _sample())
    assert result.grade.value == "fail"
    assert result.score == 0.0
