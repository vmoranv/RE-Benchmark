"""D9 Challenge — Generate Frida scripts for dynamic instrumentation of native binaries."""

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

_FENCED_JS = re.compile(r"```(?:js|javascript)?\n(.*?)\n```", re.DOTALL)

_FRIDA_API_PATTERNS = {
    "Interceptor.attach": re.compile(r"Interceptor\.attach\s*\(", re.DOTALL),
    "Interceptor.replace": re.compile(r"Interceptor\.replace\s*\(", re.DOTALL),
    "Module.findExportByName": re.compile(r"Module\.findExportByName\s*\(", re.DOTALL),
    "Module.getExportByName": re.compile(r"Module\.getExportByName\s*\(", re.DOTALL),
    "Module.findBaseAddress": re.compile(r"Module\.findBaseAddress\s*\(", re.DOTALL),
    "NativeFunction": re.compile(r"new\s+NativeFunction\s*\(", re.DOTALL),
    "NativeCallback": re.compile(r"new\s+NativeCallback\s*\(", re.DOTALL),
    "Memory.readUtf8String": re.compile(r"Memory\.readUtf8String\s*\(", re.DOTALL),
    "Memory.readByteArray": re.compile(r"Memory\.readByteArray\s*\(", re.DOTALL),
    "Memory.writeByteArray": re.compile(r"Memory\.writeByteArray\s*\(", re.DOTALL),
    "ptr": re.compile(r"ptr\s*\(\s*['\"]", re.DOTALL),
    "onEnter": re.compile(r"onEnter\s*[:=]\s*function", re.DOTALL),
    "onLeave": re.compile(r"onLeave\s*[:=]\s*function", re.DOTALL),
    "Thread.backtrace": re.compile(r"Thread\.backtrace\s*\(", re.DOTALL),
    "Process.findModuleByName": re.compile(r"Process\.findModuleByName\s*\(", re.DOTALL),
    "Script.nextTick": re.compile(r"Script\.nextTick\s*\(", re.DOTALL),
}


def _score_frida_apis(code: str) -> tuple[float, dict[str, object], dict[str, bool]]:
    """Check Frida API pattern matches and return partial score + details + hits."""
    score = 0.0
    details: dict[str, object] = {}
    api_hits: dict[str, bool] = {}

    for api_name, pattern in _FRIDA_API_PATTERNS.items():
        if pattern.search(code):
            api_hits[api_name] = True
            score += 0.05

    details["frida_apis_used"] = list(api_hits.keys())
    return score, details, api_hits


def _score_interceptor_patterns(code: str, api_hits: dict[str, bool]) -> tuple[float, dict]:
    """Score Interceptor hook patterns (onEnter/onLeave, exports)."""
    score = 0.0
    details: dict[str, object] = {}

    if "Interceptor.attach" in api_hits:
        if "onEnter" in api_hits:
            score += 0.05
            details["has_on_enter"] = True
        if "onLeave" in api_hits:
            score += 0.05
            details["has_on_leave"] = True

    if "Module.findExportByName" in api_hits or "Module.getExportByName" in api_hits:
        score += 0.05
        details["resolves_exports"] = True

    return score, details


def _score_advanced_patterns(code: str, api_hits: dict[str, bool]) -> tuple[float, dict]:
    """Score advanced Frida patterns (NativeFunction, backtrace, args, retval)."""
    score = 0.0
    details: dict[str, object] = {}

    if "NativeFunction" in api_hits:
        score += 0.05
        details["native_call_setup"] = True

    if "NativeCallback" in api_hits:
        score += 0.05
        details["callback_injection"] = True

    if "Thread.backtrace" in api_hits:
        score += 0.05
        details["backtrace_capture"] = True

    if re.search(r"args\[\d+\]", code):
        score += 0.05
        details["reads_args"] = True

    if re.search(r"retval\.", code) or re.search(r"this\.context\.", code):
        score += 0.05
        details["reads_return"] = True

    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.2
    details: dict[str, object] = {}

    api_score, api_details, api_hits = _score_frida_apis(code)
    score += api_score
    details.update(api_details)

    interp_score, interp_details = _score_interceptor_patterns(code, api_hits)
    score += interp_score
    details.update(interp_details)

    adv_score, adv_details = _score_advanced_patterns(code, api_hits)
    score += adv_score
    details.update(adv_details)

    metadata = sample.metadata or {}
    target_functions = metadata.get("target_functions", [])
    if target_functions:
        matched = sum(1 for fn in target_functions if fn in code)
        ratio = matched / max(1, len(target_functions))
        details["target_coverage"] = ratio
        score += ratio * 0.15

    return max(0.0, min(1.0, score)), details


class NativeBinaryChallenge(BaseChallenge):
    """Three-round native binary instrumentation prompt routine.

    R1 -- present binary analysis target, ask for Frida instrumentation script.
    R2 -- provide failure details, ask to fix.
    R3 -- ask for clean, production-ready final Frida script.
    """

    code = "D09.native_binary"
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
                prior[-1]["obfuscated_code"] if prior else "{{NATIVE_TARGET_INFO}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        match = _FENCED_JS.search(response)
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
                f"Heuristic Frida instrumentation score={score:.3f}. "
                f"Frida APIs used: {details.get('frida_apis_used', [])}."
            ),
        )
