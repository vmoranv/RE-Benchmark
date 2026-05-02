"""D7 Challenge — Identify game engine from Canvas/WebGL fingerprint, dump scene tree, trace click handlers."""

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

_ENGINE_NAMES = (
    "Laya",
    "Pixi",
    "Phaser",
    "Cocos",
    "Unity",
    "Egret",
    "CreateJS",
    "Three.js",
    "Babylon",
    "PlayCanvas",
)

_SCENE_TREE_KEYWORDS = (
    "scene",
    "stage",
    "root",
    "children",
    "parent",
    "displayList",
    "node",
    "transform",
    "addChild",
)

_HANDLER_KEYWORDS = (
    "addEventListener",
    "onClick",
    "onTap",
    "onPointerDown",
    "hitTest",
    "interactive",
    "input",
    "pointerEvents",
)


def _score_engine_id(code: str) -> tuple[float, dict]:
    """Check engine identification patterns."""
    score = 0.0
    details: dict[str, object] = {}
    lower = code.lower()

    engine_hits = [e for e in _ENGINE_NAMES if e.lower() in lower]
    details["engines_identified"] = engine_hits
    if engine_hits:
        score += 0.2
    if len(engine_hits) >= 2:
        score += 0.05

    if "getContext" in code or "webgl" in lower:
        score += 0.05
        details["webgl_access"] = True
    if "getParameter" in code or "gl.getParameter" in code:
        score += 0.05
        details["gl_params_read"] = True

    return score, details


def _score_scene_and_handlers(code: str) -> tuple[float, dict]:
    """Check scene-tree and handler patterns."""
    score = 0.0
    details: dict[str, object] = {}

    scene_hits = sum(1 for kw in _SCENE_TREE_KEYWORDS if kw in code)
    details["scene_tree_keywords"] = scene_hits
    if scene_hits >= 3:
        score += 0.15
    if scene_hits >= 5:
        score += 0.1

    handler_hits = sum(1 for kw in _HANDLER_KEYWORDS if kw in code)
    details["handler_keywords"] = handler_hits
    if handler_hits >= 2:
        score += 0.1
    if handler_hits >= 4:
        score += 0.05

    return score, details


def _score_output_quality(code: str) -> tuple[float, dict]:
    """Check JSON output and output quality patterns."""
    score = 0.0
    details: dict[str, object] = {}

    if "JSON" in code and ("stringify" in code or "parse" in code):
        score += 0.05
        details["json_output"] = True

    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.2
    details: dict[str, object] = {}

    engine_score, engine_details = _score_engine_id(code)
    score += engine_score
    details.update(engine_details)

    scene_score, scene_details = _score_scene_and_handlers(code)
    score += scene_score
    details.update(scene_details)

    output_score, output_details = _score_output_quality(code)
    score += output_score
    details.update(output_details)

    metadata = sample.metadata or {}
    expected_engine = metadata.get("engine")
    if expected_engine and expected_engine.lower() in code.lower():
        score += 0.1
        details["correct_engine"] = True

    return max(0.0, min(1.0, score)), details


class CanvasWebGLChallenge(BaseChallenge):
    """Three-round Canvas/WebGL reverse-engineering prompt routine.

    R1 -- present Canvas/WebGL trace, ask for engine identification and analysis.
    R2 -- provide failure details, ask to fix.
    R3 -- ask for clean, production-ready final analysis script.
    """

    code = "D07.canvas_webgl_re"
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
                prior[-1]["obfuscated_code"] if prior else "{{CANVAS_WEBGL_TRACE}}"
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
                f"Heuristic Canvas/WebGL RE score={score:.3f}. "
                f"Engines identified: {details.get('engines_identified', [])}."
            ),
        )
