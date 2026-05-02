# Dimension D1 — Deobfuscation

## Purpose

Direct successor of [JsDeObsBench](https://arxiv.org/abs/2406.06636). Measures an
LLM's ability to reverse modern JavaScript obfuscation while preserving observable
behavior.

## Scope

- Obfuscators covered: `obfuscator.io`, `javascript-obfuscator`, `JS-Confuser`,
  hand-rolled custom packers.
- Levels covered: L1 (lexical) → L3 (data). L4/L5 are scored under D2 / D17 / D18.
- Sample target: ≥1,000 variants by M2 milestone.

## Inputs

- `SampleVariant.obfuscated_artifact_id` — obfuscated `.js` source.
- `SampleVariant.original_artifact_id`   — clean reference (private).
- `semantic_test_suite_id`               — Jest/Vitest suite for M8.

## Output Contract

Each round must emit a single fenced `javascript` block. The challenge's
`parse_response` extracts the inner code; trailing prose is ignored but
penalized in readability scoring.

## Metrics Mapping

| Code | Source | Notes |
|------|--------|-------|
| `completion_rate` | round-level grade aggregate | 3-round split |
| `token_consumption` | per-round usage sum | reported in JSON |
| `readability` | LLM-as-judge round 99 | rubric in `prompts/judge.j2` |
| `complexity_reduction` | AST cyclomatic delta | requires sandbox |
| `M8` | semantic equivalence (≥90% suite pass) | requires sandbox |

## Extension Hooks

- Add a new obfuscator: drop a sample family under
  `benchmark/samples/seed_samples/D01/<obfuscator>/...` plus a manifest YAML.
- Add a new round prompt: extend `rounds = 4` and ship `round4.j2`.
- Override readability rubric: subclass `DeobfuscationChallenge` and provide a
  custom `judge_prompt`.
