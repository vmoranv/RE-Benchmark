# JS-RE-Bench

> **JS/Web Reverse Engineering Comprehensive Benchmark Platform**
>
> Extending [JsDeObsBench](https://arxiv.org/abs/2406.06636) into a unified, public, reproducible benchmark covering the full Web/JS reverse-engineering pipeline.

[![CI](https://github.com/js-re-bench/js-re-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/js-re-bench/js-re-bench/actions/workflows/ci.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

JS-RE-Bench evaluates LLMs and tools across 18 reverse-engineering dimensions:
deobfuscation · JSVMP unpacking · TLS fingerprinting · WASM/SourceMap recovery ·
anti-debug bypass · hook quality · Canvas/WebGL · V8 internals · native instrumentation ·
Android WebView · syscall correlation · protocol inference · memory scanning ·
trace replay · cross-domain evidence · HTTP proxy · obfuscator correctness ·
LLM semantic probing.

It is built around three pillars:
- **15 quantitative metrics** (6 general + 9 specialized including `M8` semantic fidelity, `M9` LLM decay rate)
- **12 qualification challenges** (Q1-Q12) executed automatically in CI
- **5-tier obfuscation taxonomy** (L1 lexical → L5 virtualization)

## Quick Start

### Prerequisites
- Docker 24+ and Docker Compose v2
- (Optional, for development) Python 3.11+, Node.js 22+

### One-command launch (Q1 Headless Reproducibility)

```bash
docker compose -f infra/compose/docker-compose.yml up --abort-on-container-exit
```

The stack exposes:
- **API**: http://localhost:8000 (Swagger at `/docs`)
- **Frontend**: http://localhost:5173
- **Postgres**: localhost:5432
- **Redis**: localhost:6379

### CLI usage

```bash
# Run a benchmark for dimension D01 with Anthropic Claude
bench run --dimension D01 --model anthropic/claude-opus-4-7 --sample-id <uuid>

# List available dimensions
bench dimensions list

# Generate a report
bench report --run-id <uuid> --format pdf
```

## Architecture

JS-RE-Bench follows a **Plugin Modular Monolith + Isolated Workers** design:

```
CLI / REST / MCP
       ↓
  FastAPI Control Plane
    ↓              ↓
PostgreSQL      Redis
    ↓              ↓
Artifact CAS   Celery Workers
                  ↓
            Docker Sandbox Pool
        (jsvmp-node / browser-anti-debug)
```

See [`docs/architecture.md`](./docs/architecture.md) and [`.claude/plan/js-re-bench.md`](./.claude/plan/js-re-bench.md) for the full design.

## Status

This project is in **early development** (M1 Skeleton milestone).

| Milestone | Status |
|-----------|:------:|
| M1: Vertical-slice skeleton (D1 + Q1) | 🟡 In Progress |
| M2: 4 core dimensions (D1 / D2 / D5 / D17-18) | ⬜ Planned |
| M3: 14 placeholder dimensions + Q5-Q11 | ⬜ Planned |
| M4: Performance, accessibility, report export | ⬜ Planned |

## Citing

If you use JS-RE-Bench in academic work, please cite via [`CITATION.cff`](./CITATION.cff).

## License

Apache License 2.0 — see [`LICENSE`](./LICENSE).

## Acknowledgements

Inspired by JsDeObsBench, JSIMPLIFIER (NDSS 2026), OBsmith (OOPSLA 2026), CASCADE (ICSE SEIP 2026), and *The Code Barrier* (arXiv 2504.10557).
