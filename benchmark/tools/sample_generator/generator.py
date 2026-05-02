"""Sample generator — creates obfuscated samples from seed manifests.

Reads ``manifest.yaml`` + ``original.js`` from seed_samples directories and
auto-generates ``obfuscated.js`` based on the dimension code and obfuscation
level declared in the manifest.
"""

from __future__ import annotations

import uuid
from pathlib import Path

import yaml

from benchmark.tools.sample_generator.obfuscators import (
    encode_base64_strings,
    js_confuser_obfuscate,
    js_obfuscator,
    uglify,
    wasm_compile,
    wrap_anti_debug,
)

_SEED_DIR = Path(__file__).resolve().parents[3] / "benchmark" / "samples" / "seed_samples"

# Dimension-specific generator configs (used by legacy generate_sample)
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


# ---------------------------------------------------------------------------
# Auto-generation from seed manifests
# ---------------------------------------------------------------------------


def generate_for_sample(sample_dir: Path) -> Path | None:
    """Auto-generate ``obfuscated.js`` for a sample based on its manifest.

    Returns the path to the generated file, or ``None`` if the sample
    directory is missing required seed files (``manifest.yaml``,
    ``original.js``).
    """
    manifest_path = sample_dir / "manifest.yaml"
    original_path = sample_dir / "original.js"
    obfuscated_path = sample_dir / "obfuscated.js"

    if not manifest_path.exists() or not original_path.exists():
        return None
    if obfuscated_path.exists():
        return obfuscated_path  # already generated

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    original = original_path.read_text(encoding="utf-8")
    dim = manifest["dimension_code"]
    level_str = manifest.get("obfuscation_level", "L2")
    level = int(level_str.lstrip("L"))

    obfuscated = _obfuscate_for_dimension(dim, level, original, manifest)
    obfuscated_path.write_text(obfuscated, encoding="utf-8")
    return obfuscated_path


def generate_all(seed_root: Path | None = None) -> list[Path]:
    """Generate all missing ``obfuscated.js`` files under *seed_root*.

    Scans for ``manifest.yaml`` files, skips directories that already have
    ``obfuscated.js``, and generates the rest.
    """
    root = seed_root or _SEED_DIR
    results: list[Path] = []
    for manifest_path in sorted(root.rglob("manifest.yaml")):
        sample_dir = manifest_path.parent
        path = generate_for_sample(sample_dir)
        if path:
            results.append(path)
    return results


def _obfuscate_for_dimension(dim: str, level: int, code: str, manifest: dict) -> str:
    """Route to the appropriate obfuscation strategy based on dimension code."""
    if dim == "D01":
        return js_obfuscator(code, level)
    elif dim == "D02":
        return js_confuser_obfuscate(code, level)  # JSVMP-like
    elif dim == "D04":
        # WASM: if the original contains WAT code, compile it to WASM base64
        wat_marker = "(module"
        if wat_marker in code.lstrip()[:50]:
            return wasm_compile(code)
        return code  # already WASM/binary — keep as-is
    elif dim == "D05":
        obfuscated = js_obfuscator(code, level)
        return wrap_anti_debug(obfuscated)
    elif dim == "D06":
        return js_obfuscator(code, max(1, level - 1))  # Lighter obfuscation
    elif dim == "D07":
        return uglify(code)  # Canvas/WebGL just minified
    elif dim == "D17":
        return js_obfuscator(code, level)  # One obfuscator
    elif dim == "D18":
        return js_confuser_obfuscate(code, 4)  # Maximum confusion
    else:
        # D03, D08-D16: trace/dump dimensions — keep original as-is
        return code


# ---------------------------------------------------------------------------
# Legacy API (used by ``bench generate-samples`` CLI command)
# ---------------------------------------------------------------------------


def generate_sample(
    dimension: str,
    original_code: str,
    sample_name: str = "generated_001",
    obfuscation_level: int = 2,
    semantic_test_cases: list[dict] | None = None,
    description: str = "",
) -> Path:
    """Generate a sample for a given dimension (legacy API)."""
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
    """Generate samples for multiple dimensions and levels (legacy API)."""
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
