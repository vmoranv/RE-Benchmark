"""D12 — Protocol Pattern Inference & State Machine Reconstruction challenge."""

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

_FENCED = re.compile(r"```.*?\n(.*?)\n```", re.DOTALL)

_KEY_PATTERNS = [
    "protocol",
    "field",
    "state machine",
    "state transition",
    "header",
    "payload",
    "opcode",
    "message type",
    "length field",
    "magic bytes",
    "delimiter",
    "schema",
    "finite state",
    "fsm",
    "transition table",
    "field boundary",
    "field extraction",
    "wireshark",
    "pcap",
    "dissector",
    "protobuf",
    "msgpack",
    "json",
    "binary protocol",
    "network trace",
    "packet",
    "sequence diagram",
    "state diagram",
]


def _score_keyword_hits(code: str) -> tuple[float, dict]:
    """Check keyword hits for protocol inference patterns."""
    score = 0.0
    details: dict[str, float | list[str]] = {}
    lower = code.lower()

    hits = [p for p in _KEY_PATTERNS if p in lower]
    details["keyword_hits"] = hits
    details["keyword_hit_count"] = len(hits)
    score += min(0.3, 0.03 * len(hits))

    return score, details


def _score_structure_patterns(code: str) -> tuple[float, dict]:
    """Check field definitions, state definitions, and schema indicators."""
    score = 0.0
    details: dict[str, float | list[str]] = {}
    lower = code.lower()

    field_defs = re.findall(r"field\s*[:=]\s*\w+", lower)
    details["field_definitions"] = len(field_defs)
    if field_defs:
        score += 0.1

    state_defs = re.findall(r"(state\s+\w+|transition\s*[:=]|->\s*\w+)", code)
    details["state_definitions"] = len(state_defs)
    if state_defs:
        score += 0.1

    schema_indicators = re.findall(r"(schema|protobuf|\.proto|json_schema|typedef|struct)", lower)
    details["schema_indicators"] = len(schema_indicators)
    if schema_indicators:
        score += 0.1

    if re.search(r"state\s+(machine|diagram|transition)", lower):
        score += 0.1

    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float | list[str]] = {}

    kw_score, kw_details = _score_keyword_hits(code)
    score += kw_score
    details.update(kw_details)

    struct_score, struct_details = _score_structure_patterns(code)
    score += struct_score
    details.update(struct_details)

    return max(0.0, min(1.0, score)), details


class ProtocolInferenceChallenge(BaseChallenge):
    code = "D12.protocol_inference"
    rounds = 3
    early_terminate_on_pass = False
    allow_retry = True

    PASS_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.4

    def build_prompt(self, sample: SampleVariant, round_no: int, prior: list[dict]) -> str:
        template = _ENV.get_template(f"round{round_no}.j2")
        ctx = {
            "sample": sample,
            "prior": prior,
            "obfuscated_code_inline": (
                prior[-1].get("obfuscated_code", "{{TARGET_DATA}}") if prior else "{{TARGET_DATA}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        match = _FENCED.search(response)
        code = match.group(1) if match else response.strip()
        return {
            "ok": bool(code),
            "round_no": round_no,
            "payload": code,
        }

    def objective_check(self, parsed: dict, sample: SampleVariant) -> ChallengeResult:
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
            rationale=f"Heuristic analysis: score={score:.3f}, keywords matched={details.get('keyword_hit_count', 0)}.",
        )
