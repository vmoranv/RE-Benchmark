"""D11 — Syscall Monitoring & JS Correlation challenge."""

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
    "strace",
    "etw",
    "syscall",
    "ptrace",
    "perf_event",
    "bpf",
    "eBPF",
    "dtrace",
    "ltrace",
    "ftrace",
    "sys_enter",
    "sys_exit",
    "javascript",
    "js function",
    "v8",
    "correlation",
    "mapping",
    "syscall_to_js",
    "js_to_syscall",
    "call stack",
    "backtrace",
    "stack trace",
    "syscall table",
]


def _score_keyword_hits(code: str) -> tuple[float, dict]:
    """Check keyword hits for syscall monitoring patterns."""
    score = 0.0
    details: dict[str, float | list[str]] = {}
    lower = code.lower()

    hits = [p for p in _KEY_PATTERNS if p.lower() in lower]
    details["keyword_hits"] = hits
    details["keyword_hit_count"] = len(hits)
    score += min(0.35, 0.04 * len(hits))

    return score, details


def _score_correlation_patterns(code: str) -> tuple[float, dict]:
    """Check syscall-to-JS correlation and tracing tool patterns."""
    score = 0.0
    details: dict[str, float | list[str]] = {}
    lower = code.lower()

    syscall_map = re.findall(r"syscall\s*[:=]\s*\w+", lower)
    details["syscall_mappings"] = len(syscall_map)
    if syscall_map:
        score += 0.1

    js_refs = re.findall(r"(js_function|javascript.*call|v8::|function\s+\w+)", code)
    details["js_references"] = len(js_refs)
    if js_refs:
        score += 0.1

    trace_patterns = re.findall(r"(strace\s+-|etw.*enable|perf record|bpf_trace)", code)
    details["trace_tool_usage"] = len(trace_patterns)
    if trace_patterns:
        score += 0.1

    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float | list[str]] = {}

    kw_score, kw_details = _score_keyword_hits(code)
    score += kw_score
    details.update(kw_details)

    corr_score, corr_details = _score_correlation_patterns(code)
    score += corr_score
    details.update(corr_details)

    return max(0.0, min(1.0, score)), details


class SyscallMonitorChallenge(BaseChallenge):
    code = "D11.syscall_monitor"
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
