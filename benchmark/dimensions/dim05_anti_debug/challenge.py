"""D5 Anti-Debug challenge — detect and bypass debugger traps and DevTools detection."""

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

# Anti-debug techniques to detect in the protected code.
_ANTI_DEBUG_PATTERNS = {
    "debugger_statement": re.compile(r"\bdebugger\b"),
    "devtools_detector": re.compile(
        r"(devtools|DevTools|dev\s*tools|inspect|isOpen|isOpened)",
        re.IGNORECASE,
    ),
    "timing_check": re.compile(
        r"(performance\.now|Date\.now|console\.time|new Date\b)",
    ),
    "console_trap": re.compile(
        r"(console\.(log|clear|debug|table|dir)|console\[\s*['\"])",
    ),
    "interval_check": re.compile(r"(setInterval|setTimeout)\s*\("),
    "window_size_check": re.compile(
        r"(window\.(outerWidth|outerHeight|innerWidth|innerHeight))",
    ),
    "stack_trace": re.compile(r"(Error\(\)|\.stack|stackTrace|printStackTrace)"),
    "function_toString": re.compile(r"\.toString\s*\(\s*\)"),
}

# Patterns indicating correct bypass techniques.
_BYPASS_PATTERNS = {
    "debugger_removal": re.compile(
        r"(\/\/\s*debugger|\/\*.*?debugger.*?\*\/|\bdebugger\s*;?\s*\/\/)", re.DOTALL
    ),
    "timing_neutralize": re.compile(
        r"(performance\.now\s*=\s*|Date\.now\s*=\s*|override.*timing|mock.*now)",
        re.IGNORECASE,
    ),
    "devtools_patch": re.compile(
        r"(delete\s+window\.devtools|devtools\s*=\s*undefined|Object\.defineProperty.*devtools)",
        re.IGNORECASE,
    ),
    "console_redefine": re.compile(
        r"(console\s*=\s*\{|window\.console\s*=|console\.\w+\s*=\s*function)",
    ),
    "interval_clear": re.compile(r"clear(Interval|Timeout)\s*\("),
    "hook_detection": re.compile(
        r"(isHooked|isPatched|native\s+code|toString.*native)",
        re.IGNORECASE,
    ),
}


def _map_check_name(n: str) -> str:
    """Normalise an anti-debug check name to its bypass counterpart."""
    return (
        n.replace("_check", "")
        .replace("statement", "_removal")
        .replace("trap", "_redefine")
        .replace("detector", "_patch")
        .replace("interval", "_clear")
    )


def _detect_traps(input_code: str) -> dict[str, bool]:
    """Find anti-debug techniques in the protected code."""
    return {name: True for name, pat in _ANTI_DEBUG_PATTERNS.items() if pat.search(input_code)}


def _score_bypass(code: str, detected_checks: dict[str, bool]) -> tuple[float, dict[str, object]]:
    """Score bypass coverage and build M1-compatible check list."""
    score = 0.3
    details: dict[str, object] = {}

    bypassed = 0
    bypass_details: dict[str, bool] = {}
    for name, pattern in _BYPASS_PATTERNS.items():
        found = bool(pattern.search(code))
        bypass_details[name] = found
        if found:
            bypassed += 1
    details["bypass_techniques"] = bypassed
    score += min(0.4, 0.1 * bypassed)

    # Reward legible code.
    legible_kw = sum(1 for kw in ("function ", "const ", "let ", "return ") if kw in code)
    details["legible_keywords"] = legible_kw
    score += min(0.15, 0.03 * legible_kw)

    # Reward explanatory comments.
    comments = len(
        re.findall(r"//.*bypass|//.*patch|//.*override|//.*neutralize", code, re.IGNORECASE)
    )
    details["explanatory_comments"] = comments
    score += min(0.1, 0.05 * comments)

    # Penalize remaining traps.
    remaining_traps = sum(1 for pat in _ANTI_DEBUG_PATTERNS.values() if pat.search(code))
    details["remaining_traps"] = remaining_traps
    if remaining_traps > 0:
        score -= 0.05 * remaining_traps

    # Build per-check bypass status for M1 metric.
    details["detected_checks"] = len(detected_checks)
    details["anti_debug_checks"] = [
        {"name": name, "bypassed": bypass_details.get(_map_check_name(name), False)}
        for name in detected_checks
    ]
    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    input_code = (sample.metadata or {}).get("protected_code", "")
    if not input_code:
        input_code = code
    detected = _detect_traps(input_code)
    partial, details = _score_bypass(code, detected)
    return max(0.0, min(1.0, partial)), details


class AntiDebugChallenge(BaseChallenge):
    """Three-round anti-debug bypass routine.

    R1 — present protected code, ask to identify and bypass traps.
    R2 — provide feedback from round 1 failures, ask to fix.
    R3 — ask for clean, production-ready bypass code.
    """

    code = "D05.anti_debug.bypass"
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
                f"Heuristic anti-debug bypass score={score:.3f}. "
                f"Detected {details.get('detected_checks', 0)} traps, "
                f"applied {details.get('bypass_techniques', 0)} bypass techniques, "
                f"{details.get('remaining_traps', 0)} traps remain."
            ),
        )
