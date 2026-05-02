# Dimensions D17 + D18 — Obfuscator Correctness & LLM Semantic Probing

> **Status:** Placeholder during M1 skeleton; full implementation in M2.

## D17 — Obfuscator Correctness Verification

Reproduces OBsmith (OOPSLA 2026) sketch-based differential testing to
detect semantic regressions introduced by JS obfuscators. Drives the M8
metric for D1's input gates.

## D18 — LLM Semantic Understanding Probing

Tracks the L1 → L5 obfuscation-tier accuracy decay curve. Slope ↘
indicates LLM robustness; M9 metric quantifies it.

## Reference Papers

- OBsmith (OOPSLA 2026)
- The Code Barrier (arXiv 2504.10557)
