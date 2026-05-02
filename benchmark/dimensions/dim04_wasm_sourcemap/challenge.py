"""D4 WASM/SourceMap challenge — recover protocol/API structure from compiled data."""

from __future__ import annotations

import re
from pathlib import Path

import jinja2

from benchmark.core.abstractions.challenge import BaseChallenge, ChallengeResult
from benchmark.core.domain import MetricGrade, SampleVariant

_PROMPT_DIR = Path(__file__).parent / "prompts"
_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(_PROMPT_DIR),
    undefined=jinja2.StrictUndefined,
    autoescape=False,
    keep_trailing_newline=True,
)

_FENCED_BLOCK = re.compile(r"```(?:json|javascript|js|typescript|yaml)?\n(.*?)\n```", re.DOTALL)

# Common API/protocol schema field indicators.
_SCHEMA_FIELDS = {
    "endpoint",
    "method",
    "path",
    "url",
    "headers",
    "body",
    "params",
    "query",
    "response",
    "request",
    "payload",
    "field",
    "type",
    "name",
    "description",
}
_PROTOCOL_KW = {
    "api",
    "endpoint",
    "route",
    "request",
    "response",
    "header",
    "parameter",
    "websocket",
    "wasm",
    "sourcemap",
    "protocol",
}


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float] = {}

    lower = code.lower()

    # Check for schema field coverage.
    fields_found = sum(1 for f in _SCHEMA_FIELDS if f in lower)
    details["schema_fields_found"] = fields_found
    score += min(0.3, 0.05 * fields_found)

    # Check for protocol-related keywords.
    proto_hits = sum(1 for kw in _PROTOCOL_KW if kw in lower)
    details["protocol_keywords"] = proto_hits
    score += min(0.15, 0.03 * proto_hits)

    # Reward structured output.
    json_braces = len(re.findall(r"[\{\[\"]", code))
    details["structured_tokens"] = json_braces
    if json_braces > 5:
        score += 0.1

    # Reward endpoint/path patterns.
    endpoint_patterns = len(re.findall(r"(?:/api/|/v\d+/|https?://)", code))
    details["endpoint_patterns"] = endpoint_patterns
    score += min(0.1, 0.05 * endpoint_patterns)

    # Penalize placeholder values.
    placeholders = len(re.findall(r"(TODO|FIXME|REPLACE|PLACEHOLDER|xxx+)", code, re.IGNORECASE))
    details["placeholder_count"] = placeholders
    if placeholders > 0:
        score -= 0.1

    # Check against expected fields from sample metadata.
    expected = (sample.metadata or {}).get("expected_fields", [])
    if expected:
        found = sum(1 for f in expected if f.lower() in lower)
        details["expected_field_coverage"] = found / len(expected)
        score += 0.1 * (found / len(expected))

    return max(0.0, min(1.0, score)), details


class WasmSourceMapChallenge(BaseChallenge):
    """Three-round WASM/SourceMap/API protocol recovery routine.

    R1 — present compiled/obfuscated data, ask for protocol recovery.
    R2 — provide feedback from round 1 failures, ask to fix.
    R3 — ask for clean, documented final schema.
    """

    code = "D04.wasm_sourcemap.recover"
    rounds = 3
    early_terminate_on_pass = False
    allow_retry = True

    PASS_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.4

    def build_prompt(
        self,
        sample: SampleVariant,
        round_no: int,
        prior: list[dict],
    ) -> str:
        template_name = f"round{round_no}.j2"
        template = _ENV.get_template(template_name)
        ctx = {
            "sample": sample,
            "prior": prior,
            "obfuscated_code_inline": (
                prior[-1]["obfuscated_code"] if prior else "{{OBFUSCATED_CODE}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        match = _FENCED_BLOCK.search(response)
        code = match.group(1) if match else response.strip()
        return {
            "ok": bool(code),
            "round_no": round_no,
            "payload": code,
        }

    def objective_check(
        self,
        parsed: dict,
        sample: SampleVariant,
    ) -> ChallengeResult:
        if not parsed["ok"] or not parsed["payload"]:
            return ChallengeResult(
                grade=MetricGrade.FAIL,
                score=0.0,
                rationale="Empty or unparseable response.",
            )

        code = parsed["payload"]
        score, details = _heuristic_score(code, sample)

        if score >= self.PASS_THRESHOLD:
            grade = MetricGrade.PASS
        elif score >= self.PARTIAL_THRESHOLD:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL

        return ChallengeResult(
            grade=grade,
            score=score,
            details=details,
            rationale=(
                f"Heuristic protocol recovery score={score:.3f}. "
                f"Found {details.get('schema_fields_found', 0)} schema fields, "
                f"{details.get('protocol_keywords', 0)} protocol keywords."
            ),
        )
