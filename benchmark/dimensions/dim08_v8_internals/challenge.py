"""D8 Challenge — Analyze V8 heap snapshots, extract bytecode, check JIT state, traverse object graph."""

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

_HEAP_SNAPSHOT_KEYWORDS = (
    "HeapSnapshot",
    "heapSnapshot",
    "nodes",
    "edges",
    "node_count",
    "edge_count",
    "meta",
)

_BYTECODE_KEYWORDS = (
    "bytecode",
    "BytecodeArray",
    "Ignition",
    "bytecodeArray",
    "handler",
    "register",
    "accumulator",
    "operand",
)

_JIT_KEYWORDS = (
    "Turbofan",
    "Maglev",
    "Sparkplug",
    "optimized",
    "deopt",
    "DeoptimizationData",
    "code",
    "Code",
    "shared_info",
    "SharedFunctionInfo",
)

_OBJECT_GRAPH_KEYWORDS = (
    "__proto__",
    "prototype",
    "constructor",
    "properties",
    "internalFields",
    "map",
    "Map",
    "elements",
    "WeakRef",
    "FinalizationRegistry",
)


def _score_keyword_group(
    code: str,
    keywords: tuple[str, ...],
    label: str,
    thresholds: list[tuple[int, float]],
) -> tuple[float, dict]:
    """Score a keyword group based on hit count and tiered thresholds."""
    hits = sum(1 for kw in keywords if kw in code)
    score = sum(bonus for min_hits, bonus in thresholds if hits >= min_hits)
    return score, {label: hits}


def _score_v8_patterns(code: str) -> tuple[float, dict]:
    """Check V8-specific patterns (traversal, JSON, native calls)."""
    score = 0.0
    details: dict[str, object] = {}

    lower = code.lower()
    if "node" in lower and "edge" in lower:
        score += 0.05
        details["traversal_pattern"] = True

    if re.search(r"JSON\.(stringify|parse)", code):
        score += 0.05
        details["json_output"] = True

    v8_native = ("%DebugPrint", "%GetOptimizationStatus", "%GetBytecode")
    if any(call in code for call in v8_native):
        score += 0.05
        details["v8_native_calls"] = True

    return score, details


def _score_operations(code: str, sample: SampleVariant) -> tuple[float, dict]:
    """Check coverage of sample-required operations."""
    score = 0.0
    details: dict[str, object] = {}

    metadata = sample.metadata or {}
    expected_ops = metadata.get("required_operations", [])
    if expected_ops:
        matched = sum(1 for op in expected_ops if op.lower() in code.lower())
        ratio = matched / max(1, len(expected_ops))
        details["operation_coverage"] = ratio
        score += ratio * 0.1

    return score, details


def _heuristic_score(code: str, sample: SampleVariant) -> tuple[float, dict]:
    score = 0.2
    details: dict[str, object] = {}

    heap_score, heap_details = _score_keyword_group(
        code,
        _HEAP_SNAPSHOT_KEYWORDS,
        "heap_snapshot_keywords",
        [(2, 0.15), (4, 0.1)],
    )
    score += heap_score
    details.update(heap_details)

    bc_score, bc_details = _score_keyword_group(
        code,
        _BYTECODE_KEYWORDS,
        "bytecode_keywords",
        [(2, 0.15), (4, 0.1)],
    )
    score += bc_score
    details.update(bc_details)

    jit_score, jit_details = _score_keyword_group(
        code,
        _JIT_KEYWORDS,
        "jit_keywords",
        [(1, 0.1), (3, 0.05)],
    )
    score += jit_score
    details.update(jit_details)

    og_score, og_details = _score_keyword_group(
        code,
        _OBJECT_GRAPH_KEYWORDS,
        "object_graph_keywords",
        [(2, 0.1), (4, 0.05)],
    )
    score += og_score
    details.update(og_details)

    pattern_score, pattern_details = _score_v8_patterns(code)
    score += pattern_score
    details.update(pattern_details)

    ops_score, ops_details = _score_operations(code, sample)
    score += ops_score
    details.update(ops_details)

    return max(0.0, min(1.0, score)), details


class V8InternalsChallenge(BaseChallenge):
    """Three-round V8 internal state inspection prompt routine.

    R1 -- present heap snapshot / V8 trace, ask for analysis.
    R2 -- provide failure details, ask to fix.
    R3 -- ask for clean, production-ready final analysis script.
    """

    code = "D08.v8_internals"
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
                prior[-1]["obfuscated_code"] if prior else "{{V8_TRACE_DATA}}"
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
                f"Heuristic V8 internals score={score:.3f}. "
                f"Heap: {details.get('heap_snapshot_keywords', 0)}, "
                f"Bytecode: {details.get('bytecode_keywords', 0)}, "
                f"JIT: {details.get('jit_keywords', 0)}."
            ),
        )
