# Architecture overview

> Concrete blueprint lives at [`.claude/plan/js-re-bench.md`](../.claude/plan/js-re-bench.md).

## Layered view

```
┌──────────────────────────────────────────────────────┐
│  Entry points: CLI · REST · MCP                      │
├──────────────────────────────────────────────────────┤
│  Control plane (FastAPI)                             │
│   ├── Run service / scheduler                        │
│   ├── Sample / artifact services                     │
│   └── Report generator                               │
├──────────────────────────────────────────────────────┤
│  Plugin contracts                                    │
│   BaseDimension · BaseChallenge · BaseEvaluator      │
│   BaseMetric · ModelAdapter · SandboxAdapter         │
├──────────────────────────────────────────────────────┤
│  Persistence: PostgreSQL · Redis · Artifact CAS      │
├──────────────────────────────────────────────────────┤
│  Workers: Celery (control / llm / metric / judge)    │
├──────────────────────────────────────────────────────┤
│  Untrusted execution: Docker sandbox pool            │
└──────────────────────────────────────────────────────┘
```

## Run lifecycle

`RunSpec` → canonical-JSON digest → state machine
(`PLANNED → PRECHECK → R1 → V1 → R2 → V2 → R3 → V3 → JUDGE → METRICS → FINALIZED`).
At every transition the engine writes audit-grade artifacts so downstream
analysis (academic plots, regression detection, evidence chain) is
trivially reproducible.

## Quality gates

| Gate | Owner | Trigger |
|------|-------|---------|
| Q1 Headless Repro | `infra/compose` | PR + nightly |
| Q2 Deterministic Metrics | `tests/determinism` | every PR |
| Q12 Semantic Fidelity | `benchmark/challenges/q12_*` | M2 |
| Lint / typecheck | ruff · mypy · tsc | every PR |

## Extending the platform

1. Pick a free dimension code (`Dxx`).
2. `cp -r benchmark/dimensions/dim01_deobfuscation benchmark/dimensions/dimXX_<name>`.
3. Edit `challenge.py`, `dimension.py`, prompts, README.
4. Register samples under `benchmark/samples/seed_samples/DXX/`.
5. Add metric subclasses if a specialized metric is needed.
6. Submit a PR; CI runs unit + determinism + Q1 smoke automatically.
