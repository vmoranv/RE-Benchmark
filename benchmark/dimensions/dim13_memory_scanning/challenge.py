"""D13 — Memory Scanning & Structure Analysis challenge."""

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
    "scan",
    "value scan",
    "pointer",
    "pointer chain",
    "vtable",
    "vtable pointer",
    "struct",
    "struct inference",
    "memory scan",
    "cheat engine",
    "readprocessmemory",
    "writeprocessmemory",
    "virtualquery",
    "base address",
    "offset",
    "dereference",
    "heap",
    "stack",
    ".data section",
    ".rdata section",
    "rtti",
    "type_info",
    "class hierarchy",
    "memory region",
    "scan strategy",
    "first scan",
    "next scan",
    "exact value",
    "unknown initial value",
    "changed value",
    "unchanged value",
]


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float | list[str]] = {}
    lower = code.lower()

    hits = [p for p in _KEY_PATTERNS if p in lower]
    details["keyword_hits"] = hits
    details["keyword_hit_count"] = len(hits)
    score += min(0.3, 0.035 * len(hits))

    ptr_patterns = re.findall(r"(0x[0-9a-fA-F]{4,}|pointer\s*->|->\s*\w+|\[[\d+]\]+)", code)
    details["pointer_expressions"] = len(ptr_patterns)
    if ptr_patterns:
        score += 0.1

    struct_defs = re.findall(r"struct\s+\w+", code)
    details["struct_definitions"] = len(struct_defs)
    if struct_defs:
        score += 0.1

    scan_refs = re.findall(r"(first scan|next scan|exact value|changed|unchanged)", lower)
    details["scan_strategy_refs"] = len(scan_refs)
    if scan_refs:
        score += 0.1

    return max(0.0, min(1.0, score)), details


class MemoryScanningChallenge(BaseChallenge):
    code = "D13.memory_scanning"
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
