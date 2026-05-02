"""D16 — HTTP Proxy & Traffic Interception challenge."""

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

_FENCED_BLOCK = re.compile(
    r"```(?:bash|shell|python|javascript|json|text|conf|nginx)?\n(.*?)\n```", re.DOTALL
)


def _heuristic_score(text: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.3
    details: dict[str, float] = {}

    proxy_keywords = ["proxy", "mitmproxy", "charles", "burp", "intercept", "forward"]
    cert_keywords = ["certificate", "ca cert", "ssl", "tls", "pem", "trust"]
    rule_keywords = ["rule", "filter", "rewrite", "redirect", "block", "allow"]
    adb_keywords = ["adb", "device", "android", "emulator", "proxy-set"]

    proxy_hits = sum(1 for kw in proxy_keywords if kw in text.lower())
    cert_hits = sum(1 for kw in cert_keywords if kw in text.lower())
    rule_hits = sum(1 for kw in rule_keywords if kw in text.lower())
    adb_hits = sum(1 for kw in adb_keywords if kw in text.lower())

    details["proxy_keyword_hits"] = proxy_hits
    details["cert_keyword_hits"] = cert_hits
    details["rule_keyword_hits"] = rule_hits
    details["adb_keyword_hits"] = adb_hits

    score += min(0.15, 0.03 * proxy_hits)
    score += min(0.15, 0.03 * cert_hits)
    score += min(0.15, 0.03 * rule_hits)
    score += min(0.15, 0.03 * adb_hits)

    has_ip_port = bool(re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d+", text))
    has_cert_export = "export" in text.lower() or "save" in text.lower()
    has_adb_cmd = bool(re.search(r"adb\s+", text))

    details["has_ip_port"] = float(has_ip_port)
    details["has_cert_export"] = float(has_cert_export)
    details["has_adb_command"] = float(has_adb_cmd)

    if has_ip_port:
        score += 0.05
    if has_cert_export:
        score += 0.05
    if has_adb_cmd:
        score += 0.05

    return max(0.0, min(1.0, score)), details


class HttpProxyChallenge(BaseChallenge):
    """Three-round HTTP proxy setup and traffic interception challenge.

    R1 — Present target app scenario, ask for proxy setup + interception rules.
    R2 — Provide feedback on missing pieces, ask to fix.
    R3 — Ask for complete final configuration with ADB device proxy setup.
    """

    code = "D16.http_proxy"
    rounds = 3
    early_terminate_on_pass = False
    allow_retry = True

    PASS_THRESHOLD = 0.75
    PARTIAL_THRESHOLD = 0.40

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
                prior[-1]["obfuscated_code"] if prior else "{{TARGET_SCENARIO}}"
            ),
        }
        return template.render(**ctx)

    def parse_response(self, response: str, round_no: int) -> dict:
        match = _FENCED_BLOCK.search(response)
        payload = match.group(1) if match else response.strip()
        return {
            "ok": bool(payload),
            "round_no": round_no,
            "payload": payload,
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

        text = parsed["payload"]
        expected_elements = list((sample.metadata or {}).get("expected_proxy_elements", []))

        if expected_elements:
            matched = sum(1 for el in expected_elements if el.lower() in text.lower())
            ratio = matched / max(1, len(expected_elements))
            if ratio >= self.PASS_THRESHOLD:
                grade = MetricGrade.PASS
            elif ratio >= self.PARTIAL_THRESHOLD:
                grade = MetricGrade.PARTIAL
            else:
                grade = MetricGrade.FAIL
            return ChallengeResult(
                grade=grade,
                score=ratio,
                details={
                    "expected_elements": len(expected_elements),
                    "matched_elements": matched,
                },
                rationale=(
                    f"Matched {matched}/{len(expected_elements)} expected proxy "
                    f"configuration elements (ratio={ratio:.3f})."
                ),
            )

        score, details = _heuristic_score(text, sample)
        if score >= 0.70:
            grade = MetricGrade.PASS
        elif score >= self.PARTIAL_THRESHOLD:
            grade = MetricGrade.PARTIAL
        else:
            grade = MetricGrade.FAIL
        return ChallengeResult(
            grade=grade,
            score=score,
            details=details,
            rationale="Heuristic fallback used; no expected_proxy_elements in sample metadata.",
        )
