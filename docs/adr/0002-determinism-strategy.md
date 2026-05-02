# ADR-0002: Determinism strategy — Engine vs Model determinism separation

- **Status:** Accepted
- **Date:** 2026-05-02

## Context

Q2 (Deterministic Metrics) requires that two runs of the same `RunSpec`
produce byte-identical metric output. External LLM APIs cannot guarantee
this — even with `seed=1`, vendors may change tokenizers, model versions,
or sampling implementations.

## Decision

Separate the two layers:

1. **Engine determinism** — owned and enforced by the platform. Every
   non-LLM input/output is canonicalized (RFC-8785-lite JSON), seed-derived
   from `(run_id, round_no, salt)` via Blake2b, and persisted with content
   hashes. Engine-deterministic Q2 must always pass.
2. **Model determinism** — out of our control. We record a `replay_manifest`
   (model_id, model_version, seed, prompt_digest, response_digest, image
   digest) per round. Q2 in fixture mode replays from cached responses and
   asserts identical metric output.

## Consequences

- The published Q2 score actually reflects engine quality, not vendor noise.
- Researchers reproducing a run can verify that the platform processed
  cached evidence identically, even when calling the live model would yield
  different responses.
- Adds storage cost for prompt/response artifacts (mitigated by the
  `llm_cache` table's natural deduplication via `request_digest`).
