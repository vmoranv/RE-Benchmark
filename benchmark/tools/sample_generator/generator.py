"""Sample generator — creates obfuscated samples from clean JS using real tools."""

from __future__ import annotations

import uuid
from pathlib import Path

import yaml

from benchmark.tools.sample_generator.obfuscators import (
    encode_base64_strings,
    js_confuser_obfuscate,
    js_obfuscator,
    wrap_anti_debug,
)

_SEED_DIR = Path(__file__).resolve().parents[3] / "benchmark" / "samples" / "seed_samples"

# Dimension-specific generator configs
_DIMENSION_CONFIGS: dict[str, dict] = {
    "D01": {
        "obfuscator": "javascript-obfuscator",
        "levels": {1: 1, 2: 2, 3: 3, 4: 4},
        "description": "Deobfuscation of {level} obfuscated JavaScript.",
    },
    "D02": {
        "obfuscator": "jsvmp",  # Will use js-obfuscator max level as approximation
        "levels": {5: 4},
        "description": "JSVMP bytecode unpacking.",
    },
    "D05": {
        "obfuscator": "anti-debug",
        "levels": {3: 3},
        "description": "Anti-debug bypass challenge at level {level}.",
        "wrapper": wrap_anti_debug,
    },
    "D06": {
        "obfuscator": "javascript-obfuscator",
        "levels": {2: 2},
        "description": "Hook injection target code.",
    },
    "D07": {
        "obfuscator": "javascript-obfuscator",
        "levels": {2: 2},
        "description": "Canvas/WebGL fingerprint code.",
    },
    "D17": {
        "obfuscator": "multi",
        "levels": {3: 3},
        "description": "Obfuscator correctness verification.",
    },
}


def generate_sample(
    dimension: str,
    original_code: str,
    sample_name: str = "generated_001",
    obfuscation_level: int = 2,
    semantic_test_cases: list[dict] | None = None,
    description: str = "",
) -> Path:
    """Generate a sample for a given dimension."""
    out_dir = _SEED_DIR / dimension / sample_name
    out_dir.mkdir(parents=True, exist_ok=True)

    config = _DIMENSION_CONFIGS.get(dimension, _DIMENSION_CONFIGS["D01"])
    tool_level = config["levels"].get(obfuscation_level, obfuscation_level)

    # Generate obfuscated code
    obfuscator_name = config["obfuscator"]
    if obfuscator_name == "javascript-obfuscator":
        obfuscated = js_obfuscator(original_code, level=tool_level)
    elif obfuscator_name == "js-confuser":
        obfuscated = js_confuser_obfuscate(original_code, level=tool_level)
    elif obfuscator_name == "anti-debug":
        # First obfuscate, then wrap
        obfuscated = js_obfuscator(original_code, level=tool_level)
        wrapper = config.get("wrapper")
        if wrapper:
            obfuscated = wrapper(obfuscated)
    elif obfuscator_name == "multi":
        # Use multiple obfuscators for D17
        obfuscated = js_obfuscator(original_code, level=tool_level)
    elif obfuscator_name == "jsvmp":
        obfuscated = js_confuser_obfuscate(original_code, level=4)
    else:
        obfuscated = encode_base64_strings(original_code)

    # Write files
    (out_dir / "original.js").write_text(original_code, encoding="utf-8")
    (out_dir / "obfuscated.js").write_text(obfuscated, encoding="utf-8")

    manifest = {
        "id": sample_name,
        "dimension_code": dimension,
        "obfuscation_level": f"L{obfuscation_level}",
        "obfuscator": obfuscator_name,
        "description": description or config["description"].format(level=obfuscation_level),
    }
    if semantic_test_cases:
        manifest["semantic_test_cases"] = semantic_test_cases

    (out_dir / "manifest.yaml").write_text(
        yaml.dump(manifest, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )
    return out_dir


def batch_generate(
    dimensions: list[str] | None = None,
    levels: list[int] | None = None,
) -> list[Path]:
    """Generate samples for multiple dimensions and levels."""
    results: list[Path] = []
    target_dims = dimensions or list(_DIMENSION_CONFIGS.keys())
    target_levels = levels or [2]

    for dim in target_dims:
        config = _DIMENSION_CONFIGS.get(dim)
        if not config:
            continue
        for level in target_levels:
            if level not in config["levels"]:
                continue
            sample_name = f"auto_L{level}_{uuid.uuid4().hex[:6]}"
            # Use D01 smoke_001 original as base
            base = _SEED_DIR / "D01" / "smoke_001" / "original.js"
            if not base.exists():
                continue
            original = base.read_text(encoding="utf-8")
            path = generate_sample(
                dimension=dim,
                original_code=original,
                sample_name=sample_name,
                obfuscation_level=level,
            )
            results.append(path)
    return results
