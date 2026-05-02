"""Obfuscation tool wrappers — call Node.js obfuscators via subprocess."""

from __future__ import annotations

import base64
import json
import re
import subprocess
from pathlib import Path


def _run_node(script: str, timeout: int = 30) -> str:
    """Execute a Node.js script and return stdout."""
    result = subprocess.run(
        ["node", "-e", script],
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=Path(__file__).resolve().parents[3],  # project root
    )
    if result.returncode != 0:
        raise RuntimeError(f"Node.js error: {result.stderr}")
    return result.stdout.strip()


def js_obfuscator(code: str, level: int = 2) -> str:
    """Obfuscate using javascript-obfuscator. Levels 1-4."""
    configs = {
        1: {"compact": True, "simplifyExpressions": True},
        2: {
            "compact": True,
            "stringArray": True,
            "stringArrayEncoding": ["base64"],
            "stringArrayThreshold": 0.75,
        },
        3: {
            "compact": True,
            "controlFlowFlattening": True,
            "controlFlowFlatteningThreshold": 0.75,
            "stringArray": True,
            "stringArrayEncoding": ["rc4"],
            "stringArrayThreshold": 1,
            "deadCodeInjection": True,
            "deadCodeInjectionThreshold": 0.4,
        },
        4: {
            "compact": True,
            "controlFlowFlattening": True,
            "controlFlowFlatteningThreshold": 1,
            "stringArray": True,
            "stringArrayEncoding": ["rc4"],
            "stringArrayThreshold": 1,
            "deadCodeInjection": True,
            "deadCodeInjectionThreshold": 0.6,
            "selfDefending": True,
            "renameGlobals": True,
            "transformObjectKeys": True,
            "unicodeEscapeSequence": True,
        },
    }
    config = configs.get(level, configs[2])
    script = f"""
    const JavaScriptObfuscator = require('javascript-obfuscator');
    const code = {json.dumps(code)};
    const config = {json.dumps(config)};
    const result = JavaScriptObfuscator.obfuscate(code, config);
    process.stdout.write(result.getObfuscatedCode());
    """
    return _run_node(script)


def js_confuser_obfuscate(code: str, level: int = 2) -> str:
    """Obfuscate using js-confuser. Levels 1-4."""
    presets = {
        1: {"target": "node", "compact": True},
        2: {"target": "node", "compact": True, "stringEncoding": True, "stringConcealing": True},
        3: {
            "target": "node",
            "compact": True,
            "stringEncoding": True,
            "controlFlowFlattening": True,
            "opaquePredicates": True,
        },
        4: {
            "target": "node",
            "compact": True,
            "stringEncoding": True,
            "controlFlowFlattening": True,
            "opaquePredicates": True,
            "dispatcher": True,
            "ragged": True,
            "minify": True,
        },
    }
    config = presets.get(level, presets[2])
    script = f"""
    const JsConfuser = require('js-confuser');
    const code = {json.dumps(code)};
    const config = {json.dumps(config)};
    JsConfuser.obfuscate(code, config).then(function(result) {{
        process.stdout.write(result);
    }}).catch(function(e) {{
        process.stderr.write(e.message);
        process.exit(1);
    }});
    """
    return _run_node(script, timeout=60)


def wrap_anti_debug(code: str) -> str:
    """Wrap code with anti-debugging techniques for D05."""
    return (
        "setInterval(function(){debugger;},1000);\n"
        "(function(){var _t0=performance.now();(function(){return arguments.callee.toString();})();\n"
        'var _dt=performance.now()-_t0;if(_dt>100)throw new Error("blocked");})();\n'
        "var _0xc=console;console={log:function(){},warn:function(){},error:function(){},clear:function(){}};\n"
        f"{code}"
    )


def encode_base64_strings(code: str) -> str:
    """Encode string literals as base64 for light obfuscation."""

    def _encode(match: re.Match[str]) -> str:
        s = match.group(1)
        encoded = base64.b64encode(s.encode()).decode()
        return f'atob("{encoded}")'

    return re.sub(r'"([^"]{3,})"', _encode, code)
