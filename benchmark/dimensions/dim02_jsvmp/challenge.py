"""D2 JSVMP challenge — recover original logic from VM-protected code."""

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

# Patterns that indicate successful VM unpacking.
_FUNC_SIG = re.compile(r"function\s+\w+\s*\(")
_OPCODE_HANDLER = re.compile(r"(case\s+0x[0-9a-f]+|opcodes?\[|dispatch\()", re.IGNORECASE)
_VM_DISPATCH = re.compile(r"(while\s*\(true\)|switch\s*\(_0x|\.call\()", re.IGNORECASE)
_LEGIBLE_KW = ("function ", "const ", "let ", "return ", "if ", "else ")


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.4
    details: dict[str, float] = {}

    # Penalize remaining VM boilerplate.
    vm_hits = len(_VM_DISPATCH.findall(code))
    details["vm_dispatch_remnants"] = vm_hits
    if vm_hits > 3:
        score -= 0.15

    # Reward recognized opcode handling patterns.
    opcode_hits = len(_OPCODE_HANDLER.findall(code))
    details["opcode_handler_hits"] = opcode_hits
    if opcode_hits >= 2:
        score += 0.15

    # Reward function signature recovery.
    func_sigs = len(_FUNC_SIG.findall(code))
    details["function_signatures"] = func_sigs
    score += min(0.2, 0.04 * func_sigs)

    # Reward legible JS constructs.
    legible = sum(1 for kw in _LEGIBLE_KW if kw in code)
    details["legible_keywords"] = legible
    score += min(0.2, 0.04 * legible)

    # Penalize hex identifiers.
    hex_ids = len(re.findall(r"\b_0x[0-9a-f]{4,}\b", code, re.IGNORECASE))
    details["hex_identifier_count"] = hex_ids
    if hex_ids > 5:
        score -= 0.1

    return max(0.0, min(1.0, score)), details


class JSVMPChallenge(BaseChallenge):
    """Three-round JSVMP unpacking routine.

    R1 — present VM-protected code, ask for logic recovery.
    R2 — provide failure feedback, ask to fix.
    R3 — ask for clean, human-readable final version.
    """

    code = "D02.jsvmp.unpack"
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
                f"Heuristic VM-unpacking score={score:.3f}. "
                f"Recovered {details.get('function_signatures', 0)} function signatures, "
                f"{details.get('opcode_handler_hits', 0)} opcode handlers."
            ),
        )
