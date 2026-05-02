"""D17 / D18 — Obfuscator Correctness + LLM Semantic Probing. Placeholder."""

from typing import ClassVar

from benchmark.dimensions._placeholder import PlaceholderDimension


class CorrectnessAndProbeDimension(PlaceholderDimension):
    code = "D17"
    name = "Obfuscator Correctness + LLM Semantic Probing"
    paper_refs: ClassVar[list[str]] = ["OBsmith", "The Code Barrier"]
